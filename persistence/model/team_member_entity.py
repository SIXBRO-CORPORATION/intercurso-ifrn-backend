from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from persistence.model.abstract_entity import AbstractEntity


class TeamMemberEntity(AbstractEntity):
    __tablename__ = "team_members"

    team_id = Column(ForeignKey("teams.id"), nullable=False)

    user_id = Column(ForeignKey("users.id"), nullable=False)

    role = Column(String(20), nullable=False)

    donation_status = Column(String(30), nullable=False)

    donation_confirmed_at = Column(DateTime(timezone=True), nullable=True)

    donation_confirmed_by = Column(ForeignKey("users.id"), nullable=True)

    joined_at = Column(DateTime(timezone=True), nullable=False)