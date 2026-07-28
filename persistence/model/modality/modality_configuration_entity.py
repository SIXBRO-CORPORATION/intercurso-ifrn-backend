from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from persistence.model.abstract_entity import AbstractEntity


class ModalityConfigurationEntity(AbstractEntity):
    __tablename__ = "modality_configurations"

    modality_id = Column(ForeignKey("modalities.id"), nullable=False, unique=True)

    num_periods = Column(Integer, default=2, nullable=False)

    period_durations_minutes = Column(Integer, nullable=False)

    score_type = Column(String(50), nullable=False)

    has_third_place_match = Column(Boolean, default=True, nullable=False)

    metadata_json = Column(JSONB, nullable=True)