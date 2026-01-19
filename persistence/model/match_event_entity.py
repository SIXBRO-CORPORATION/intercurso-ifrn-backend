from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from persistence.model.abstract_entity import AbstractEntity


class MatchEventEntity(AbstractEntity):
    __tablename__ = "match_events"

    match_id = Column(ForeignKey("matches.id"), nullable=False)

    team_id = Column(ForeignKey("teams.id"), nullable=True)

    player_id = Column(ForeignKey("users.id"), nullable=True)

    event_type = Column(String(30), nullable=False)

    clock_seconds = Column(Integer, nullable=False)

    metadata = Column(JSONB, nullable=True)