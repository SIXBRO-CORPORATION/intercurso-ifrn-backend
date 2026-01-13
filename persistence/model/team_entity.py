from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from persistence.model.abstract_entity import AbstractEntity


class TeamEntity(AbstractEntity):
    __tablename__ = "teams"

    name = Column(String(100), nullable=False)

    season_id = Column(ForeignKey("seasons.id"), nullable=False)

    modality_id = Column(ForeignKey("modalities.id"), nullable=False)

    owner_id = Column(ForeignKey("users.id"), nullable=False)

    captain_id = Column(ForeignKey("users.id"), nullable=True)

    status = Column(String(30), nullable=False, default="DRAFT")

    invite_token = Column(UUID(as_uuid=True), unique=True, nullable=False)

    token_active = Column(Boolean, default=True)

    photo = Column(Text, nullable=True)

    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)