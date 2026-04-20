from typing import Any, Optional
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    extra: Optional[dict[str, Any]] = None