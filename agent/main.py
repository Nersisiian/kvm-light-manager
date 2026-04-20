import asyncio
import logging

from agent.server import AgentServer
from app.core.logging import setup_logging

logger = logging.getLogger(__name__)


async def main():
    setup_logging()
    server = AgentServer()
    try:
        await server.start()
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())