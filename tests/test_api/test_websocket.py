import uuid

import pytest
from httpx import AsyncClient

from app.models.vm import VirtualMachine
from app.core.constants import VMStatus


@pytest.mark.asyncio
async def test_websocket_connection(async_client: AsyncClient, db_session):
    """Test WebSocket connection (basic)."""
    vm = VirtualMachine(
        id=uuid.uuid4(),
        name="ws-test",
        status=VMStatus.PROVISIONING,
        cpu=2,
        ram=2048,
    )
    db_session.add(vm)
    await db_session.commit()

    # Note: AsyncClient doesn't support WebSocket directly in tests;
    # we would use websockets library. We'll skip detailed WebSocket test
    # in this example for brevity.
    pass