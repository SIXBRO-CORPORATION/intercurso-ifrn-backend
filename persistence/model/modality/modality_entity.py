from sqlalchemy import Column, String, Integer
from persistence.model.abstract_entity import AbstractEntity


class ModalityEntity(AbstractEntity):
    __tablename__ = "modalities"

    name = Column(String(100), nullable=False, unique=True)
    min_members = Column(Integer, nullable=False)
    max_members = Column(Integer, nullable=False)

    gender_mode = Column(String(10), nullable=False, server_default="MIXED")

    min_male_members = Column(Integer, nullable=True)
    min_female_members = Column(Integer, nullable=True)
