import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import VMStatus, PowerAction
from app.models.vm import VirtualMachine
from app.schemas.vm import VMCreateRequest
from app.services.redis_client import RedisClient
from app.services.agent_client import AgentClient
from app.messaging.schemas import AgentRequest, AgentResponse, ProvisionRequest
from app.services.task_manager import task_manager
from app.db.repositories import VMRepository

logger = logging.getLogger(__name__)


class VMService:
    def __init__(
        self,
        db: AsyncSession,
        redis: RedisClient,
        agent: Optional[AgentClient] = None,
    ):
        self.db = db
        self.redis = redis
        self.agent = agent
        self.repo = VMRepository(db)

    async def create_vm(self, request: VMCreateRequest) -> Tuple[uuid.UUID, str]:
        vm_id = uuid.uuid4()
        task_id = str(uuid.uuid4())

        vm = VirtualMachine(
            id=vm_id,
            name=request.name,
            status=VMStatus.PENDING,
            cpu=request.cpu,
            ram=request.ram,
        )
        await self.repo.create(vm)

        task_manager.create_task(
            self._provision_vm(vm_id, request, task_id),
            name=f"provision-{vm_id}"
        )
        return vm_id, task_id

    async def _provision_vm(self, vm_id: uuid.UUID, request: VMCreateRequest, task_id: str):
        try:
            await self._log_progress(vm_id, task_id, "Starting VM provisioning...", "info")
            await self.repo.update_status(vm_id, VMStatus.PROVISIONING)

            agent_req = AgentRequest(
                action="provision",
                payload=ProvisionRequest(
                    vm_id=vm_id,
                    name=request.name,
                    cpu=request.cpu,
                    ram=request.ram,
                    base_image=request.base_image or "ubuntu-22.04-cloudimg",
                ).model_dump(mode="json"),
                request_id=task_id,
            )

            await self._log_progress(vm_id, task_id, "Sending provision request to agent...", "info")
            response = await self.agent.send_request(agent_req)

            if response.status == "success":
                await self._log_progress(vm_id, task_id, f"Provisioning completed. Host: {response.data.get('host')}", "info")
                await self.repo.update_status(vm_id, VMStatus.STOPPED, host=response.data.get("host"))
            else:
                await self._log_progress(vm_id, task_id, f"Provisioning failed: {response.error}", "error")
                await self.repo.update_status(vm_id, VMStatus.ERROR)

        except Exception as e:
            logger.exception("Provisioning failed")
            await self._log_progress(vm_id, task_id, f"Provisioning error: {str(e)}", "error")
            await self.repo.update_status(vm_id, VMStatus.ERROR)

    async def _log_progress(self, vm_id: uuid.UUID, task_id: str, message: str, level: str = "info"):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": task_id,
            "level": level,
            "message": message,
        }
        await self.redis.add_log(str(vm_id), log_entry)
        await self.redis.publish_log(str(vm_id), log_entry)

    async def get_vm(self, vm_id: uuid.UUID) -> Optional[VirtualMachine]:
        return await self.repo.get_by_id(vm_id)

    async def delete_vm(self, vm_id: uuid.UUID) -> bool:
        vm = await self.repo.get_by_id(vm_id)
        if not vm:
            return False

        if vm.host and self.agent:
            agent_req = AgentRequest(
                action="delete",
                payload={"vm_id": str(vm_id)},
            )
            try:
                await self.agent.send_request(agent_req)
            except Exception as e:
                logger.error(f"Agent delete failed for VM {vm_id}: {e}")

        success = await self.repo.delete(vm_id)
        await self.redis.delete_logs(str(vm_id))
        return success

    async def power_action(self, vm_id: uuid.UUID, action: PowerAction) -> Optional[VirtualMachine]:
        vm = await self.repo.get_by_id(vm_id)
        if not vm or not vm.host:
            return None

        agent_req = AgentRequest(
            action=action.value,
            payload={"vm_id": str(vm_id)},
        )
        response = await self.agent.send_request(agent_req)

        if response.status == "success":
            new_status = {
                PowerAction.START: VMStatus.RUNNING,
                PowerAction.STOP: VMStatus.STOPPED,
                PowerAction.REBOOT: VMStatus.RUNNING,
            }.get(action, vm.status)
            vm = await self.repo.update_status(vm_id, new_status)
            return vm
        else:
            logger.error(f"Power action {action} failed for VM {vm_id}: {response.error}")
            return vm