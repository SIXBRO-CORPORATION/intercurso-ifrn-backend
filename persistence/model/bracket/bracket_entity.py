from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from persistence.model.abstract_entity import AbstractEntity


class BracketEntity(AbstractEntity):
    __tablename__ = "brackets"

    season_id = Column(ForeignKey("seasons.id"), nullable=False)

    modality_id = Column(ForeignKey("modalities.id"), nullable=False)

    format = Column(String(30), nullable=False)

    configuration = Column(JSONB, nullable=False, default={})

    status = Column(String(20), nullable=False)

    created_by = Column(ForeignKey("users.id"), nullable=False)