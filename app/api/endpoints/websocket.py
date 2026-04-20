import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.services.redis_client import redis_client
from app.services.vm_service import VMService

router = APIRouter(prefix="/ws", tags=["WebSocket"])
logger = logging.getLogger(__name__)


@router.websocket("/logs/{vm_id}")
async def websocket_logs(
    websocket: WebSocket,
    vm_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await websocket.accept()
    service = VMService(db, redis_client, None)

    vm = await service.get_vm(vm_id)
    if not vm:
        await websocket.close(code=1008, reason="VM not found")
        return

    channel = f"vm_logs:{vm_id}"
    pubsub = redis_client.client.pubsub()
    await pubsub.subscribe(channel)

    try:
        logs = await redis_client.get_logs(str(vm_id))
        for log_entry in logs:
            await websocket.send_text(json.dumps(log_entry))

        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_text(json.dumps(data))
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for VM {vm_id}")
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()