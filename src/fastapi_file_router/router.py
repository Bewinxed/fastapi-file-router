import importlib
import logging
import operator
import os
import re
from collections.abc import Generator
from pathlib import Path
from time import time
from typing import Optional

from fastapi import APIRouter, FastAPI

__all__ = ["load_routes"]

logger = logging.getLogger("fastapi-file-router")


def log(message: str, verbose: bool = False):
    if verbose:
        logger.info(message)  # Simple print can be replaced with any logging mechanism
    else:
        logger.debug(message)


def square_to_curly_brackets(path: str) -> str:
    """Convert square brackets in a path to curly brackets for route parameters."""
    return path.replace("[", "{").replace("]", "}")


def walk(directory: Path) -> Generator[tuple[str, list[str], list[str]], None, None]:
    """Walk through the directory yielding each folder's path and filenames."""
    yield from os.walk(directory)


def load_routes(
    app: FastAPI, directory: Path, auto_tags: bool = True, verbose: bool = False
):
    """
    Dynamically load FastAPI routes from a specified directory.

    Args:
        app: The FastAPI app instance to include routers into.
        directory: The directory path where route files are located.
            It should follow
            a structure where each file represents a route module, and nested
            directories are translated into URL path segments. Files named 'route.py'
            are treated as index routes for their directory. Filenames other than
            'route.py' are appended to the path as additional segments. Square brackets
            in directory names are converted to curly brackets in route paths to denote
            path parameters.
        auto_tags: Automatically set tags for routes based on file paths.
        verbose: Enable detailed logging.

    Example:
        Given a directory structure:
            /api
                /users
                    route.py       # Translates to /users
                    [user_id].py   # Translates to /users/{user_id}
                /documents
                    /[document_id]
                        route.py   # Translates to /documents/{document_id}

        The 'route.py' file should define an 'APIRouter' instance named 'router'.
        This function will load each router and configure it within the FastAPI application.
    """
    start = time()
    log(f"Loading routes from {directory}", verbose)

    routers: list[tuple[str, APIRouter]] = []

    for root, _, files in walk(directory):
        root = Path(root)
        if root.name.startswith("__"):
            continue
        for file in files:
            file_path = Path(file)
            if file_path.name.startswith("__") or file_path.suffix != ".py":
                continue
            if "route" in file_path.stem and file_path.stem != "route":
                log(
                    f"Skipping possibly misspelled route file {file_path.stem} in {root}",
                    verbose=verbose,
                )
                continue

            route = importlib.import_module(
                (root / file).as_posix().replace("/", ".")[:-3]
            )
            router: Optional[APIRouter] = getattr(route, "router", None)
            if not router:
                log(
                    f"Router {(root / file).absolute().as_posix()} does not contain a router",
                    verbose=verbose,
                )
                continue

            route_path = square_to_curly_brackets(
                "/".join((root / file).as_posix().split("/")[1:-1]),
            ).replace(directory.name, "")

            if re.search(r"\[(.*?)\]", file_path.stem):
                # This is a parameter route like [user_id].py
                # Extract parameter name from between square brackets
                match = re.search(r"\[(.*?)\]", file_path.stem)
                if match:
                    param_name = match.group(1)
                    route_path += f"/{{{param_name}}}"
            elif file_path.stem != "route":
                # This is a regular file, not a parameter route and not route.py
                # Just add the filename as a path segment
                route_path += f"/{file_path.stem}"

            # Register the router
            # convert root path to prefix
            if auto_tags:
                router.tags += [f"{route_path.replace(directory.name, '')}"]
            routers.append((route_path, router))

    # sort alphabetically
    for route_path, router in sorted(routers, key=operator.itemgetter(0)):
        log(f"Loaded router with path /{route_path}", verbose=verbose)
        app.include_router(
            router,
            prefix=f"{route_path}",
            tags=router.tags,
        )
    log(f"Routes loaded in {time() - start:.2f}s", verbose=verbose)

    return app
