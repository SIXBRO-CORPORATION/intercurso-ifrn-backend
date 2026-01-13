from dataclasses import dataclass
from typing import Any

from domain.abstract_domain import AbstractDomain
from uuid import UUID

from domain.enums.score_type import ScoreType


@dataclass
class ModalityConfiguration(AbstractDomain):
    season_modality_id: UUID = None
    num_periods: int = None
    period_durations_minutes: int = None
    score_type: ScoreType = None
    has_third_place_match: bool = None
    metadata: Any = None
