import logging
import os
import uuid

from agent.simulator import LibvirtSimulator
from app.messaging.schemas import AgentRequest, AgentResponse

logger = logging.getLogger(__name__)
simulator = LibvirtSimulator()


async def handle_request(request_bytes: bytes) -> AgentResponse:
    try:
        request = AgentRequest.model_validate_json(request_bytes.decode())
    except Exception as e:
        return AgentResponse(
            request_id="unknown",
            status="error",
            error=f"Invalid request: {str(e)}",
        )

    logger.info(f"Received action: {request.action} (req_id={request.request_id})")

    if request.action == "ping":
        return AgentResponse(
            request_id=request.request_id,
            status="success",
            data={"host": os.environ.get("HOSTNAME", "agent-01")},
        )
    elif request.action == "provision":
        return await handle_provision(request)
    elif request.action in ("start", "stop", "reboot"):
        return await handle_power(request)
    elif request.action == "delete":
        return await handle_delete(request)
    else:
        return AgentResponse(
            request_id=request.request_id,
            status="error",
            error=f"Unknown action: {request.action}",
        )


async def handle_provision(request: AgentRequest) -> AgentResponse:
    payload = request.payload
    vm_id = payload.get("vm_id")
    name = payload.get("name")
    cpu = payload.get("cpu")
    ram = payload.get("ram")
    base_image = payload.get("base_image", "ubuntu-22.04-cloudimg")

    if not all([vm_id, name, cpu, ram]):
        return AgentResponse(
            request_id=request.request_id,
            status="error",
            error="Missing required fields",
        )

    try:
        host = await simulator.create_vm(
            vm_id=uuid.UUID(vm_id),
            name=name,
            cpu=cpu,
            ram=ram,
            base_image=base_image,
        )
        return AgentResponse(
            request_id=request.request_id,
            status="success",
            data={"host": host, "vm_id": vm_id},
        )
    except Exception as e:
        logger.exception("Provisioning failed")
        return AgentResponse(
            request_id=request.request_id,
            status="error",
            error=str(e),
        )


async def handle_power(request: AgentRequest) -> AgentResponse:
    vm_id = request.payload.get("vm_id")
    if not vm_id:
        return AgentResponse(
            request_id=request.request_id,
            status="error",
            error="Missing vm_id",
        )

    try:
        await simulator.power_action(uuid.UUID(vm_id), request.action)
        return AgentResponse(
            request_id=request.request_id,
            status="success",
            data={"vm_id": vm_id, "action": request.action},
        )
    except Exception as e:
        return AgentResponse(
            request_id=request.request_id,
            status="error",
            error=str(e),
        )


async def handle_delete(request: AgentRequest) -> AgentResponse:
    vm_id = request.payload.get("vm_id")
    if not vm_id:
        return AgentResponse(
            request_id=request.request_id,
            status="error",
            error="Missing vm_id",
        )

    try:
        await simulator.delete_vm(uuid.UUID(vm_id))
        return AgentResponse(
            request_id=request.request_id,
            status="success",
            data={"vm_id": vm_id},
        )
    except Exception as e:
        return AgentResponse(
            request_id=request.request_id,
            status="error",
            error=str(e),
        )