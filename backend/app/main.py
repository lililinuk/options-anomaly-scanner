from fastapi import FastAPI

from app.api.router import api_router
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        description="Evidence-first Phase 2A options positioning research; not trade advice.",
    )
    application.include_router(api_router, prefix="/api/v1")
    return application


app = create_app()
