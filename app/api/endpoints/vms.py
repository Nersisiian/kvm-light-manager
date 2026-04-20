import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.vm import (
    VMCreateRequest,
    VMCreateResponse,
    VMResponse,
    VMPowerAction,
    VMStatusResponse,
)
from app.services.vm_service import VMService
from app.services.redis_client import redis_client
from app.services.agent_client import agent_client

router = APIRouter(prefix="/vms", tags=["Virtual Machines"])
logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=VMCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a new virtual machine",
)
async def create_vm(
    request: VMCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    service = VMService(db, redis_client, agent_client)
    vm_id, task_id = await service.create_vm(request)
    return VMCreateResponse(vm_id=vm_id, task_id=task_id, status="provisioning")


@router.get(
    "/{vm_id}/status",
    response_model=VMStatusResponse,
    summary="Get VM status",
)
async def get_vm_status(
    vm_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = VMService(db, redis_client, agent_client)
    vm = await service.get_vm(vm_id)
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    return VMStatusResponse.model_validate(vm)


@router.delete(
    "/{vm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a VM",
)
async def delete_vm(
    vm_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = VMService(db, redis_client, agent_client)
    success = await service.delete_vm(vm_id)
    if not success:
        raise HTTPException(status_code=404, detail="VM not found")
    return


@router.post(
    "/{vm_id}/power",
    response_model=VMResponse,
    summary="Power control (start/stop/reboot)",
)
async def power_action(
    vm_id: UUID,
    action: VMPowerAction,
    db: AsyncSession = Depends(get_db),
):
    service = VMService(db, redis_client, agent_client)
    vm = await service.power_action(vm_id, action.action)
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    return VMResponse.model_validate(vm)