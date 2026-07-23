from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

@dataclass
class SeasonModality:
    id: UUID = None
    season_id: UUID = None
    modality_id: UUID = None
    created_at: datetime = None