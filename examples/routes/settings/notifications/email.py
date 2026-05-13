from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class EmailPreferences(BaseModel):
    marketing: bool = False
    product_updates: bool = True


@router.get("")
def get_email_prefs():
    """GET /settings/notifications/email — read email notification preferences."""
    return EmailPreferences()


@router.put("")
def update_email_prefs(prefs: EmailPreferences):
    """PUT /settings/notifications/email — update preferences."""
    return prefs
