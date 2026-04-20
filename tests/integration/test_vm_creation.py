import uuid
import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.vm import VirtualMachine
from app.core.constants import VMStatus


@pytest.mark.asyncio
async def test_full_vm_creation_flow(async_client: AsyncClient, db_session):
    """Integration test: create VM and poll status until completion."""
    # Mock agent response for success
    with patch("app.services.agent_client.AgentClient.send_request") as mock_send:
        mock_send.return_value = AsyncMock(
            status="success",
            data={"host": "agent-01", "vm_id": str(uuid.uuid4())},
        )
        # Create VM
        response = await async_client.post(
            "/api/v1/vms",
            json={"name": "integration-test", "cpu": 2, "ram": 2048},
        )
        assert response.status_code == 202
        data = response.json()
        vm_id = data["vm_id"]

        # Wait for background task to complete (max 10 seconds)
        for _ in range(20):
            await asyncio.sleep(0.5)
            status_resp = await async_client.get(f"/api/v1/vms/{vm_id}/status")
            if status_resp.status_code == 200:
                vm_data = status_resp.json()
                if vm_data["status"] in (VMStatus.STOPPED, VMStatus.ERROR):
                    break

        # Final check
        status_resp = await async_client.get(f"/api/v1/vms/{vm_id}/status")
        assert status_resp.status_code == 200
        assert status_resp.json()["status"] == VMStatus.STOPPED