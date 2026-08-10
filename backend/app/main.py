from fastapi import FastAPI

from app.api.router import api_router
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Research infrastructure; no trade signals are produced in Phase 1.",
    )
    application.include_router(api_router, prefix="/api/v1")
    return application


app = create_app()

