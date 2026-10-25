from typing import Annotated
from typing import List
from uuid import UUID

from fastapi import APIRouter, Query, status
from fastapi.params import Depends

from core.business.modality.create_modality_port import CreateModalityPort
from core.business.modality.list_all_modalities_port import ListAllModalitiesPort
from core.business.modality.list_modalities_port import ListModalitiesPort
from core.business.modality.update_modality_active_port import (
    UpdateModalityActivePort,
)
from core.context import Context
from domain.enums.score_type import ScoreType
from domain.modality.modality import Modality
from domain.modality.modality_configuration import ModalityConfiguration
from domain.modality.volleyball_modality_configuration import VolleyballModalityConfiguration
from domain.user.user import User
from web.commons.api_response import ApiResponse
from web.dependencies import require_monitor
from web.dependencies.business.modality_dependencies import (
    get_create_modality_port,
    get_list_all_modalities_port,
    get_list_modalities_port,
    get_update_modality_active_port,
)
from web.dependencies.mapper_dependencies import get_modality_model_mapper
from web.mappers.modality_model_mapper import ModalityModelMapper
from web.models.request.modality.modality_create_request import ModalityCreateRequest
from web.models.request.modality.modality_update_active_request import (
    ModalityUpdateActiveRequest,
)
from web.models.response.modality.modality_create_response import ModalityCreateResponse
from web.models.response.modality.modality_status_response import (
    ModalityStatusResponse,
)
from web.models.response.modality.modality_summary_response import (
    ModalitySummaryResponse,
)

router = APIRouter(prefix="/api/modality", tags=["modality"])


@router.get("/", response_model=ApiResponse[List[ModalitySummaryResponse]])
async def list_modalities(
    list_modalities_port: Annotated[
        ListModalitiesPort, Depends(get_list_modalities_port)
    ],
    mapper: Annotated[ModalityModelMapper, Depends(get_modality_model_mapper)],
    season_id: Annotated[
        UUID | None, Query(description="Restringe às modalidades da temporada")
    ] = None,
):
    context = Context()
    if season_id is not None:
        context.put_property("season_id", season_id)
    modalities = await list_modalities_port.execute(context)
    configurations = context.get_property("modality_configurations", dict) or {}
    volleyball_configurations = (
        context.get_property("modality_volleyball_configurations", dict) or {}
    )
    return ApiResponse(
        data=mapper.to_summary_responses(
            modalities, configurations, volleyball_configurations
        )
    )


@router.get(
    "/admin",
    response_model=ApiResponse[List[ModalitySummaryResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_all_modalities(
    list_all_modalities_port: Annotated[
        ListAllModalitiesPort, Depends(get_list_all_modalities_port)
    ],
    mapper: Annotated[ModalityModelMapper, Depends(get_modality_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    modalities = await list_all_modalities_port.execute(context)
    configurations = context.get_property("modality_configurations", dict) or {}
    volleyball_configurations = (
        context.get_property("modality_volleyball_configurations", dict) or {}
    )
    return ApiResponse(
        data=mapper.to_summary_responses(
            modalities, configurations, volleyball_configurations
        )
    )


@router.post(
    "/",
    response_model=ApiResponse[ModalityCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_modality(
    request: ModalityCreateRequest,
    create_modality_port: Annotated[
        CreateModalityPort, Depends(get_create_modality_port)
    ],
    mapper: Annotated[ModalityModelMapper, Depends(get_modality_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    modality_domain = Modality(
        name=request.name,
        min_members=request.min_members,
        max_members=request.max_members,
        gender_mode=request.gender_mode,
        min_male_members=request.min_male_members,
        min_female_members=request.min_female_members,
    )
    configuration_domain = ModalityConfiguration(
        num_periods=request.num_periods,
        period_durations_minutes=request.period_durations_minutes,
        score_type=request.score_type,
        metadata=request.metadata,
    )

    context = Context(data=modality_domain)
    context.put_property("modality_configuration", configuration_domain)
    context.put_property("created_by", current_user.id)

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


@router.patch(
    "/{modality_id}/",
    response_model=ApiResponse[ModalityStatusResponse],
    status_code=status.HTTP_200_OK,
)
async def update_modality_active(
    modality_id: UUID,
    request: ModalityUpdateActiveRequest,
    update_modality_active_port: Annotated[
        UpdateModalityActivePort, Depends(get_update_modality_active_port)
    ],
    mapper: Annotated[ModalityModelMapper, Depends(get_modality_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("modality_id", modality_id)
    context.put_property("active", request.active)
    context.put_property("updated_by", current_user.id)

    updated_modality = await update_modality_active_port.execute(context)

    message = (
        "Modalidade ativada com sucesso!"
        if updated_modality.active
        else "Modalidade desativada com sucesso!"
    )
    response_data = mapper.to_status_response(updated_modality, message)

    return ApiResponse(data=response_data, message=message)
