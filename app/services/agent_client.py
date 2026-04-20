import asyncio
import logging
import time
from enum import Enum
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.core.exceptions import AgentUnavailableError, AgentTimeoutError, CircuitBreakerOpenError
from app.messaging.client import ZeroMQClient
from app.messaging.schemas import AgentRequest, AgentResponse

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, failure_threshold: int, recovery_timeout: int):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()

    async def call(self, coro):
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker half-open, trying request")
                else:
                    raise CircuitBreakerOpenError("Circuit breaker is open")

        try:
            result = await coro
            if self.state == CircuitState.HALF_OPEN:
                await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e

    async def _on_success(self):
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            logger.info("Circuit breaker closed")

    async def _on_failure(self):
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning("Circuit breaker opened due to failures")


class AgentClient:
    def __init__(self, zmq_client: ZeroMQClient):
        self.zmq = zmq_client
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
        )

    async def send_request(self, request: AgentRequest) -> AgentResponse:
        async def _send():
            try:
                response_bytes = await asyncio.wait_for(
                    self.zmq.send_request(request.to_json()),
                    timeout=settings.AGENT_REQUEST_TIMEOUT,
                )
                return AgentResponse.from_json(response_bytes)
            except asyncio.TimeoutError:
                raise AgentTimeoutError("Agent request timed out")
            except Exception as e:
                raise AgentUnavailableError(f"Agent communication error: {e}")

        @retry(
            stop=stop_after_attempt(settings.AGENT_RETRY_ATTEMPTS),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((AgentUnavailableError, AgentTimeoutError)),
            reraise=True,
        )
        async def _retryable():
            return await self.circuit_breaker.call(_send())

        return await _retryable()


agent_client: Optional[AgentClient] = None


def init_agent_client(zmq_client: ZeroMQClient):
    global agent_client
    agent_client = AgentClient(zmq_client)