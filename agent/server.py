import asyncio
import logging
from typing import Optional

import zmq
import zmq.asyncio

from agent.config import settings
from agent.handlers import handle_request
from app.messaging.schemas import AgentResponse

logger = logging.getLogger(__name__)


class AgentServer:
    def __init__(self):
        self.context: Optional[zmq.asyncio.Context] = None
        self.socket: Optional[zmq.asyncio.Socket] = None
        self.running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.ROUTER)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.bind(settings.ZMQ_BIND_ADDR)
        self.running = True
        self._task = asyncio.create_task(self._run())
        logger.info(f"Agent ROUTER listening on {settings.ZMQ_BIND_ADDR}")

    async def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        logger.info("Agent server stopped")

    async def _run(self):
        while self.running:
            try:
                identity = await self.socket.recv()
                # ROUTER may have an empty frame
                if self.socket.getsockopt(zmq.RCVMORE):
                    empty = await self.socket.recv()
                request_bytes = await self.socket.recv()
                asyncio.create_task(self._handle_request(identity, request_bytes))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in receive loop: {e}")

    async def _handle_request(self, identity: bytes, request_bytes: bytes):
        try:
            response: AgentResponse = await handle_request(request_bytes)
            reply = response.model_dump_json().encode()
        except Exception as e:
            logger.exception("Handler error")
            response = AgentResponse(
                request_id="unknown",
                status="error",
                error=f"Internal error: {str(e)}",
            )
            reply = response.model_dump_json().encode()
        await self.socket.send_multipart([identity, b"", reply])