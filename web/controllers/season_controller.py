from typing import Annotated

from fastapi import APIRouter, status
from fastapi.params import Depends

from core.business.season.create_season_port import CreateSeasonPort
from core.context import Context
from domain.season import Season
from domain.user import User
from web.commons.api_response import ApiResponse
from web.dependencies import require_authenticated_user
from web.dependencies.business.season_dependencies import get_create_season_port
from web.mappers.season_model_mapper import SeasonModelMapper
from web.models.request.season_create_request import SeasonCreateRequest
from web.models.response.season_create_response import SeasonCreateResponse

router = APIRouter(prefix="/api/season", tags=["season"])


@router.post(
    "/",
    response_model=ApiResponse[SeasonCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_season(
    request: SeasonCreateRequest,
    create_season_port: Annotated[CreateSeasonPort, Depends(get_create_season_port)],
    current_user: User = Depends(require_authenticated_user),
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

    mapper = SeasonModelMapper()
    response_data = mapper.to_create_response(saved_season, season_modalities)

    return ApiResponse(data=response_data, message="Temporada criada com sucesso!")
