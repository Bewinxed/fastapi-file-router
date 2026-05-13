"""Full example for fastapi-file-router.

Run from this directory so that `routes` is importable as a package:

    cd examples
    uvicorn main:app --reload

Then visit http://127.0.0.1:8000/docs to see every route grouped by auto-generated tags.
"""

import logging
from pathlib import Path

from fastapi import FastAPI

from fastapi_file_router import load_routes

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="fastapi-file-router example")

load_routes(app, Path("routes"), verbose=True)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
