from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class AuthToken:
    access_token: str
    token_type: str = "bearer"
    expires_at: Optional[datetime] = None
    user_id: Optional[UUID] = None


class SUAPUserData:
    pass
