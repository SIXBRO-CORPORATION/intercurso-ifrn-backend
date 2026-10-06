from dataclasses import dataclass


@dataclass
class UploadedPhoto:

    object_key: str
    preview_url: str
