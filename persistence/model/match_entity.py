from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from persistence.model.abstract_entity import AbstractEntity


class MatchEntity(AbstractEntity):
    __tablename__ = "matches"

    bracket_id = Column(ForeignKey("brackets.id"), nullable=False)

    bracket_group_id = Column(ForeignKey("bracket_groups.id"), nullable=True)

    team1_id = Column(ForeignKey("teams.id"), nullable=True)

    team2_id = Column(ForeignKey("teams.id"), nullable=True)

    winner_id = Column(ForeignKey("teams.id"), nullable=True)

    match_type = Column(String(20), nullable=False)

    match_category = Column(String(20), nullable=False)

    status = Column(String(20), nullable=False)

    scheduled_date = Column(DateTime(timezone=True), nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)

    finished_at = Column(DateTime(timezone=True), nullable=True)

    team1_score = Column(Integer, default=0, nullable=False)

    team2_score = Column(Integer, default=0, nullable=False)

    penality_result = Column(JSONB, nullable=True)

    clock_seconds = Column(Integer, default=0, nullable=False)

    clock_running = Column(Boolean, default=False, nullable=False)

    current_period = Column(Integer, default=1, nullable=False)

    is_bye = Column(Boolean, default=False, nullable=False)

    metadata = Column(JSONB, nullable=True)