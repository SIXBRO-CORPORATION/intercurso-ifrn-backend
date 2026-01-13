from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from persistence.model.abstract_entity import AbstractEntity


class SeasonEntity(AbstractEntity):
    __tablename__ = "seasons"

    name = Column(String(100), nullable=False)

    year = Column(Integer, nullable=False)

    status = Column(String(30), nullable=False)

    registration_start_date = Column(DateTime(timezone=True), nullable=True)

    registration_end_date = Column(DateTime(timezone=True), nullable=True)

    registration_opened_at = Column(DateTime(timezone=True), nullable=True)

    registration_closed_at = Column(DateTime(timezone=True), nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)

    finished_at = Column(DateTime(timezone=True), nullable=True)

    rules_document = Column(Text, nullable=True)

    created_by = Column(ForeignKey("users.id"), nullable=False)