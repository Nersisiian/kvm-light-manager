import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import (
    CorrelationIDMiddleware,
    RequestLoggingMiddleware,
    MetricsMiddleware,
)
from app.db.session import engine
from app.services.redis_client import redis_client
from app.services.agent_client import agent_client, init_agent_client
from app.messaging.client import zmq_client
from app.services.task_manager import task_manager

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting KVM Light Manager API")
    await redis_client.initialize()
    await zmq_client.initialize()
    init_agent_client(zmq_client)
    yield
    # Shutdown
    logger.info("Shutting down KVM Light Manager API")
    await task_manager.shutdown(timeout=30.0)
    await redis_client.close()
    await zmq_client.close()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="KVM Light Manager",
        description="Enterprise Async VM Orchestration Service",
        version="2.0.0",
        lifespan=lifespan,
    )

    # Middleware order
    app.add_middleware(CorrelationIDMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    if settings.METRICS_ENABLED:
        app.add_middleware(MetricsMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()