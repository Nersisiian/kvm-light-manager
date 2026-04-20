from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, Counter, Histogram

from app.core.config import settings

router = APIRouter(prefix="/metrics", tags=["Metrics"])

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"]
)


@router.get("")
async def get_metrics():
    if not settings.METRICS_ENABLED:
        return Response(content="Metrics disabled", media_type="text/plain")
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )