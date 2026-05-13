from fastapi import APIRouter

router = APIRouter()


@router.get("")
def get_settings():
    """GET /settings — application-level settings."""
    return {"theme": "dark", "language": "en"}
