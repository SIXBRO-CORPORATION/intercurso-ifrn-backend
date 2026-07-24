from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from persistence.model.abstract_entity import AbstractEntity


class MatchSetEntity(AbstractEntity):
    __tablename__ = "match_sets"
    __table_args__ = (
        UniqueConstraint("match_id", "set_number", name="uq_match_sets_match_id_set_number"),
    )

    match_id = Column(ForeignKey("matches.id"), nullable=False)

    set_number = Column(Integer, nullable=False)

    team1_points = Column(Integer, nullable=False)

    team2_points = Column(Integer, nullable=False)

    winner_team_id = Column(ForeignKey("teams.id"), nullable=False)
