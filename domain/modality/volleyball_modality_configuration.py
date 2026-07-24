from dataclasses import dataclass
from uuid import UUID

from domain.abstract_domain import AbstractDomain

@dataclass
class VolleyballModalityConfiguration(AbstractDomain):

    modality_configuration_id: UUID = None
    points_per_set: int = 25
    final_set_points: int = 15
    sets_to_win: int = 2
