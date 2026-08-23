from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Query, status
from fastapi.params import Depends

from core.business.season.close_registration_port import CloseRegistrationPort
from core.business.season.create_season_port import CreateSeasonPort
from core.business.season.finish_season_port import FinishSeasonPort
from core.business.season.get_active_season_port import GetActiveSeasonPort
from core.business.season.get_season_details_port import GetSeasonDetailsPort
from core.business.season.list_seasons_port import ListSeasonsPort
from core.business.season.manage_season_port import ManageSeasonPort
from core.business.season.reopen_registration_port import ReopenRegistrationPort
from core.context import Context
from domain.enums.season_status import SeasonStatus
from domain.season.season import Season
from domain.user.user import User
from web.commons.api_response import ApiResponse
from web.dependencies import require_authenticated_user, require_monitor
from web.dependencies.business.season_dependencies import (
    get_active_season_port,
    get_close_registration_port,
    get_create_season_port,
    get_finish_season_port,
    get_list_seasons_port,
    get_manage_season_port,
    get_reopen_registration_port,
    get_season_details_port,
)
from web.dependencies.mapper_dependencies import get_season_model_mapper
from web.mappers.season_model_mapper import SeasonModelMapper
from web.models.request.season.season_create_request import SeasonCreateRequest
from web.models.request.season.season_edit_dates_request import SeasonEditDatesRequest
from web.models.request.season.season_finish_request import SeasonFinishRequest
from web.models.request.season.season_reopen_request import SeasonReopenRequest
from web.models.response.season.season_create_response import SeasonCreateResponse
from web.models.response.season.season_details_response import SeasonDetailsResponse
from web.models.response.season.season_status_response import SeasonStatusResponse
from web.models.response.season.season_summary_response import SeasonSummaryResponse

router = APIRouter(prefix="/api/season", tags=["season"])


