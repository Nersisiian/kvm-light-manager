import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_vm_with_mock_agent(async_client: AsyncClient, mock_zmq_client):
    response = await async_client.post(
        "/api/v1/vms",
        json={"name": "test", "cpu": 2, "ram": 2048},
    )
    assert response.status_code == 202
    mock_zmq_client.send_request.assert_called_once()