import asyncio
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from core.storage.file_storage_port import FileStoragePort
from domain.exceptions.business_exception import BusinessException
from storage.config import storage_settings


class R2StorageAdapter(FileStoragePort):

    def __init__(self):
        self.bucket_name = storage_settings.r2_bucket_name
        self.default_expires_in = storage_settings.r2_presigned_url_expires_seconds

        endpoint_url = storage_settings.r2_endpoint_url or (
            f"https://{storage_settings.r2_account_id}.r2.cloudflarestorage.com"
        )

        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=storage_settings.r2_access_key_id,
            aws_secret_access_key=storage_settings.r2_secret_access_key,
            config=Config(signature_version="s3v4", region_name="auto"),
        )

    def _put_object(self, file_bytes: bytes, object_key: str, content_type: str) -> None:
        self._client.put_object(
            Bucket=self.bucket_name,
            Key=object_key,
            Body=file_bytes,
            ContentType=content_type,
        )

    def _delete_object(self, object_key: str) -> None:
        self._client.delete_object(Bucket=self.bucket_name, Key=object_key)

    async def upload(self, file_bytes: bytes, object_key: str, content_type: str) -> str:
        try:
            await asyncio.to_thread(
                self._put_object, file_bytes, object_key, content_type
            )
        except (BotoCoreError, ClientError) as e:
            raise BusinessException(f"Erro ao enviar arquivo para o storage: {str(e)}")

        return object_key

    def generate_presigned_url(
        self, object_key: str, expires_in: Optional[int] = None
    ) -> str:
        try:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=expires_in or self.default_expires_in,
            )
        except (BotoCoreError, ClientError) as e:
            raise BusinessException(
                f"Erro ao gerar URL assinada do storage: {str(e)}"
            )

    async def delete(self, object_key: str) -> None:
        try:
            await asyncio.to_thread(self._delete_object, object_key)
        except (BotoCoreError, ClientError) as e:
            raise BusinessException(f"Erro ao remover arquivo do storage: {str(e)}")
