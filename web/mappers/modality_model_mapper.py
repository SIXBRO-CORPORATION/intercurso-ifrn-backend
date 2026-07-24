from typing import Optional

from domain.modality.modality import Modality
from domain.modality.modality_configuration import ModalityConfiguration
from domain.modality.volleyball_modality_configuration import (
    VolleyballModalityConfiguration,
)
from web.models.response.modality_create_response import (
    ModalityConfigurationResponse,
    ModalityCreateResponse,
)


class ModalityModelMapper:
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
            has_third_place_match=configuration.has_third_place_match,
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
