from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.core.constants import VMStatus, PowerAction as PowerActionEnum


class VMCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    cpu: int = Field(..., ge=1, le=64)
    ram: int = Field(..., ge=512, le=262144)
    base_image: Optional[str] = Field(default="ubuntu-22.04-cloudimg")


class VMCreateResponse(BaseModel):
    vm_id: UUID
    task_id: str
    status: str = "provisioning"


class VMResponse(BaseModel):
    id: UUID
    name: str
    status: VMStatus
    cpu: int
    ram: int
    host: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class VMStatusResponse(VMResponse):
    pass


class VMPowerAction(BaseModel):
    action: PowerActionEnum