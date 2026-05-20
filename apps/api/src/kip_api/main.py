from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kip_api.routes import auth, documents, health, organization, search, sync
from kip_core.config import get_settings
from kip_core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    settings = get_settings()
    logger.info("application_starting", app_name=settings.app_name, env=settings.app_env)
    yield
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Knowledge Infrastructure Platform API",
        description="Governance-aware enterprise knowledge retrieval",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    prefix = "/api/v1"
    app.include_router(health.router, prefix=prefix)
    app.include_router(auth.router, prefix=prefix)
    app.include_router(sync.router, prefix=prefix)
    app.include_router(search.router, prefix=prefix)
    app.include_router(documents.router, prefix=prefix)
    app.include_router(organization.router, prefix=prefix)
    return app


app = create_app()
