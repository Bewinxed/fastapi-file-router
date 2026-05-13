from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_reviews(product_id: str):
    """GET /products/{product_id}/reviews — combines a directory parameter with a regular file segment."""
    return [
        {"product_id": product_id, "rating": 5, "comment": "Great!"},
        {"product_id": product_id, "rating": 4, "comment": "Good value."},
    ]
