import uuid

from core.business.storage.upload_team_photo_port import UploadTeamPhotoPort
from core.context import Context
from core.storage.file_storage_port import FileStoragePort
from domain.exceptions.business_exception import BusinessException
from domain.storage.uploaded_photo import UploadedPhoto

ALLOWED_CONTENT_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
}

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB

TEAM_PHOTO_FOLDER = "teams"


class UploadTeamPhotoAdapter(UploadTeamPhotoPort):
    def __init__(self, file_storage: FileStoragePort):
        self.file_storage = file_storage

    async def execute(self, context: Context) -> UploadedPhoto:
        file_bytes = context.get_property("file_bytes", bytes)
        content_type = context.get_property("content_type", str)

        if not file_bytes:
            raise BusinessException("Arquivo de foto é obrigatório")

        if content_type not in ALLOWED_CONTENT_TYPES:
            raise BusinessException(
                "Formato de imagem inválido. Envie um arquivo PNG, JPG ou JPEG"
            )

        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise BusinessException(
                "Arquivo de foto excede o tamanho máximo permitido de 5MB"
            )

        extension = ALLOWED_CONTENT_TYPES[content_type]
        object_key = f"{TEAM_PHOTO_FOLDER}/{uuid.uuid4()}.{extension}"

        await self.file_storage.upload(
            file_bytes=file_bytes,
            object_key=object_key,
            content_type=content_type,
        )

        preview_url = self.file_storage.generate_presigned_url(object_key)

        return UploadedPhoto(object_key=object_key, preview_url=preview_url)
