from fastapi import APIRouter

router = APIRouter()


@router.get("")
def get_product(product_id: str):
    """GET /products/{product_id} — the directory name `[product_id]` becomes a path parameter."""
    return {"id": product_id, "name": f"Product {product_id}"}
