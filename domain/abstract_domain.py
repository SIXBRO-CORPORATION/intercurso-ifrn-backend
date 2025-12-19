from dataclasses import dataclass
from abc import ABC
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class AbstractDomain(ABC):
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    active: bool = True

    def validate(self) -> None:
        pass
