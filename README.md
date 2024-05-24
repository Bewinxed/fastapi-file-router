# FastAPI Dynamic Route Loader 🚀

This Python module dynamically loads FastAPI routes from a specified directory structure. It is designed to streamline the integration of API routes into a FastAPI app, making it easy to manage large applications with many endpoints.

## Features

- **Dynamic Route Loading**: Automatically load route files as APIRouter instances into your FastAPI application.
- **Path Conversion**: Converts square brackets in filenames to curly brackets in route paths to denote path parameters.
- **Verbose Logging**: Provides detailed logging to help with debugging during route loading.
- **Auto Tagging**: Automatically tags routes in the FastAPI documentation based on their directory path.

## Installation

Clone this repository or copy the script into your project directory:

```bash
git clone https://github.com/Bewinxed/fastapi-file-router
```

Ensure that you have FastAPI installed, or install it using pip:

```
pip install fastapi
```

## Usage

1. Prepare your route files: Create a directory structure where each Python file represents a FastAPI route. Use route.py for base paths and include other .py files for additional route segments. Use square brackets for dynamic segments in filenames, e.g., [user_id].py.

2. Load Routes: Import the load_routes function from the module and pass your FastAPI app instance along with the directory containing your route files.

## Example directory structure:

```
/api
    /users
        route.py       # Translates to /users
        [user_id].py   # Translates to /users/{user_id}
    /documents
        /[document_id]
            route.py   # Translates to /documents/{document_id}

```

3. Run your app

```
uvicorn app:app --reload
```

# Logging

Enable verbose logging to get detailed output during the route loading process, which can be helpful for debugging:

```
load_routes(app, Path("./api"), verbose=True)
```

# Contributing

Contributions are welcome! Please fork the repository and open a pull request with your features or fixes.

# License

Don't be a bozo.
