from dataclasses import dataclass

from domain.abstract_domain import AbstractDomain
from domain.enums.season_status import SeasonStatus
from datetime import datetime
from uuid import UUID


@dataclass
class Season(AbstractDomain):
    name: str = None
    year: int = None
    status: SeasonStatus = None
    registration_start_date: datetime = None
    registration_end_date: datetime = None
    registration_opened_at: datetime = None
    registration_closed_at: datetime = None
    started_at: datetime = None
    finished_at: datetime = None
    rules_document: str = None
    created_by: UUID = None