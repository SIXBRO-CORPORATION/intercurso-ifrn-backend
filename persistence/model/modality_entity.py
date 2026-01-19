from sqlalchemy import Column, String, Integer, Text
from persistence.model.abstract_entity import AbstractEntity


class ModalityEntity(AbstractEntity):
    __tablename__ = "modalities"

    name = Column(String(100), nullable=False, unique=True)
    min_members = Column(Integer, nullable=False)
    max_members = Column(Integer, nullable=False)