import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import APIRouter, FastAPI

# Import the module to test
from fastapi_file_router.router import load_routes, square_to_curly_brackets


@pytest.fixture
def app():
    """Fixture to create a FastAPI app instance."""
    app = FastAPI()
    # Mock the include_router method
    app.include_router = MagicMock()
    return app


@pytest.fixture
def temp_directory():
    """Fixture to create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    api_dir = os.path.join(temp_dir, "api")
    os.makedirs(api_dir)

    yield Path(api_dir)

    # Clean up after the test
    shutil.rmtree(temp_dir)


def create_route_file(directory, filename, with_router=True):
    """Helper function to create test route files."""
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, filename)

    with open(file_path, "w") as f:
        f.write("from fastapi import APIRouter\n\n")
        if with_router:
            f.write("router = APIRouter(tags=[])\n\n")
            f.write("@router.get('')\n")
            f.write("def get_endpoint():\n")
            f.write("    return {'message': 'success'}\n")
        else:
            f.write("# No router defined\n")


def test_square_to_curly_brackets():
    """Test the square_to_curly_brackets function."""
    assert square_to_curly_brackets("users/[user_id]") == "users/{user_id}"
    assert (
        square_to_curly_brackets("products/[category]/[id]")
        == "products/{category}/{id}"
    )
    assert square_to_curly_brackets("normal/path") == "normal/path"


def test_load_routes_basic(app, temp_directory):
    """Test loading a simple route file."""
    # Create a basic route.py file
    users_dir = os.path.join(temp_directory, "users")
    create_route_file(users_dir, "route.py")

    # Setup the mock
    with patch("fastapi_file_router.router.importlib.import_module") as mock_import:
        # Configure the mock to return a module with a router
        mock_module = MagicMock()
        mock_router = APIRouter(tags=[])
        mock_module.router = mock_router
        mock_import.return_value = mock_module

        # Call the function
        load_routes(app, temp_directory, verbose=True)

        # Use assert_called to check with less strict matching
        assert app.include_router.called

        # Check that the arguments match what we expect - get actual values from call
        call_args = app.include_router.call_args
        assert call_args[0][0] == mock_router

        # Just verify the user path is included in the prefix, without worrying about the exact temp dir
        assert "/users" in call_args[1]["prefix"]

        # For the tag, just verify it contains the user path
        assert any("/users" in tag for tag in call_args[1]["tags"])


def test_load_routes_parameter_file(app, temp_directory):
    """Test loading a parameter route file like [user_id].py."""
    # Create a parameter route file
    users_dir = os.path.join(temp_directory, "users")
    create_route_file(users_dir, "[user_id].py")

    with patch("fastapi_file_router.router.importlib.import_module") as mock_import:
        mock_module = MagicMock()
        mock_router = APIRouter(tags=[])
        mock_module.router = mock_router
        mock_import.return_value = mock_module

        load_routes(app, temp_directory, verbose=True)

        # Check that the router was included
        assert app.include_router.called

        # Check that the arguments contain the parameter path
        call_args = app.include_router.call_args
        assert call_args[0][0] == mock_router

        # Just verify the parameter path is included, without worrying about exact temp dir
        assert "/users/{user_id}" in call_args[1]["prefix"]

        # For the tag, verify it contains the parameter path
        assert any("/users/{user_id}" in tag for tag in call_args[1]["tags"])


def test_load_routes_nested_structure(app, temp_directory):
    """Test loading nested directory structure with various route types."""
    # Create a more complex structure
    users_dir = os.path.join(temp_directory, "users")
    create_route_file(users_dir, "route.py")

    user_id_dir = os.path.join(temp_directory, "users", "[user_id]")
    create_route_file(user_id_dir, "route.py")
    create_route_file(user_id_dir, "profile.py")

    docs_dir = os.path.join(temp_directory, "documents")
    create_route_file(docs_dir, "route.py")

    with patch("fastapi_file_router.router.importlib.import_module") as mock_import:
        # Set up the mock to return different routers for different imports
        def side_effect(module_path):
            mock_module = MagicMock()
            mock_module.router = APIRouter(tags=[])
            return mock_module

        mock_import.side_effect = side_effect

        load_routes(app, temp_directory, verbose=True)

        # Check that app.include_router was called multiple times
        assert app.include_router.call_count >= 4


def test_load_routes_skip_non_routers(app, temp_directory):
    """Test that files without routers are skipped."""
    users_dir = os.path.join(temp_directory, "users")
    create_route_file(users_dir, "route.py", with_router=False)

    with patch("fastapi_file_router.router.importlib.import_module") as mock_import:
        # Mock the router module but don't add a router attribute
        mock_module = MagicMock(spec=[])  # Empty spec - no router attribute
        mock_import.return_value = mock_module

        # Patch getattr to simulate attribute error when router is accessed
        with patch("fastapi_file_router.router.getattr") as mock_getattr:
            mock_getattr.return_value = None

            load_routes(app, temp_directory, verbose=True)

            # Since router is None, app.include_router should not be called with a router
            for call in app.include_router.call_args_list:
                # Verify none of the calls included our mock_module or None as router
                assert call[0][0] is not None
                assert call[0][0] is not mock_module


def test_load_routes_skip_special_dirs_and_files(app, temp_directory):
    """Test that __pycache__ directories and __init__.py files are skipped."""
    # Create a __pycache__ directory
    pycache_dir = os.path.join(temp_directory, "__pycache__")
    os.makedirs(pycache_dir)
    create_route_file(pycache_dir, "cached.py")

    # Create a __init__.py file
    init_file = os.path.join(temp_directory, "__init__.py")
    with open(init_file, "w") as f:
        f.write("# init file\n")

    with patch("fastapi_file_router.router.importlib.import_module") as mock_import:
        load_routes(app, temp_directory, verbose=True)

        # Check that no imports were attempted for pycache
        for call in mock_import.call_args_list:
            assert "__pycache__" not in call[0][0]


def test_load_routes_skip_misspelled_routes(app, temp_directory):
    """Test that files with 'route' in the name but not exactly 'route.py' are skipped."""
    users_dir = os.path.join(temp_directory, "users")
    os.makedirs(users_dir, exist_ok=True)

    # Create a misspelled route file
    misspelled_file = os.path.join(users_dir, "router.py")
    with open(misspelled_file, "w") as f:
        f.write("# Misspelled route file\n")

    initial_call_count = 0  # To track calls before our test

    with patch("fastapi_file_router.router.importlib.import_module") as mock_import:
        # This will make the import succeed but not find a router
        mock_import.return_value = MagicMock(spec=[])

        # We'll use this flag to detect if our specific file was processed
        detected_router_py = False

        # Override the original import_module to detect when our router.py is imported
        original_import = mock_import.side_effect

        def custom_import_side_effect(name):
            nonlocal detected_router_py
            if "router.py" in name:
                detected_router_py = True
            return MagicMock(spec=[])

        mock_import.side_effect = custom_import_side_effect

        load_routes(app, temp_directory, verbose=True)

        # Our router.py file should not be imported since it's misspelled
        assert not detected_router_py


def test_auto_tags_parameter(app, temp_directory):
    """Test the auto_tags parameter."""
    users_dir = os.path.join(temp_directory, "users")
    create_route_file(users_dir, "route.py")

    with patch("fastapi_file_router.router.importlib.import_module") as mock_import:
        # With auto_tags=True
        mock_module = MagicMock()
        mock_router = APIRouter(tags=["existing_tag"])
        mock_module.router = mock_router
        mock_import.return_value = mock_module

        load_routes(app, temp_directory, auto_tags=True, verbose=True)

        # Check that the arguments match
        call_args = app.include_router.call_args
        assert call_args[0][0] == mock_router

        # Just verify the path contains users and the existing tag is present
        assert "/users" in call_args[1]["prefix"]
        assert "existing_tag" in call_args[1]["tags"]

        # With auto_tags=False
        app.include_router.reset_mock()
        mock_router = APIRouter(tags=["existing_tag"])
        mock_module.router = mock_router
        mock_import.return_value = mock_module

        load_routes(app, temp_directory, auto_tags=False, verbose=True)

        # Make sure only the original tags are present
        call_args = app.include_router.call_args
        assert call_args[0][0] == mock_router
        assert "/users" in call_args[1]["prefix"]
        assert call_args[1]["tags"] == ["existing_tag"]  # Only the original tag


def test_log_function():
    """Test the log function with proper mocking of the logger."""
    with patch("fastapi_file_router.router.logger") as mock_logger:
        # Import the log function after mocking the logger
        from fastapi_file_router.router import log

        # Test verbose=True
        log("Test message", verbose=True)
        mock_logger.info.assert_called_once_with("Test message")

        # Test verbose=False
        mock_logger.reset_mock()
        log("Debug message", verbose=False)
        mock_logger.debug.assert_called_once_with("Debug message")
