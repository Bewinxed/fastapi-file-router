from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("")
def get_user(user_id: int):
    """GET /users/{user_id} — fetch a single user by id.

    The filename `[user_id].py` is converted to the path parameter `{user_id}`.
    """
    sample = {1: "Ada Lovelace", 2: "Alan Turing"}
    if user_id not in sample:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user_id, "name": sample[user_id]}
