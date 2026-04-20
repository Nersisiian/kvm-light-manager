import uuid
from typing import Optional, List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vm import VirtualMachine
from app.core.constants import VMStatus


class VMRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, vm: VirtualMachine) -> VirtualMachine:
        self.session.add(vm)
        await self.session.flush()
        return vm

    async def get_by_id(self, vm_id: uuid.UUID) -> Optional[VirtualMachine]:
        stmt = select(VirtualMachine).where(VirtualMachine.id == vm_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[VirtualMachine]:
        stmt = select(VirtualMachine).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, vm_id: uuid.UUID, status: VMStatus, host: Optional[str] = None) -> Optional[VirtualMachine]:
        vm = await self.get_by_id(vm_id)
        if vm:
            vm.status = status
            if host:
                vm.host = host
            await self.session.flush()
        return vm

    async def delete(self, vm_id: uuid.UUID) -> bool:
        stmt = delete(VirtualMachine).where(VirtualMachine.id == vm_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0