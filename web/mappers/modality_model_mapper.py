from typing import Dict, List, Optional
from uuid import UUID

from domain.modality.modality import Modality
from domain.modality.modality_configuration import ModalityConfiguration
from domain.modality.volleyball_modality_configuration import VolleyballModalityConfiguration
from web.models.response.modality.modality_summary_response import (
    ModalitySummaryResponse,
)
from web.models.response.modality.modality_create_response import (
    ModalityConfigurationResponse,
    ModalityCreateResponse,
)
from web.models.response.modality.modality_status_response import (
    ModalityStatusResponse,
)


class ModalityModelMapper:
    def to_summary_responses(
        self,
        modalities: List[Modality],
        configurations: Optional[Dict[UUID, ModalityConfiguration]] = None,
        volleyball_configurations: Optional[
            Dict[UUID, VolleyballModalityConfiguration]
        ] = None,
    ) -> List[ModalitySummaryResponse]:
        configurations = configurations or {}
        volleyball_configurations = volleyball_configurations or {}
        return [
            ModalitySummaryResponse(
                modality_id=m.id,
                name=m.name,
                min_members=m.min_members,
                max_members=m.max_members,
                gender_mode=m.gender_mode,
                min_male_members=m.min_male_members,
                min_female_members=m.min_female_members,
                active=m.active,
                num_periods=self._configuration_field(configurations, m.id, "num_periods"),
                period_durations_minutes=self._configuration_field(
                    configurations, m.id, "period_durations_minutes"
                ),
                score_type=(
                    configurations[m.id].score_type.value
                    if m.id in configurations and configurations[m.id].score_type
                    else None
                ),
                points_per_set=self._configuration_field(
                    volleyball_configurations, m.id, "points_per_set"
                ),
                final_set_points=self._configuration_field(
                    volleyball_configurations, m.id, "final_set_points"
                ),
                sets_to_win=self._configuration_field(
                    volleyball_configurations, m.id, "sets_to_win"
                ),
            )
            for m in modalities
        ]

    def to_status_response(
        self, modality: Modality, message: str
    ) -> ModalityStatusResponse:
        return ModalityStatusResponse(
            modality_id=modality.id,
            name=modality.name,
            active=modality.active,
            message=message,
        )

    def to_create_response(
        self,
        modality: Modality,
        configuration: Optional[ModalityConfiguration] = None,
        volleyball_configuration: Optional[VolleyballModalityConfiguration] = None,
    ) -> ModalityCreateResponse:
        return ModalityCreateResponse(
            modality_id=modality.id,
            name=modality.name,
            min_members=modality.min_members,
            max_members=modality.max_members,
            gender_mode=modality.gender_mode,
            min_male_members=modality.min_male_members,
            min_female_members=modality.min_female_members,
            active=modality.active,
            configuration=self._to_configuration_response(
                configuration, volleyball_configuration
            ),
            message="Modalidade cadastrada com sucesso!",
        )

    def _to_configuration_response(
        self,
        configuration: Optional[ModalityConfiguration],
        volleyball_configuration: Optional[VolleyballModalityConfiguration] = None,
    ) -> Optional[ModalityConfigurationResponse]:
        if configuration is None:
            return None

        return ModalityConfigurationResponse(
            num_periods=configuration.num_periods,
            period_durations_minutes=configuration.period_durations_minutes,
            score_type=(
                configuration.score_type.value if configuration.score_type else None
            ),
            metadata=configuration.metadata,
            points_per_set=(
                volleyball_configuration.points_per_set
                if volleyball_configuration
                else None
            ),
            final_set_points=(
                volleyball_configuration.final_set_points
                if volleyball_configuration
                else None
            ),
            sets_to_win=(
                volleyball_configuration.sets_to_win
                if volleyball_configuration
                else None
            ),
        )

    @staticmethod
    def _configuration_field(
        configurations: Dict[UUID, ModalityConfiguration],
        modality_id: Optional[UUID],
        field: str,
    ):
        configuration = configurations.get(modality_id)
        return getattr(configuration, field) if configuration is not None else None
