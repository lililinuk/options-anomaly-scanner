from fastapi import APIRouter

from app.api.routes import dealer_gex, health, scans, system

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
api_router.include_router(dealer_gex.router, prefix="/dealer-gex", tags=["dealer-gex"])
