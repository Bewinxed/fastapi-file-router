from fastapi import APIRouter

router = APIRouter()


@router.get("")
def get_profile():
    """GET /users/profile — any non-`route.py` filename becomes a path segment."""
    return {"name": "Ada Lovelace", "bio": "Mathematician and the first programmer."}
