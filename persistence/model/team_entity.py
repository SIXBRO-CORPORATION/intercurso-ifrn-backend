from enum import Enum

from sqlalchemy import Column, String

from domain.enums.modality import ModalityType
from domain.enums.team_status import TeamStatus
from persistence.model.abstract_entity import AbstractEntity


class TeamEntity(AbstractEntity):

    __tablename__ = "teams"

    name = Column(
        String(255),
        nullable=False
    )

    photo = Column(
        String()
    )

    modality = Column(
        Enum(ModalityType),
        nullable=False
    )

    status = Column(
        Enum(TeamStatus),
        nullable=False
    )