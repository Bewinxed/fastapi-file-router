from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_file_router import load_routes
from fastapi_file_router.router import square_to_curly_brackets


def _make_route(path: Path, body: str = "{'ok': True}") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n"
        "@router.get('')\n"
        f"def handler(): return {body}\n"
    )


def _mounted_paths(app: FastAPI) -> set[str]:
    return {r.path for r in app.routes if hasattr(r, "path")}


def test_square_to_curly_brackets():
    assert square_to_curly_brackets("users/[user_id]") == "users/{user_id}"
    assert (
        square_to_curly_brackets("products/[category]/[id]")
        == "products/{category}/{id}"
    )
    assert square_to_curly_brackets("normal/path") == "normal/path"


def test_basic_route(tmp_path: Path):
    routes = tmp_path / "routes"
    _make_route(routes / "users" / "route.py")
    app = FastAPI()
    load_routes(app, routes)
    assert "/users" in _mounted_paths(app)


def test_parameter_file(tmp_path: Path):
    routes = tmp_path / "routes"
    _make_route(routes / "users" / "[user_id].py")
    app = FastAPI()
    load_routes(app, routes)
    assert "/users/{user_id}" in _mounted_paths(app)


def test_parameter_directory(tmp_path: Path):
    routes = tmp_path / "routes"
    _make_route(routes / "products" / "[product_id]" / "route.py")
    _make_route(routes / "products" / "[product_id]" / "reviews.py")
    app = FastAPI()
    load_routes(app, routes)
    paths = _mounted_paths(app)
    assert "/products/{product_id}" in paths
    assert "/products/{product_id}/reviews" in paths


def test_nested_structure(tmp_path: Path):
    routes = tmp_path / "routes"
    _make_route(routes / "users" / "route.py")
    _make_route(routes / "users" / "profile.py")
    _make_route(routes / "users" / "[user_id].py")
    _make_route(routes / "documents" / "route.py")
    app = FastAPI()
    load_routes(app, routes)
    assert {
        "/users",
        "/users/profile",
        "/users/{user_id}",
        "/documents",
    }.issubset(_mounted_paths(app))


def test_static_segment_matches_before_param(tmp_path: Path):
    """Regression: routes like /users/profile must be registered before /users/{user_id}."""
    routes = tmp_path / "routes"
    routes.mkdir(parents=True)
    (routes / "users").mkdir()
    (routes / "users" / "profile.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n"
        "@router.get('')\n"
        "def f(): return {'kind': 'profile'}\n"
    )
    (routes / "users" / "[user_id].py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n"
        "@router.get('')\n"
        "def f(user_id: str): return {'kind': 'user', 'id': user_id}\n"
    )
    app = FastAPI()
    load_routes(app, routes)
    client = TestClient(app)
    assert client.get("/users/profile").json() == {"kind": "profile"}
    assert client.get("/users/123").json() == {"kind": "user", "id": "123"}


def test_skip_misspelled_route_files(tmp_path: Path):
    routes = tmp_path / "routes"
    _make_route(routes / "users" / "route.py")
    _make_route(routes / "users" / "router.py")
    _make_route(routes / "users" / "routes.py")
    app = FastAPI()
    load_routes(app, routes)
    paths = _mounted_paths(app)
    assert "/users" in paths
    assert "/users/router" not in paths
    assert "/users/routes" not in paths


def test_allows_route_substring_in_filename(tmp_path: Path):
    """Files like route_handler.py are legitimate; only exact typos are skipped."""
    routes = tmp_path / "routes"
    _make_route(routes / "route_handler.py")
    _make_route(routes / "enroute.py")
    app = FastAPI()
    load_routes(app, routes)
    paths = _mounted_paths(app)
    assert "/route_handler" in paths
    assert "/enroute" in paths


def test_skip_dunder_dirs_and_files(tmp_path: Path):
    routes = tmp_path / "routes"
    _make_route(routes / "users" / "route.py")
    _make_route(routes / "__pycache__" / "fake.py")
    _make_route(routes / "users" / "__pycache__" / "fake.py")
    _make_route(routes / "users" / "__pycache__" / "nested" / "deep.py")
    (routes / "__init__.py").write_text("# init\n")
    app = FastAPI()
    load_routes(app, routes)
    paths = _mounted_paths(app)
    assert "/users" in paths
    assert not any("__pycache__" in p for p in paths)
    assert not any("nested" in p or "deep" in p for p in paths)


def test_skip_files_without_router(tmp_path: Path):
    routes = tmp_path / "routes"
    routes.mkdir(parents=True)
    (routes / "lonely.py").write_text("# no router here\n")
    (routes / "wrong_type.py").write_text("router = 'not a router'\n")
    app = FastAPI()
    load_routes(app, routes)
    paths = _mounted_paths(app)
    assert "/lonely" not in paths
    assert "/wrong_type" not in paths


def test_auto_tags_appends_path(tmp_path: Path):
    routes = tmp_path / "routes"
    _make_route(routes / "users" / "route.py")
    app = FastAPI()
    load_routes(app, routes, auto_tags=True)
    op = app.openapi()["paths"]["/users"]["get"]
    assert "/users" in op["tags"]


