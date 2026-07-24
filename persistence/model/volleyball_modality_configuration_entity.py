from sqlalchemy import Column, Integer, ForeignKey
from persistence.model.abstract_entity import AbstractEntity


class VolleyballModalityConfigurationEntity(AbstractEntity):
    __tablename__ = "volleyball_modality_configurations"

    modality_configuration_id = Column(
        ForeignKey("modality_configurations.id"), nullable=False, unique=True
    )

    points_per_set = Column(Integer, default=25, nullable=False)

    final_set_points = Column(Integer, default=15, nullable=False)

    sets_to_win = Column(Integer, default=2, nullable=False)
