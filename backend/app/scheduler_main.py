from fastapi import FastAPI

from app.scheduler.routes import router


def create_scheduler_app() -> FastAPI:
    application = FastAPI(
        title="Nightwatch Canonical Production Orchestrator",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    application.include_router(router)
    return application


app = create_scheduler_app()
