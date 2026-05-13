from fastapi import APIRouter

router = APIRouter()

_PRODUCTS = [
    {"id": "abc", "name": "Notebook"},
    {"id": "xyz", "name": "Pen"},
]


@router.get("")
def list_products():
    """GET /products — list all products."""
    return _PRODUCTS
