from functools import lru_cache

from core.storage.file_storage_port import FileStoragePort
from storage.adapters.r2_storage_adapter import R2StorageAdapter


@lru_cache
def get_file_storage() -> FileStoragePort:
    return R2StorageAdapter()
