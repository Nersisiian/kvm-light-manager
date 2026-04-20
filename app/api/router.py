from fastapi import APIRouter

from app.api.endpoints import vms, websocket, metrics, health

api_router = APIRouter()

api_router.include_router(vms.router)
api_router.include_router(websocket.router)
api_router.include_router(metrics.router)
api_router.include_router(health.router)