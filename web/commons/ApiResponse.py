from typing import TypeVar, Generic, Optional
from datetime import datetime

from pydantic import BaseModel, Field

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):

    success: bool = Field(
        default=True,
        description="Indica se a operação foi bem-sucedida"
    )

    data: Optional[T] = Field(
        default=None,
        description="Dados de resposta"
    )

    message: Optional[str] = Field(
        default=None,
        description="Mensagem descritiva"
    )

    error: Optional[str] = Field(
        default=None,
        description="Mensagem de erro"
    )

    code: Optional[str] = Field(
        default=None,
        description="Código de erro"
    )

    timestamp: datetime = Field(
        default_factory=datetime.now,  # ← CORRETO: função sem ()
        description="Timestamp da resposta"
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
            message: Optional[str] = None
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
            code: Optional[str] = None,
            data: Optional[T] = None
    ) -> "ApiResponse[T]":
        return cls(
            success=False,
            error=error,
            code=code,
            data=data,
            timestamp=datetime.now()
        )