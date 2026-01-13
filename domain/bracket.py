from domain.abstract_domain import AbstractDomain
from dataclasses import dataclass, field
from uuid import UUID

from domain.enums.bracket_status import BracketStatus
from domain.enums.modality_format import ModalityFormat


@dataclass
class Bracket(AbstractDomain):
    season_id: UUID = None
    modality_id: UUID = None
    format: ModalityFormat = None
    configuration: dict = field(default_factory=dict)
    status: BracketStatus = None
    created_by: UUID = None
