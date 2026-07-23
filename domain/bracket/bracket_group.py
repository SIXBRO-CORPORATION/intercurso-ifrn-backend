from dataclasses import dataclass
from uuid import UUID

from domain.abstract_domain import AbstractDomain


@dataclass
class BracketGroup(AbstractDomain):
    bracket_id: UUID = None
    name: str = None
    display_order: int = None