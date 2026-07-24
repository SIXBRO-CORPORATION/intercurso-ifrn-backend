from sqlalchemy import Column, ForeignKey

from persistence.model.abstract_entity import AbstractEntity


class SeasonModalityEntity(AbstractEntity):
    __tablename__ = "season_modalities"

    season_id = Column(ForeignKey("seasons.id"), nullable=False)
    
    modality_id = Column(ForeignKey("modalities.id"), nullable=False)
