from functools import lru_cache

from core.business.storage.upload_team_photo_port import UploadTeamPhotoPort
from core.storage.file_storage_port import FileStoragePort
from business.storage.upload_team_photo_adapter import UploadTeamPhotoAdapter
from storage.adapters.r2_storage_adapter import R2StorageAdapter


@lru_cache
def get_file_storage() -> FileStoragePort:
    return R2StorageAdapter()


def get_upload_team_photo_port() -> UploadTeamPhotoPort:
    return UploadTeamPhotoAdapter(get_file_storage())
