from fastapi import APIRouter

from app.api.routes import (
    candidate_contexts,
    dealer_gex,
    health,
    scans,
    system,
    trading_dashboard,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
api_router.include_router(dealer_gex.router, prefix="/dealer-gex", tags=["dealer-gex"])
api_router.include_router(
    trading_dashboard.router,
    prefix="/dashboard/trading",
    tags=["trading-dashboard"],
)
api_router.include_router(
    candidate_contexts.router,
    prefix="/product-candidates",
    tags=["product-candidate-context"],
)
