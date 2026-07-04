from typing import Annotated

from fastapi import APIRouter, status
from fastapi.params import Depends

from core.business.modality.create_modality_port import CreateModalityPort
from core.context import Context
from domain.modality import Modality
from domain.user import User
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

    context = Context(data=modality_domain)

    saved_modality = await create_modality_port.execute(context)

    response_data = mapper.to_create_response(saved_modality)

    return ApiResponse(
        data=response_data, message="Modalidade cadastrada com sucesso!"
    )
