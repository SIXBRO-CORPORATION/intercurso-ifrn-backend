from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.params import Depends

from core.business.bracket.create_bracket_port import CreateBracketPort
from core.business.bracket.delete_match_port import DeleteMatchPort
from core.business.bracket.get_bracket_config_suggestion_port import (
    GetBracketConfigSuggestionPort,
)
from core.business.bracket.get_bracket_details_port import GetBracketDetailsPort
from core.business.bracket.list_bracket_matches_port import ListBracketMatchesPort
from core.business.bracket.list_brackets_by_season_port import ListBracketsBySeasonPort
from core.business.bracket.resort_bracket_port import ResortBracketPort
from core.business.bracket.update_match_port import UpdateMatchPort
from core.context import Context
from domain.bracket.bracket import Bracket
from domain.enums.modality_format import ModalityFormat
from domain.exceptions.business_exception import BusinessException
from domain.user.user import User
from web.commons.api_response import ApiResponse
from web.dependencies import (
    get_bracket_config_suggestion_port,
    get_bracket_details_port,
    get_bracket_model_mapper,
    get_create_bracket_port,
    get_delete_match_port,
    get_list_bracket_matches_port,
    get_list_brackets_by_season_port,
    get_resort_bracket_port,
    get_update_match_port,
    require_monitor,
)
from web.mappers.bracket_model_mapper import BracketModelMapper
from web.models.request.bracket.bracket_create_request import BracketCreateRequest
from web.models.request.match.match_update_request import MatchUpdateRequest
from web.models.response.bracket.bracket_config_suggestion_response import (
    BracketConfigSuggestionResponse,
)
from web.models.response.bracket.bracket_detail_response import BracketDetailResponse
from web.models.response.bracket.bracket_match_response import BracketMatchResponse
from web.models.response.bracket.bracket_response import BracketResponse
from web.models.response.bracket.bracket_summary_response import BracketSummaryResponse
from web.models.response.match.match_response import MatchResponse

router = APIRouter(prefix="/api/bracket", tags=["bracket"])


