![00034-3220091456](https://github.com/Bewinxed/fastapi-file-router/assets/9145989/760cff2c-dffb-4e08-9617-5de26c861a05)

# FastAPI File-Based Router 🚀

## Motivation

Sveltekit ruined me 🤓! I made this package because:

> 1. File-based routing is the bees knees.
> 2. I like to watch the world burn.
> 3. It's just easier, bro.

This Python module dynamically loads FastAPI routes from a specified directory structure. It walks the directory once, imports every `route.py` (and any sibling `.py` files), and mounts their `router: APIRouter` onto your app with a prefix derived from the path.

## Installation

```bash
pip install fastapi-file-router
```

## Usage

Point `load_routes` at any directory and it does the rest:

```python
from pathlib import Path

from fastapi import FastAPI
from fastapi_file_router import load_routes

app = FastAPI()

load_routes(app, Path("routes"), verbose=True)
```

The `directory` argument must be a `pathlib.Path`. Run your app from the parent of that directory so the modules can be imported (e.g. `cd examples && uvicorn main:app`).

### Filesystem conventions

```
📁 routes/                          # passed to load_routes
├ 📄 route.py                       # GET /
│
├ 📁 users/
│ ├ 📄 route.py                     # /users
│ ├ 📄 [user_id].py                 # /users/{user_id}
│ └ 📄 profile.py                   # /users/profile
│
├ 📁 products/
│ ├ 📄 route.py                     # /products
│ └ 📁 [product_id]/
│   ├ 📄 route.py                   # /products/{product_id}
│   └ 📄 reviews.py                 # /products/{product_id}/reviews
│
└ 📁 settings/
  ├ 📄 route.py                     # /settings
  └ 📁 notifications/
    ├ 📄 route.py                   # /settings/notifications
    └ 📄 email.py                   # /settings/notifications/email
```

Rules used by the loader:

- A file named `route.py` is the index of its directory.
- Any other `.py` file becomes an extra path segment (`profile.py` → `/profile`).
- Square brackets in a file or directory name become path parameters (`[user_id]` → `{user_id}`).
- Each file must expose a module-level `router = APIRouter()`. Files without one are skipped.
- Files/directories starting with `__` (e.g. `__pycache__`, `__init__.py`) are skipped.
- A file that has `route` in its name but isn't exactly `route.py` (e.g. `routes.py`, `router.py`) is skipped to guard against typos.

### Options

`load_routes(app, directory, auto_tags=True, verbose=False)`

- `auto_tags` (default `True`): appends the computed route path to each router's `tags`, which groups endpoints by URL in the `/docs` UI.
- `verbose` (default `False`): logs each loaded path at `INFO` level on the `fastapi-file-router` logger. Combine with `logging.basicConfig(level=logging.INFO)` to see the output.

## Full example

A runnable end-to-end example covering every feature lives in [`examples/`](./examples/). Try it with:

```bash
cd examples
uvicorn main:app --reload
```

Then open <http://127.0.0.1:8000/docs>.

# Contributing

Contributions are welcome! Please fork the repository and open a pull request with your features or fixes.

# License

Don't be a bozo.
