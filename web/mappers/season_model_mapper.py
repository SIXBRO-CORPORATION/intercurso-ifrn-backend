from typing import List

from domain.season import Season
from domain.season_modality import SeasonModality
from web.models.response.season_create_response import SeasonCreateResponse


class SeasonModelMapper:
    def to_create_response(
        self, season: Season, season_modalities: List[SeasonModality]
    ) -> SeasonCreateResponse:
        return SeasonCreateResponse(
            season_id=season.id,
            name=season.name,
            year=season.year,
            status=season.status.value,
            active=season.active,
            registration_start_date=season.registration_start_date,
            registration_end_date=season.registration_end_date,
            modality_ids=[
                season_modality.modality_id for season_modality in season_modalities
            ],
            message="Temporada criada com sucesso!",
        )
