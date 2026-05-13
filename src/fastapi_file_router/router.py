import importlib.util
import logging
import os
import re
import sys
from pathlib import Path
from time import time
from types import ModuleType
from typing import Union

from fastapi import APIRouter, FastAPI

__all__ = ["load_routes"]

logger = logging.getLogger("fastapi-file-router")

_PARAM_RE = re.compile(r"\[(.*?)\]")
# Common typos for "route". Anything else is treated as a real path segment.
_TYPO_NAMES = frozenset({"routes", "router", "routers"})


def log(message: str, verbose: bool = False) -> None:
    if verbose:
        logger.info(message)
    else:
        logger.debug(message)


def square_to_curly_brackets(path: str) -> str:
    """Convert square brackets in a path to curly brackets for route parameters."""
    return _PARAM_RE.sub(lambda m: "{" + m.group(1) + "}", path)


def _import_module_from_path(file_path: Path) -> ModuleType:
    resolved = file_path.resolve()
    module_name = f"fastapi_file_router._loaded_{abs(hash(str(resolved))):x}"
    spec = importlib.util.spec_from_file_location(module_name, resolved)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {resolved}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        sys.modules.pop(module_name, None)
        raise RuntimeError(f"Failed to load route file {file_path}: {exc}") from exc
    return module


def _segments_for(rel_parts: tuple[str, ...]) -> list[str]:
    """Compute URL segments for a route file from its parts relative to the routes dir."""
    *dir_parts, file_part = rel_parts
    stem = Path(file_part).stem
    segments = [square_to_curly_brackets(p) for p in dir_parts]
    if stem == "route":
        return segments
    if _PARAM_RE.search(stem):
        segments.append(square_to_curly_brackets(stem))
    else:
        segments.append(stem)
    return segments


def _sort_key(url_path: str) -> tuple[tuple[int, str], ...]:
    """Sort routes so static segments come before parameter segments at every depth."""
    parts = url_path.split("/") if url_path else []
    return tuple((1 if "{" in p else 0, p) for p in parts)


def load_routes(
    app: FastAPI,
    directory: Union[Path, str],
    auto_tags: bool = True,
    verbose: bool = False,
) -> FastAPI:
    """Mount every route file under ``directory`` onto ``app``.

    Args:
        app: The FastAPI app to mount routers onto.
        directory: Path to the routes folder. Accepts anything ``pathlib.Path``
            accepts (``Path`` or ``str``). May be relative or absolute; nesting
            (e.g. ``Path("src/routes")``) is supported.
        auto_tags: If True, append the computed URL path to each router's tags
            so endpoints group by route in the ``/docs`` UI. The caller's
            ``router.tags`` list is not mutated; tags already present on the
            router are not duplicated.
        verbose: Log every mounted route at INFO level on the
            ``fastapi-file-router`` logger.

    File-to-URL mapping rules:
        * ``route.py`` is the index of its directory.
        * Any other ``.py`` file becomes a URL segment.
        * ``[param]`` in a file or directory name becomes ``{param}``. Mixed
          names (e.g. ``[user_id]_admin.py``) keep the surrounding text and
          mount at ``/{user_id}_admin``.
        * Files/directories starting with ``__`` are skipped (and not descended
          into).
        * Files exactly named ``routes.py``, ``router.py``, or ``routers.py``
          are skipped to guard against typos for ``route.py``.

    Each route module must define a top-level ``router = APIRouter()``. Modules
    are imported via ``importlib.util.spec_from_file_location`` and their
    top-level code re-executes on every call to ``load_routes`` — keep module
    import side effects idempotent.

    Raises:
        FileNotFoundError: If ``directory`` is not an existing directory.
        ValueError: If two route files resolve to the same URL path.
        RuntimeError: If a route file raises during import.
    """
    start = time()
    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"Routes directory does not exist: {directory}")
    log(f"Loading routes from {directory}", verbose)

    routers: list[tuple[str, Path, APIRouter, list[str]]] = []

    for root, dirnames, files in os.walk(directory):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("__"))
        root_path = Path(root)

        for file in sorted(files):
            if file.startswith("__") or not file.endswith(".py"):
                continue
            file_path = root_path / file
            stem = file_path.stem
            if stem in _TYPO_NAMES:
                log(
                    f"Skipping possibly misspelled route file {file_path} "
                    "(did you mean route.py?)",
                    verbose,
                )
                continue

            module = _import_module_from_path(file_path)
            router = getattr(module, "router", None)
            if not isinstance(router, APIRouter):
                log(f"Skipping {file_path}: no `router: APIRouter` defined", verbose)
                continue

            rel_parts = file_path.relative_to(directory).parts
            segments = _segments_for(rel_parts)
            url_path = ("/" + "/".join(segments)) if segments else ""

            extra_tags: list[str] = []
            if auto_tags:
                tag = url_path or "/"
                if tag not in router.tags:
                    extra_tags.append(tag)

            routers.append((url_path, file_path, router, extra_tags))

    seen: dict[str, Path] = {}
    for url_path, file_path, _router, _tags in routers:
        if url_path in seen:
            raise ValueError(
                f"Duplicate route path {url_path or '/'!r}: "
                f"{seen[url_path]} and {file_path} both map to it"
            )
        seen[url_path] = file_path

    for url_path, _file_path, router, extra_tags in sorted(
        routers, key=lambda r: _sort_key(r[0])
    ):
        log(f"Loaded router at {url_path or '/'}", verbose)
        app.include_router(router, prefix=url_path, tags=extra_tags)

    log(f"Routes loaded in {time() - start:.2f}s", verbose)
    return app
