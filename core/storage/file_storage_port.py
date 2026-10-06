from abc import ABC, abstractmethod
from typing import Optional


class FileStoragePort(ABC):

    @abstractmethod
    async def upload(
        self,
        file_bytes: bytes,
        object_key: str,
        content_type: str,
    ) -> str:
        pass

    @abstractmethod
    def generate_presigned_url(
        self, object_key: str, expires_in: Optional[int] = None
    ) -> str:
        pass

    @abstractmethod
    async def delete(self, object_key: str) -> None:
        pass
