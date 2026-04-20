import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.services.redis_client import redis_client
from app.services.agent_client import agent_client
from app.messaging.schemas import AgentRequest

router = APIRouter(prefix="/health", tags=["Health"])
logger = logging.getLogger(__name__)


@router.get("/live", summary="Liveness probe")
async def liveness():
    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe")
async def readiness(db: AsyncSession = Depends(get_db)):
    status = {"status": "ok", "details": {}}

    try:
        await db.execute(text("SELECT 1"))
        status["details"]["database"] = "ok"
    except Exception as e:
        status["status"] = "degraded"
        status["details"]["database"] = f"error: {str(e)}"
        logger.error(f"Database health check failed: {e}")

    try:
        await redis_client.client.ping()
        status["details"]["redis"] = "ok"
    except Exception as e:
        status["status"] = "degraded"
        status["details"]["redis"] = f"error: {str(e)}"
        logger.error(f"Redis health check failed: {e}")

    try:
        response = await agent_client.send_request(AgentRequest(action="ping", payload={}))
        if response.status == "success":
            status["details"]["agent"] = "ok"
        else:
            status["details"]["agent"] = f"error: {response.error}"
            if status["status"] == "ok":
                status["status"] = "degraded"
    except Exception as e:
        status["details"]["agent"] = f"error: {str(e)}"
        if status["status"] == "ok":
            status["status"] = "degraded"

    return status


@router.get("/status", summary="Detailed health status")
async def detailed_status(db: AsyncSession = Depends(get_db)):
    info: Dict[str, Any] = {
        "service": "kvm-light-manager",
        "version": "2.0.0",
        "environment": "development",
    }

    pool = db.get_bind().pool
    info["database_pool"] = {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "overflow": pool.overflow(),
        "total": pool.total(),
    }

    return info