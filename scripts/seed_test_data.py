#!/usr/bin/env python3
"""Seed database with test VMs for development."""
import asyncio
import uuid

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.vm import VirtualMachine
from app.core.constants import VMStatus


async def seed():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        for i in range(5):
            vm = VirtualMachine(
                id=uuid.uuid4(),
                name=f"test-vm-{i}",
                status=VMStatus.STOPPED,
                cpu=2,
                ram=2048,
                host="agent-01",
            )
            session.add(vm)
        await session.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())