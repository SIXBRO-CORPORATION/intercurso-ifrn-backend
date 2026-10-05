from dataclasses import dataclass
from typing import Optional

from domain.abstract_domain import AbstractDomain
from domain.enums.modality_gender_mode import ModalityGenderMode


@dataclass
class Modality(AbstractDomain):
    name: str = None
    min_members: int = None
    max_members: int = None
    gender_mode: Optional[ModalityGenderMode] = None
    min_male_members: Optional[int] = None
    min_female_members: Optional[int] = None
