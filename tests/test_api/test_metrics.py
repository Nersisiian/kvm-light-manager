import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_metrics_endpoint(async_client: AsyncClient):
    """Test metrics endpoint returns Prometheus format."""
    response = await async_client.get("/api/v1/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text