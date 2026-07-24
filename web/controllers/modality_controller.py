from typing import Annotated

from fastapi import APIRouter, status
from fastapi.params import Depends

from core.business.modality.create_modality_port import CreateModalityPort
from core.context import Context
from domain.enums.score_type import ScoreType
from domain.modality.modality import Modality
from domain.modality.modality_configuration import ModalityConfiguration
from domain.modality.volleyball_modality_configuration import (
    VolleyballModalityConfiguration,
)
from web.commons.api_response import ApiResponse
from web.dependencies import require_monitor
from web.dependencies.business.modality_dependencies import get_create_modality_port
from web.dependencies.mapper_dependencies import get_modality_model_mapper
from web.mappers.modality_model_mapper import ModalityModelMapper
from web.models.request.modality_create_request import ModalityCreateRequest
from web.models.response.modality_create_response import ModalityCreateResponse

router = APIRouter(prefix="/api/modality", tags=["modality"])


@router.post(
    "/",
    response_model=ApiResponse[ModalityCreateResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_monitor)]
)
async def create_modality(
    request: ModalityCreateRequest,
    create_modality_port: Annotated[
        CreateModalityPort, Depends(get_create_modality_port)
    ],
    mapper: Annotated[ModalityModelMapper, Depends(get_modality_model_mapper)],
):
    modality_domain = Modality(
        name=request.name,
        min_members=request.min_members,
        max_members=request.max_members,
    )
    configuration_domain = ModalityConfiguration(
        num_periods=request.num_periods,
        period_durations_minutes=request.period_durations_minutes,
        score_type=request.score_type,
        has_third_place_match=request.has_third_place_match,
        metadata=request.metadata,
    )

    context = Context(data=modality_domain)
    context.put_property("modality_configuration", configuration_domain)

    if request.score_type == ScoreType.SETS:
        context.put_property(
            "volleyball_configuration",
            VolleyballModalityConfiguration(
                points_per_set=request.points_per_set,
                final_set_points=request.final_set_points,
                sets_to_win=request.sets_to_win,
            ),
        )

    saved_modality = await create_modality_port.execute(context)
    saved_configuration = context.get_property(
        "modality_configuration", ModalityConfiguration
    )
    saved_volleyball_configuration = context.get_property(
        "volleyball_configuration", VolleyballModalityConfiguration
    )

    response_data = mapper.to_create_response(
        saved_modality, saved_configuration, saved_volleyball_configuration
    )

    return ApiResponse(
        data=response_data, message="Modalidade cadastrada com sucesso!"
    )
