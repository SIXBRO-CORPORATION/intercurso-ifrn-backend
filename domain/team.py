from dataclasses import dataclass

from domain.abstract_domain import AbstractDomain
from domain.enums.modality import ModalityType

@dataclass
class Team(AbstractDomain):

    name: str = None
    photo: str = None
    modality: ModalityType = None