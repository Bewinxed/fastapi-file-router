![00034-3220091456](https://github.com/Bewinxed/fastapi-file-router/assets/9145989/760cff2c-dffb-4e08-9617-5de26c861a05)

# FastAPI File-Based Router 🚀

File-based routing for FastAPI, inspired by SvelteKit/Next.js. Drop a `route.py` into a folder and you have an endpoint — no manual `include_router` calls, no central registry to keep in sync.

## Installation

```bash
pip install fastapi-file-router
```

## A 30-second example

Say you have this on disk:

```
my_app/
├── main.py
└── routes/
    ├── route.py            # → GET /
    └── users/
        ├── route.py        # → GET /users
        └── [user_id].py    # → GET /users/{user_id}
```

**`main.py`**

```python
from pathlib import Path

from fastapi import FastAPI
from fastapi_file_router import load_routes

app = FastAPI()
load_routes(app, Path("routes"))
```

**`routes/route.py`**

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def index():
    return {"hello": "world"}
```

**`routes/users/route.py`**

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("")
def list_users():
    return [{"id": 1, "name": "Ada"}]
```

**`routes/users/[user_id].py`**

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("")
def get_user(user_id: int):
    return {"id": user_id}
```

Run it:

```bash
cd my_app
uvicorn main:app --reload
```

You get three live endpoints with zero registration boilerplate:

| Request                  | Response                  |
| ------------------------ | ------------------------- |
| `GET /`                  | `{"hello": "world"}`      |
| `GET /users`             | `[{"id": 1, "name":...}]` |
| `GET /users/42`          | `{"id": 42}`              |

Open <http://127.0.0.1:8000/docs> and they're already grouped by path.

## How it works

`load_routes(app, Path("routes"))` walks the directory once at startup. For every `.py` file it finds, it imports the module, looks for a top-level `router = APIRouter()`, and calls `app.include_router(router, prefix=...)` with a prefix derived from the file's location.

The mapping rules:

| On disk                                | URL                                   |
| -------------------------------------- | ------------------------------------- |
| `routes/route.py`                      | `/`                                   |
| `routes/users/route.py`                | `/users`                              |
| `routes/users/profile.py`              | `/users/profile`                      |
| `routes/users/[user_id].py`            | `/users/{user_id}`                    |
| `routes/products/[product_id]/route.py`| `/products/{product_id}`              |
| `routes/products/[product_id]/reviews.py` | `/products/{product_id}/reviews`   |

In short:
- `route.py` is the directory's index.
- Any other `.py` filename becomes a path segment.
- Square brackets — on either a filename or a directory name — become path parameters.
- Nested folders chain together.

A few quieter rules worth knowing:
- A file must expose a module-level `router = APIRouter()`. If it doesn't, the file is skipped.
- Anything starting with `__` (e.g. `__pycache__`, `__init__.py`) is ignored.
- A file with `route` in the name but not exactly `route.py` (`routes.py`, `router.py`, ...) is skipped to catch typos.

## API

```python
load_routes(app, directory, auto_tags=True, verbose=False)
```

| Argument     | Type       | Default | Description                                                                                                       |
| ------------ | ---------- | ------- | ----------------------------------------------------------------------------------------------------------------- |
| `app`        | `FastAPI`  | —       | The app to mount routes onto.                                                                                     |
| `directory`  | `Path`     | —       | A `pathlib.Path` to your routes folder. Run your app from the parent so the modules are importable.               |
| `auto_tags`  | `bool`     | `True`  | Appends the URL path to each router's `tags`, so `/docs` groups endpoints by route.                               |
| `verbose`    | `bool`     | `False` | Logs every mounted path at `INFO` on the `fastapi-file-router` logger. Pair with `logging.basicConfig(level=...)`.|

## Full example

A runnable app that exercises every feature — nested directories, parameterized folders, multiple HTTP methods, auto tags, verbose logging — lives in [`examples/`](./examples/):

```bash
cd examples
uvicorn main:app --reload
# then open http://127.0.0.1:8000/docs
```

## Motivation

Sveltekit ruined me 🤓:

> 1. File-based routing is the bees knees.
> 2. I like to watch the world burn.
> 3. It's just easier, bro.

## Contributing

Contributions welcome — fork and open a PR.

## License

Don't be a bozo.
