from dataclasses import dataclass

from domain.abstract_domain import AbstractDomain


@dataclass
class Modality(AbstractDomain):
    name: str = None
    min_members: int = None
    max_members: int = None
    