@router.get(
    "/preview",
    response_model=ApiResponse[BracketConfigSuggestionResponse],
    status_code=status.HTTP_200_OK,
)
async def preview_bracket_config(
    modality_id: UUID,
    format: str,
    suggestion_port: Annotated[
        GetBracketConfigSuggestionPort, Depends(get_bracket_config_suggestion_port)
    ],
    mapper: Annotated[BracketModelMapper, Depends(get_bracket_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    normalized_format = format.strip().upper()
    if normalized_format not in ModalityFormat.__members__:
        valid = ", ".join(ModalityFormat.__members__.keys())
        raise BusinessException(f"Formato inválido. Valores aceitos: {valid}")
    modality_format = ModalityFormat[normalized_format]

    context = Context()
    context.put_property("modality_id", modality_id)
    context.put_property("format", modality_format)

    suggested_configuration = await suggestion_port.execute(context)

    team_count = context.get_property("team_count", int) or 0
    byes_estimated = context.get_property("byes_estimated", int) or 0

    response_data = mapper.to_config_suggestion_response(
        modality_id, modality_format, team_count, byes_estimated, suggested_configuration
    )

    return ApiResponse(data=response_data)


@router.get(
    "/season/{season_id}",
    response_model=ApiResponse[List[BracketSummaryResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_brackets_by_season(
    season_id: UUID,
    list_port: Annotated[
        ListBracketsBySeasonPort, Depends(get_list_brackets_by_season_port)
    ],
    mapper: Annotated[BracketModelMapper, Depends(get_bracket_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("season_id", season_id)

    brackets: List[Bracket] = await list_port.execute(context)

    stats = context.get_property("bracket_stats", dict) or {}
    modality_names = context.get_property("modality_names", dict) or {}

    response_data = [
        mapper.to_bracket_summary_response(
            bracket,
            modality_names.get(bracket.modality_id),
            stats.get(bracket.id, {}),
        )
        for bracket in brackets
    ]

    return ApiResponse(data=response_data)


@router.get(
    "/{bracket_id}",
    response_model=ApiResponse[BracketDetailResponse],
    status_code=status.HTTP_200_OK,
)
async def get_bracket_details(
    bracket_id: UUID,
    details_port: Annotated[GetBracketDetailsPort, Depends(get_bracket_details_port)],
    mapper: Annotated[BracketModelMapper, Depends(get_bracket_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("bracket_id", bracket_id)

    bracket = await details_port.execute(context)

    response_data = mapper.to_bracket_detail_response(
        bracket,
        modality_name=context.get_property("modality_name", str),
        stats=context.get_property("bracket_stats", dict) or {},
        groups=context.get_property("bracket_groups", list) or [],
        matches=context.get_property("bracket_matches", list) or [],
        team_names=context.get_property("team_names", dict) or {},
    )

    return ApiResponse(data=response_data)


@router.get(
    "/{bracket_id}/matches",
    response_model=ApiResponse[List[BracketMatchResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_bracket_matches(
    bracket_id: UUID,
    matches_port: Annotated[
        ListBracketMatchesPort, Depends(get_list_bracket_matches_port)
    ],
    mapper: Annotated[BracketModelMapper, Depends(get_bracket_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("bracket_id", bracket_id)

    matches = await matches_port.execute(context)

    team_names = context.get_property("team_names", dict) or {}
    group_names = context.get_property("group_names", dict) or {}

    response_data = [
        mapper.to_bracket_match_response(match, team_names, group_names)
        for match in matches
    ]

    return ApiResponse(data=response_data)


@router.post(
    "/",
    response_model=ApiResponse[BracketResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_bracket(
    request: BracketCreateRequest,
    create_bracket_port: Annotated[CreateBracketPort, Depends(get_create_bracket_port)],
    mapper: Annotated[BracketModelMapper, Depends(get_bracket_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    bracket_domain = Bracket(
        modality_id=request.modality_id, format=ModalityFormat[request.format]
    )

    context = Context(data=bracket_domain)
    context.put_property("created_by", current_user.id)
    context.put_property("configuration", request.configuration)

    saved_bracket = await create_bracket_port.execute(context)

    teams_count = context.get_property("teams_count", int) or 0
    groups_created = context.get_property("groups_created", int) or 0
    matches_created = context.get_property("matches_created", int) or 0
    byes_created = context.get_property("byes_created", int) or 0
    season_transitioned = (
        context.get_property("season_transitioned_to_in_progress", bool) or False
    )

    response_data = mapper.to_bracket_response(
        saved_bracket,
        teams_count,
        groups_created,
        matches_created,
        byes_created,
        season_transitioned,
    )

    message = "Chaveamento criado com sucesso!"
    if season_transitioned:
        message = "Chaveamento criado com sucesso! Fase de jogos iniciada."

    return ApiResponse(data=response_data, message=message)


@router.post(
    "/{bracket_id}/resort",
    response_model=ApiResponse[BracketResponse],
    status_code=status.HTTP_200_OK,
)
async def resort_bracket(
    bracket_id: UUID,
    resort_bracket_port: Annotated[ResortBracketPort, Depends(get_resort_bracket_port)],
    mapper: Annotated[BracketModelMapper, Depends(get_bracket_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("bracket_id", bracket_id)
    context.put_property("requested_by", current_user.id)

    saved_bracket = await resort_bracket_port.execute(context)

    teams_count = context.get_property("teams_count", int) or 0
    groups_created = context.get_property("groups_created", int) or 0
    matches_created = context.get_property("matches_created", int) or 0
    byes_created = context.get_property("byes_created", int) or 0

    response_data = mapper.to_bracket_response(
        saved_bracket, teams_count, groups_created, matches_created, byes_created
    )

    return ApiResponse(data=response_data, message="Chaveamento re-sorteado com sucesso!")


@router.patch(
    "/match/{match_id}",
    response_model=ApiResponse[MatchResponse],
    status_code=status.HTTP_200_OK,
)
async def update_match(
    match_id: UUID,
    request: MatchUpdateRequest,
    update_match_port: Annotated[UpdateMatchPort, Depends(get_update_match_port)],
    mapper: Annotated[BracketModelMapper, Depends(get_bracket_model_mapper)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("match_id", match_id)
    context.put_property("scheduled_date", request.scheduled_date)
    context.put_property("team1_id", request.team1_id)
    context.put_property("team2_id", request.team2_id)
    context.put_property("updated_by", current_user.id)

    updated_match = await update_match_port.execute(context)

    response_data = mapper.to_match_response(updated_match)

    return ApiResponse(data=response_data, message="Partida atualizada com sucesso!")


@router.delete(
    "/match/{match_id}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
)
async def delete_match(
    match_id: UUID,
    delete_match_port: Annotated[DeleteMatchPort, Depends(get_delete_match_port)],
    current_user: User = Depends(require_monitor),
):
    context = Context()
    context.put_property("match_id", match_id)
    context.put_property("deleted_by", current_user.id)

    await delete_match_port.execute(context)

    return ApiResponse.success(
        data={"match_id": str(match_id)},
        message="Partida deletada com sucesso!",
    )
