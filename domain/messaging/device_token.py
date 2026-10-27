from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from domain.abstract_domain import AbstractDomain
from domain.enums.device_platform import DevicePlatform
from domain.exceptions.business_exception import BusinessException


@dataclass
class DeviceToken(AbstractDomain):

    user_id: UUID = None
    token: str = None
    platform: DevicePlatform = None
    last_used_at: Optional[datetime] = None

    def validate(self) -> None:
        if not self.user_id:
            raise BusinessException("Device token precisa estar vinculado a um usuário")

        if not self.token:
            raise BusinessException("Device token não pode ser vazio")

        if self.platform is None:
            raise BusinessException("Device token precisa informar a plataforma")

    def deactivate(self) -> None:
        self.active = False

    def touch(self, moment: Optional[datetime] = None) -> None:
        self.last_used_at = moment or datetime.now()
