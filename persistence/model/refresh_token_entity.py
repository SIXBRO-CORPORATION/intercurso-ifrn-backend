from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, UUID as SQLUUID
from persistence.model.abstract_entity import AbstractEntity


class RefreshTokenEntity(AbstractEntity):
    __tablename__ = "refresh_tokens"

    user_id = Column(
        SQLUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    token = Column(String(500), nullable=False, unique=True, index=True)

    expires_at = Column(DateTime, nullable=False, index=True)

    revoked = Column(Boolean, nullable=False, default=False)

    revoked_at = Column(DateTime, nullable=True)

    replaced_by_token = Column(
        SQLUUID, ForeignKey("refresh_tokens.id", ondelete="SET NULL"), nullable=True
    )
