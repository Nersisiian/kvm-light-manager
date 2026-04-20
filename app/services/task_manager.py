import asyncio
import logging
from typing import Coroutine, Any

logger = logging.getLogger(__name__)


class TaskManager:
    def __init__(self):
        self._tasks: set[asyncio.Task] = set()

    def create_task(self, coro: Coroutine[Any, Any, Any], name: str = None) -> asyncio.Task:
        task = asyncio.create_task(coro, name=name)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def shutdown(self, timeout: float = 30.0):
        if not self._tasks:
            return

        logger.info(f"Waiting for {len(self._tasks)} background tasks to finish...")
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._tasks, return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Some background tasks did not complete within {timeout}s")
            for task in self._tasks:
                if not task.done():
                    task.cancel()
            await asyncio.sleep(2)


task_manager = TaskManager()