@router.post(
    "/",
    response_model=ApiResponse[SeasonCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_season(
    request: SeasonCreateRequest,
    create_season_port: Annotated[CreateSeasonPort, Depends(get_create_season_port)],
    mapper: Annotated[SeasonModelMapper, Depends(get_season_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    season_domain = Season(
        name=request.name,
        year=request.year,
        registration_start_date=request.registration_start_date,
        registration_end_date=request.registration_end_date,
        rules_document=request.rules_document,
    )

    context = Context(data=season_domain)
    context.put_property("modality_ids", request.modality_ids)
    context.put_property("open_immediately", request.open_immediately)
    context.put_property("created_by", current_user.id)

    saved_season = await create_season_port.execute(context)
    season_modalities = context.get_property("season_modalities", list) or []

    response_data = mapper.to_create_response(saved_season, season_modalities)

    return ApiResponse(data=response_data, message="Temporada criada com sucesso!")


@router.get(
    "/",
    response_model=ApiResponse[List[SeasonSummaryResponse]],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_monitor)],
)
async def list_seasons(
    list_seasons_port: Annotated[ListSeasonsPort, Depends(get_list_seasons_port)],
    mapper: Annotated[SeasonModelMapper, Depends(get_season_model_mapper)],
    status_filter: Optional[SeasonStatus] = Query(default=None, alias="status"),
    year: Optional[int] = Query(default=None),
):
    context = Context()
    if status_filter is not None:
        context.put_property("status", status_filter)
    if year is not None:
        context.put_property("year", year)

    seasons = await list_seasons_port.execute(context)

    response_data = [mapper.to_summary_response(season) for season in seasons]

    return ApiResponse(data=response_data)


@router.get(
    "/active",
    response_model=ApiResponse[SeasonSummaryResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_authenticated_user)],
)
async def get_active_season(
    active_season_port: Annotated[
        GetActiveSeasonPort, Depends(get_active_season_port)
    ],
    mapper: Annotated[SeasonModelMapper, Depends(get_season_model_mapper)],
):
    context = Context()

    season = await active_season_port.execute(context)

    response_data = mapper.to_summary_response(season)

    return ApiResponse(data=response_data)


@router.get(
    "/{season_id}",
    response_model=ApiResponse[SeasonDetailsResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_monitor)]
)
async def get_season_details(
    season_id: UUID,
    season_details_port: Annotated[
        GetSeasonDetailsPort, Depends(get_season_details_port)
    ],
    mapper: Annotated[SeasonModelMapper, Depends(get_season_model_mapper)],
):
    context = Context()
    context.put_property("season_id", season_id)

    season = await season_details_port.execute(context)
    season_modalities = context.get_property("season_modalities", list) or []
    total_created = context.get_property("total_teams_created", int) or 0
    total_submitted = context.get_property("total_teams_submitted", int) or 0
    total_approved = context.get_property("total_teams_approved", int) or 0
    available_actions = context.get_property("available_actions", list) or []

    response_data = mapper.to_details_response(
        season,
        season_modalities,
        total_created,
        total_submitted,
        total_approved,
        available_actions,
    )

    return ApiResponse(data=response_data)


@router.patch(
    "/{season_id}/dates",
    response_model=ApiResponse[SeasonStatusResponse],
    status_code=status.HTTP_200_OK,
)
async def edit_season_dates(
    season_id: UUID,
    request: SeasonEditDatesRequest,
    manage_season_port: Annotated[ManageSeasonPort, Depends(get_manage_season_port)],
    mapper: Annotated[SeasonModelMapper, Depends(get_season_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("season_id", season_id)
    context.put_property(
        "new_registration_start_date", request.new_registration_start_date
    )
    context.put_property(
        "new_registration_end_date", request.new_registration_end_date
    )
    context.put_property("reason", request.reason)
    context.put_property("updated_by", current_user.id)

    updated_season = await manage_season_port.execute(context)

    response_data = mapper.to_status_response(
        updated_season, "Datas da temporada atualizadas com sucesso!"
    )

    return ApiResponse(data=response_data, message=response_data.message)


@router.post(
    "/{season_id}/close-registration",
    response_model=ApiResponse[SeasonStatusResponse],
    status_code=status.HTTP_200_OK,
)
async def close_season_registration(
    season_id: UUID,
    close_registration_port: Annotated[
        CloseRegistrationPort, Depends(get_close_registration_port)
    ],
    mapper: Annotated[SeasonModelMapper, Depends(get_season_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("season_id", season_id)
    context.put_property("closed_by", current_user.id)

    updated_season = await close_registration_port.execute(context)

    response_data = mapper.to_status_response(
        updated_season, "Inscrições encerradas antecipadamente com sucesso!"
    )

    return ApiResponse(data=response_data, message=response_data.message)


@router.post(
    "/{season_id}/reopen-registration",
    response_model=ApiResponse[SeasonStatusResponse],
    status_code=status.HTTP_200_OK,
)
async def reopen_season_registration(
    season_id: UUID,
    request: SeasonReopenRequest,
    reopen_registration_port: Annotated[
        ReopenRegistrationPort, Depends(get_reopen_registration_port)
    ],
    mapper: Annotated[SeasonModelMapper, Depends(get_season_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("season_id", season_id)
    context.put_property(
        "new_registration_end_date", request.new_registration_end_date
    )
    context.put_property("reopened_by", current_user.id)

    updated_season = await reopen_registration_port.execute(context)

    response_data = mapper.to_status_response(
        updated_season, "Inscrições reabertas com sucesso!"
    )

    return ApiResponse(data=response_data, message=response_data.message)


@router.post(
    "/{season_id}/finish",
    response_model=ApiResponse[SeasonStatusResponse],
    status_code=status.HTTP_200_OK,
)
async def finish_season(
    season_id: UUID,
    request: SeasonFinishRequest,
    finish_season_port: Annotated[FinishSeasonPort, Depends(get_finish_season_port)],
    mapper: Annotated[SeasonModelMapper, Depends(get_season_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("season_id", season_id)
    context.put_property("confirmation_name", request.confirmation_name)
    context.put_property("finished_by", current_user.id)

    updated_season = await finish_season_port.execute(context)

    response_data = mapper.to_status_response(
        updated_season, "Temporada finalizada com sucesso!"
    )

    return ApiResponse(data=response_data, message=response_data.message)
