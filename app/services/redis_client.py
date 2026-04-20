import json
from typing import List, Dict, Any, Optional

import redis.asyncio as redis

from app.core.config import settings


class RedisClient:
    def __init__(self):
        self.client: Optional[redis.Redis] = None

    async def initialize(self):
        self.client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    async def close(self):
        if self.client:
            await self.client.close()

    async def add_log(self, vm_id: str, log_entry: Dict[str, Any]) -> None:
        key = f"logs:{vm_id}"
        await self.client.rpush(key, json.dumps(log_entry))
        await self.client.ltrim(key, -1000, -1)

    async def get_logs(self, vm_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        key = f"logs:{vm_id}"
        items = await self.client.lrange(key, -limit, -1)
        return [json.loads(item) for item in items]

    async def publish_log(self, vm_id: str, log_entry: Dict[str, Any]) -> None:
        channel = f"vm_logs:{vm_id}"
        await self.client.publish(channel, json.dumps(log_entry))

    async def delete_logs(self, vm_id: str) -> None:
        key = f"logs:{vm_id}"
        await self.client.delete(key)


redis_client = RedisClient()