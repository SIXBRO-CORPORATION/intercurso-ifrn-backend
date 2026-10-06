from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status

from core.business.storage.upload_team_photo_port import UploadTeamPhotoPort
from core.context import Context
from domain.exceptions.business_exception import BusinessException
from domain.storage.uploaded_photo import UploadedPhoto
from domain.user.user import User
from web.commons.api_response import ApiResponse
from web.dependencies import get_upload_team_photo_port, require_authenticated_user
from web.models.response.storage.upload_response import UploadResponse

router = APIRouter(prefix="/api/storage", tags=["storage"])


@router.post(
    "/team-photo",
    response_model=ApiResponse[UploadResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_team_photo(
    upload_port: Annotated[UploadTeamPhotoPort, Depends(get_upload_team_photo_port)],
    file: UploadFile = File(...),
    current_user: User = Depends(require_authenticated_user),
):

    if file.content_type is None:
        raise BusinessException("Não foi possível identificar o tipo do arquivo enviado")

    file_bytes = await file.read()

    context = Context()
    context.put_property("file_bytes", file_bytes)
    context.put_property("content_type", file.content_type)
    context.put_property("uploaded_by_user_id", current_user.id)

    uploaded_photo: UploadedPhoto = await upload_port.execute(context)

    return ApiResponse(
        data=UploadResponse(
            object_key=uploaded_photo.object_key,
            preview_url=uploaded_photo.preview_url,
        ),
        message="Foto enviada com sucesso!",
    )
