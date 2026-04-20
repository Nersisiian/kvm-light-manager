import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.models.vm import VirtualMachine
from app.core.constants import VMStatus


@pytest.mark.asyncio
async def test_create_vm(async_client: AsyncClient, db_session):
    """Test VM creation endpoint."""
    with patch("app.services.agent_client.AgentClient.send_request") as mock_send:
        mock_send.return_value = AsyncMock(
            status="success",
            data={"host": "agent-01", "vm_id": str(uuid.uuid4())},
        )
        response = await async_client.post(
            "/api/v1/vms",
            json={
                "name": "test-vm",
                "cpu": 2,
                "ram": 2048,
            },
        )
    assert response.status_code == 202
    data = response.json()
    assert "vm_id" in data
    assert "task_id" in data
    assert data["status"] == "provisioning"


@pytest.mark.asyncio
async def test_get_vm_status(async_client: AsyncClient, db_session):
    """Test getting VM status."""
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name="existing-vm",
        status=VMStatus.STOPPED,
        cpu=2,
        ram=2048,
    )
    db_session.add(vm)
    await db_session.commit()

    response = await async_client.get(f"/api/v1/vms/{vm.id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(vm.id)
    assert data["status"] == "stopped"


@pytest.mark.asyncio
async def test_delete_vm(async_client: AsyncClient, db_session):
    """Test VM deletion."""
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name="to-delete",
        status=VMStatus.STOPPED,
        cpu=1,
        ram=1024,
    )
    db_session.add(vm)
    await db_session.commit()

    with patch("app.services.agent_client.AgentClient.send_request") as mock_send:
        mock_send.return_value = AsyncMock(status="success")
        response = await async_client.delete(f"/api/v1/vms/{vm.id}")
    assert response.status_code == 204

    # Verify deleted
    response = await async_client.get(f"/api/v1/vms/{vm.id}/status")
    assert response.status_code == 404