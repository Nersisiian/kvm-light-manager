import json
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    action: str
    payload: dict[str, Any]
    request_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))

    def to_json(self) -> bytes:
        return self.model_dump_json().encode()


class AgentResponse(BaseModel):
    request_id: str
    status: str  # "success" or "error"
    data: Optional[dict[str, Any]] = None
    error: Optional[str] = None

    @classmethod
    def from_json(cls, data: bytes) -> "AgentResponse":
        return cls.model_validate_json(data.decode())


class ProvisionRequest(BaseModel):
    vm_id: uuid.UUID
    name: str
    cpu: int
    ram: int
    base_image: str