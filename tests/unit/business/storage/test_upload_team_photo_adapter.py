from unittest.mock import AsyncMock, MagicMock

import pytest

from business.storage.upload_team_photo_adapter import UploadTeamPhotoAdapter
from core.context import Context
from domain.exceptions.business_exception import BusinessException
from domain.storage.uploaded_photo import UploadedPhoto


def make_adapter():
    file_storage = MagicMock()
    file_storage.upload = AsyncMock(side_effect=lambda **kwargs: kwargs["object_key"])
    file_storage.generate_presigned_url = MagicMock(
        return_value="https://account.r2.cloudflarestorage.com/bucket/teams/x.png?X-Amz-Signature=abc"
    )
    adapter = UploadTeamPhotoAdapter(file_storage)
    return adapter, file_storage


def make_context(file_bytes=b"fake-image-bytes", content_type="image/png"):
    context = Context()
    if file_bytes is not None:
        context.put_property("file_bytes", file_bytes)
    if content_type is not None:
        context.put_property("content_type", content_type)
    return context


@pytest.mark.unit
class TestUploadTeamPhotoAdapter:
    async def test_uploads_png_and_returns_object_key_and_preview_url(self):
        adapter, file_storage = make_adapter()

        context = make_context(content_type="image/png")
        result = await adapter.execute(context)

        assert isinstance(result, UploadedPhoto)
        assert result.object_key.startswith("teams/")
        assert result.object_key.endswith(".png")
        assert result.preview_url.startswith("https://")

        file_storage.upload.assert_awaited_once()
        _, kwargs = file_storage.upload.call_args
        assert kwargs["content_type"] == "image/png"
        assert kwargs["object_key"] == result.object_key

        file_storage.generate_presigned_url.assert_called_once_with(result.object_key)

    async def test_uploads_jpeg_with_jpg_extension(self):
        adapter, file_storage = make_adapter()

        context = make_context(content_type="image/jpeg")
        result = await adapter.execute(context)

        assert result.object_key.endswith(".jpg")

    async def test_rejects_missing_file(self):
        adapter, file_storage = make_adapter()
        context = make_context(file_bytes=b"", content_type="image/png")

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        file_storage.upload.assert_not_awaited()

    async def test_rejects_invalid_content_type(self):
        adapter, file_storage = make_adapter()
        context = make_context(content_type="application/pdf")

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        file_storage.upload.assert_not_awaited()

    async def test_rejects_file_above_size_limit(self):
        adapter, file_storage = make_adapter()
        oversized_bytes = b"0" * (5 * 1024 * 1024 + 1)
        context = make_context(file_bytes=oversized_bytes, content_type="image/png")

        with pytest.raises(BusinessException):
            await adapter.execute(context)

        file_storage.upload.assert_not_awaited()
