from typing import List, Optional

from core.storage.file_storage_port import FileStoragePort
from domain.season.season import Season
from domain.season.season_modality import SeasonModality
from web.models.response.season.season_create_response import SeasonCreateResponse
from web.models.response.season.season_details_response import SeasonDetailsResponse
from web.models.response.season.season_status_response import SeasonStatusResponse
from web.models.response.season.season_summary_response import SeasonSummaryResponse


class SeasonModelMapper:
    def __init__(self, file_storage: FileStoragePort):
        self.file_storage = file_storage

    def _resolve_rules_document_url(
        self, rules_document_object_key: Optional[str]
    ) -> Optional[str]:
        if not rules_document_object_key:
            return None
        return self.file_storage.generate_presigned_url(rules_document_object_key)

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
            rules_document=self._resolve_rules_document_url(season.rules_document),
            message="Temporada criada com sucesso!",
        )

    def to_summary_response(self, season: Season) -> SeasonSummaryResponse:
        return SeasonSummaryResponse(
            season_id=season.id,
            name=season.name,
            year=season.year,
            status=season.status.value,
            active=season.active,
            registration_start_date=season.registration_start_date,
            registration_end_date=season.registration_end_date,
        )

    def to_status_response(self, season: Season, message: str) -> SeasonStatusResponse:
        return SeasonStatusResponse(
            season_id=season.id,
            name=season.name,
            status=season.status.value,
            active=season.active,
            registration_start_date=season.registration_start_date,
            registration_end_date=season.registration_end_date,
            registration_closed_at=season.registration_closed_at,
            finished_at=season.finished_at,
            message=message,
        )

    def to_details_response(
        self,
        season: Season,
        season_modalities: List[SeasonModality],
        total_teams_created: int,
        total_teams_submitted: int,
        total_teams_approved: int,
        available_actions: List[str],
    ) -> SeasonDetailsResponse:
        return SeasonDetailsResponse(
            season_id=season.id,
            name=season.name,
            year=season.year,
            status=season.status.value,
            active=season.active,
            modality_ids=[
                season_modality.modality_id for season_modality in season_modalities
            ],
            registration_start_date=season.registration_start_date,
            registration_end_date=season.registration_end_date,
            registration_opened_at=season.registration_opened_at,
            registration_closed_at=season.registration_closed_at,
            total_teams_created=total_teams_created,
            total_teams_submitted=total_teams_submitted,
            total_teams_approved=total_teams_approved,
            available_actions=available_actions,
        )
