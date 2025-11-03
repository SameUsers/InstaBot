import pytest
import io
from source.services.storage import minio_client
from source.tests.fixtures.sample_data import SAMPLE_BASE64_IMAGE


@pytest.mark.integration
class TestMinioStorage:
    
    @pytest.mark.asyncio
    async def test_upload_from_base64_success(self):
        image_url = await minio_client.upload_from_base64(SAMPLE_BASE64_IMAGE)
        
        assert image_url is not None
        assert isinstance(image_url, str)
        assert "images/" in image_url or minio_client.bucket_name in image_url
    
    @pytest.mark.asyncio
    async def test_upload_from_base64_format(self):
        image_url = await minio_client.upload_from_base64(SAMPLE_BASE64_IMAGE)
        
        assert image_url.endswith((".jpeg", ".jpg", ".png", ".gif"))
    
    @pytest.mark.asyncio
    async def test_multiple_uploads_unique_names(self):
        url1 = await minio_client.upload_from_base64(SAMPLE_BASE64_IMAGE)
        url2 = await minio_client.upload_from_base64(SAMPLE_BASE64_IMAGE)
        
        assert url1 != url2
    
    @pytest.mark.asyncio
    async def test_upload_empty_base64_raises_error(self):
        with pytest.raises(Exception):
            await minio_client.upload_from_base64("")
    
    @pytest.mark.asyncio
    async def test_upload_invalid_base64_raises_error(self):
        with pytest.raises(Exception):
            await minio_client.upload_from_base64("not_a_valid_base64_string!!!")

