from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

_USERS: dict[int, dict] = {
    1: {"id": 1, "name": "Ada Lovelace"},
    2: {"id": 2, "name": "Alan Turing"},
}


class UserCreate(BaseModel):
    name: str


@router.get("")
def list_users():
    """GET /users — list all users."""
    return list(_USERS.values())


@router.post("")
def create_user(payload: UserCreate):
    """POST /users — create a new user."""
    new_id = max(_USERS) + 1 if _USERS else 1
    _USERS[new_id] = {"id": new_id, "name": payload.name}
    return _USERS[new_id]