def test_auto_tags_false_preserves_user_tags(tmp_path: Path):
    routes = tmp_path / "routes"
    routes.mkdir(parents=True)
    (routes / "users").mkdir()
    (routes / "users" / "route.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter(tags=['existing'])\n"
        "@router.get('')\n"
        "def f(): return {}\n"
    )
    app = FastAPI()
    load_routes(app, routes, auto_tags=False)
    tags = app.openapi()["paths"]["/users"]["get"]["tags"]
    assert tags == ["existing"]


def test_does_not_mutate_router_tags(tmp_path: Path):
    """Regression: repeated load_routes calls must not accumulate tags on the router instance."""
    routes = tmp_path / "routes"
    routes.mkdir(parents=True)
    (routes / "users").mkdir()
    (routes / "users" / "route.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter(tags=['original'])\n"
        "@router.get('')\n"
        "def f(): return {}\n"
    )
    for _ in range(3):
        app = FastAPI()
        load_routes(app, routes, auto_tags=True)
    # Find the module loaded for this specific file and check its router's tags weren't appended to.
    import sys

    target_file = str((routes / "users" / "route.py").resolve())
    loaded = [
        m
        for n, m in sys.modules.items()
        if n.startswith("fastapi_file_router._loaded_")
        and getattr(m, "__file__", None) == target_file
    ]
    assert loaded, "expected the loaded route module to be present in sys.modules"
    for m in loaded:
        assert m.router.tags == ["original"]


def test_directory_basename_not_substring_stripped(tmp_path: Path):
    """Regression: directory.name was string-replaced anywhere in the URL path."""
    routes = tmp_path / "api"
    _make_route(routes / "apicake" / "route.py")
    _make_route(routes / "users" / "route.py")
    app = FastAPI()
    load_routes(app, routes)
    paths = _mounted_paths(app)
    assert "/apicake" in paths
    assert "/cake" not in paths
    assert "/users" in paths


def test_nested_directory_path(tmp_path: Path):
    """Regression: passing a multi-segment dir like Path('src/routes') used to make '//users'."""
    routes = tmp_path / "src" / "routes"
    _make_route(routes / "users" / "route.py")
    app = FastAPI()
    load_routes(app, routes)
    paths = _mounted_paths(app)
    assert "/users" in paths
    assert "//users" not in paths


def test_absolute_directory_path(tmp_path: Path):
    """Regression: absolute paths broke the dotted-name importlib lookup."""
    routes = tmp_path / "routes"
    _make_route(routes / "users" / "route.py")
    app = FastAPI()
    load_routes(app, routes.resolve())
    assert "/users" in _mounted_paths(app)


def test_root_index_route(tmp_path: Path):
    """A route.py at the routes root mounts at /."""
    routes = tmp_path / "routes"
    routes.mkdir(parents=True)
    (routes / "route.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n"
        "@router.get('/')\n"
        "def f(): return {'ok': True}\n"
    )
    app = FastAPI()
    load_routes(app, routes)
    assert TestClient(app).get("/").json() == {"ok": True}


def test_missing_directory_raises(tmp_path: Path):
    app = FastAPI()
    with pytest.raises(FileNotFoundError):
        load_routes(app, tmp_path / "does-not-exist")


def test_string_directory_argument(tmp_path: Path):
    routes = tmp_path / "routes"
    _make_route(routes / "users" / "route.py")
    app = FastAPI()
    load_routes(app, str(routes))
    assert "/users" in _mounted_paths(app)


def test_duplicate_url_paths_raise(tmp_path: Path):
    """Regression: routes/users.py and routes/users/route.py both map to /users."""
    routes = tmp_path / "routes"
    _make_route(routes / "users.py")
    _make_route(routes / "users" / "route.py")
    app = FastAPI()
    with pytest.raises(ValueError, match="Duplicate route path '/users'"):
        load_routes(app, routes)


def test_route_file_import_error_is_wrapped(tmp_path: Path):
    routes = tmp_path / "routes"
    routes.mkdir(parents=True)
    bad = routes / "broken.py"
    bad.write_text("raise RuntimeError('boom')\n")
    app = FastAPI()
    with pytest.raises(RuntimeError, match="Failed to load route file") as info:
        load_routes(app, routes)
    assert isinstance(info.value.__cause__, RuntimeError)
    assert "boom" in str(info.value.__cause__)


def test_auto_tags_does_not_duplicate_existing_tag(tmp_path: Path):
    routes = tmp_path / "routes"
    routes.mkdir(parents=True)
    (routes / "users").mkdir()
    (routes / "users" / "route.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter(tags=['/users'])\n"
        "@router.get('')\n"
        "def f(): return {}\n"
    )
    app = FastAPI()
    load_routes(app, routes, auto_tags=True)
    tags = app.openapi()["paths"]["/users"]["get"]["tags"]
    assert tags == ["/users"]


def test_log_function():
    from unittest.mock import patch

    with patch("fastapi_file_router.router.logger") as mock_logger:
        from fastapi_file_router.router import log

        log("Info msg", verbose=True)
        mock_logger.info.assert_called_once_with("Info msg")

        mock_logger.reset_mock()
        log("Debug msg", verbose=False)
        mock_logger.debug.assert_called_once_with("Debug msg")
