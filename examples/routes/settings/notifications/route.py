from fastapi import APIRouter

router = APIRouter()


@router.get("")
def get_notifications():
    """GET /settings/notifications — nested directories chain together as path segments."""
    return {"push": True, "sms": False, "email": True}
