from typing import TypeVar, Generic, Optional
from datetime import datetime

from pydantic import BaseModel, Field

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):

    success: bool = Field(
        default=True
    )

    data: Optional[T] = Field(
        default=None
    )

    message: Optional[str] = Field(
        default=None
    )

    error: Optional[str] = Field(
        default=None
    )

    code: Optional[str] = Field(
        default=None
    )

    timestamp: datetime = Field(
        default_factory=datetime.now()
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": "123", "name": "John Doe"},
                "message": "Operation successful",
                "timestamp": "2024-01-01T00:00:00"
            }
        }

    @classmethod
    def success(
            cls,
            data: Optional[T] = None,
            message: Optional[T] = None
    ) -> "ApiResponse[T]":
        return cls(
            success=True,
            data=data,
            message=message,
            timestamp=datetime.now()
        )

    @classmethod
    def error(
            cls,
            error: str,
            code: Optional[str] = None
    ) -> "ApiResponse[T]":
        return cls(
            success=False,
            error=error,
            code=code,
            timestamp=datetime.now()
        )