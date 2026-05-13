from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def index():
    """Root endpoint — mounted at `/` because this file is `route.py` at the root of the routes directory."""
    return {"message": "Welcome to the fastapi-file-router example"}
