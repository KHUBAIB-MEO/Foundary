from fastapi import APIRouter

from app.api.v1.routes import (
    auth,
    cart,
    health,
    orders,
    payments,
    products,
    seller_orders,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(products.router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
api_router.include_router(payments.router)
api_router.include_router(seller_orders.router)