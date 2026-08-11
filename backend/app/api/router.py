from fastapi import APIRouter

from app.api.routes import health, scans, system

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
