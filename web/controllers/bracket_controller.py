from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.params import Depends

from core.business.bracket.create_bracket_port import CreateBracketPort
from core.business.bracket.delete_match_port import DeleteMatchPort
from core.business.bracket.get_bracket_config_suggestion_port import (
    GetBracketConfigSuggestionPort,
)
from core.business.bracket.resort_bracket_port import ResortBracketPort
from core.business.bracket.update_match_port import UpdateMatchPort
from core.context import Context
from domain.bracket import Bracket
from domain.enums.modality_format import ModalityFormat
from domain.exceptions.business_exception import BusinessException
from domain.user import User
from web.commons.api_response import ApiResponse
from web.dependencies import (
    get_bracket_config_suggestion_port,
    get_bracket_model_mapper,
    get_create_bracket_port,
    get_delete_match_port,
    get_resort_bracket_port,
    get_update_match_port,
    require_monitor,
)
from web.mappers.bracket_model_mapper import BracketModelMapper
from web.models.request.bracket_create_request import BracketCreateRequest
from web.models.request.match_update_request import MatchUpdateRequest
from web.models.response.bracket_config_suggestion_response import (
    BracketConfigSuggestionResponse,
)
from web.models.response.bracket_response import BracketResponse
from web.models.response.match_response import MatchResponse

router = APIRouter(prefix="/api/bracket", tags=["bracket"])

# TODO (débito técnico Fase 4): endpoints de consulta ainda não implementados —
# GET /api/bracket/{bracket_id} (detalhe com grupos/partidas),
# GET /api/bracket/season/{season_id} (lista de brackets da temporada),
# GET /api/bracket/{bracket_id}/matches (lista de partidas do chaveamento).
# Ficam para uma rodada futura focada em endpoints de leitura para o front,
# conforme combinado: nesta fase o foco foi write (criar/editar/deletar).


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
        raise BusinessException(f"Formato inválido! Valores aceitos: {valid}")
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
