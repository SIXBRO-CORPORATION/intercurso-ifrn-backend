from sqlalchemy import Column, String, DateTime, ForeignKey, UUID as SQLUUID
from persistence.model.abstract_entity import AbstractEntity


class DeviceTokenEntity(AbstractEntity):
    __tablename__ = "device_tokens"

    user_id = Column(
        SQLUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    token = Column(String(500), nullable=False, unique=True, index=True)

    platform = Column(String(10), nullable=False)

    last_used_at = Column(DateTime, nullable=True)
