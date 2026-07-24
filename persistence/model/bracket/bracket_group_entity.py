from sqlalchemy import Column, String, Integer, ForeignKey
from persistence.model.abstract_entity import AbstractEntity


class BracketGroupEntity(AbstractEntity):
    __tablename__ = "bracket_groups"

    bracket_id = Column(ForeignKey("brackets.id"), nullable=False)

    name = Column(String(50), nullable=False)

    display_order = Column(Integer, nullable=False, default=0)