from sqlalchemy import Column, Integer, ForeignKey
from persistence.model.abstract_entity import AbstractEntity


class BracketGroupTeamEntity(AbstractEntity):
    __tablename__ = "bracket_group_teams"

    bracket_group_id = Column(ForeignKey("bracket_groups.id"), nullable=False)

    team_id = Column(ForeignKey("teams.id"), nullable=False)

    points = Column(Integer, default=0, nullable=False)

    wins = Column(Integer, default=0, nullable=False)

    draws = Column(Integer, default=0, nullable=False)

    losses = Column(Integer, default=0, nullable=False)

    goals_for = Column(Integer, default=0, nullable=False)

    goals_against = Column(Integer, default=0, nullable=False)

    goals_difference = Column(Integer, default=0, nullable=False)