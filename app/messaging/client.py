import asyncio
import logging
from typing import Optional

import zmq
import zmq.asyncio

from app.core.config import settings

logger = logging.getLogger(__name__)


class ZeroMQClient:
    def __init__(self):
        self.context: Optional[zmq.asyncio.Context] = None
        self.socket: Optional[zmq.asyncio.Socket] = None
        self._lock = asyncio.Lock()

    async def initialize(self):
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.connect(settings.AGENT_ZMQ_ENDPOINT)
        logger.info(f"ZMQ DEALER connected to {settings.AGENT_ZMQ_ENDPOINT}")

    async def close(self):
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()

    async def send_request(self, request: bytes) -> bytes:
        async with self._lock:
            await self.socket.send(request)
            reply = await self.socket.recv()
            return reply


zmq_client = ZeroMQClient()