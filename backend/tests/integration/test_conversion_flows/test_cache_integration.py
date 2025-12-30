"""
Integration tests for cache service with actual converters and routers.

These tests verify the end-to-end caching flow:
1. First conversion (cache miss) → stores in cache
2. Second identical conversion (cache hit) → returns cached result
3. Different options → cache miss
4. Cache expiration → triggers reconversion
5. Cache statistics accuracy
"""

import pytest
import time
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.services.cache_service import initialize_cache_service, get_cache_service
from app.services.image_converter import ImageConverter
from app.config import settings


@pytest.fixture
def test_client():
    """Create test client for API testing"""
    return TestClient(app)


@pytest.fixture
def sample_image(temp_dir):
    """Create a sample JPG image for testing"""
    image_path = temp_dir / "sample.jpg"
    img = Image.new('RGB', (100, 100), color='red')
    img.save(image_path, 'JPEG')
    return image_path


@pytest.fixture
def cache_enabled(temp_dir):
    """Initialize cache service and enable caching"""
    cache_dir = temp_dir / "cache"
    cache_service = initialize_cache_service(
        cache_dir=cache_dir,
        expiration_hours=1,
        max_size_mb=100
    )

    # Enable caching in settings
    original_cache_enabled = settings.CACHE_ENABLED
    settings.CACHE_ENABLED = True

    # Clear cache before each test
    cache_service.clear_all()

    yield cache_service

    # Restore original setting
    settings.CACHE_ENABLED = original_cache_enabled


class TestCacheIntegrationFlow:
    """Test full end-to-end cache integration with converters"""

    @pytest.mark.asyncio
    async def test_first_conversion_cache_miss(self, sample_image, cache_enabled, temp_dir):
        """Test that first conversion results in cache miss and stores result"""
        converter = ImageConverter()
        session_id = "test_session_1"

        # First conversion should be a cache miss
        output_path = await converter.convert_with_cache(
            input_path=sample_image,
            output_format="png",
            options={"quality": 95},
            session_id=session_id
        )

        assert output_path.exists()
        assert output_path.suffix == ".png"

        # Verify cache statistics
        cache_info = cache_enabled.get_cache_info()
        assert cache_info["stats"]["total_requests"] == 1
        assert cache_info["stats"]["misses"] == 1
        assert cache_info["stats"]["hits"] == 0
        assert cache_info["entry_count"] == 1

    @pytest.mark.asyncio
    async def test_second_conversion_cache_hit(self, sample_image, cache_enabled, temp_dir):
        """Test that second identical conversion results in cache hit"""
        converter = ImageConverter()
        session_id = "test_session_2"

        options = {"quality": 95}

        # First conversion (cache miss)
        output_path_1 = await converter.convert_with_cache(
            input_path=sample_image,
            output_format="png",
            options=options,
            session_id=session_id
        )

        # Second conversion with same parameters (cache hit)
        output_path_2 = await converter.convert_with_cache(
            input_path=sample_image,
            output_format="png",
            options=options,
            session_id=session_id
        )

        assert output_path_1.exists()
        assert output_path_2.exists()

        # Verify cache statistics
        cache_info = cache_enabled.get_cache_info()
        assert cache_info["stats"]["total_requests"] == 2
        assert cache_info["stats"]["misses"] == 1
        assert cache_info["stats"]["hits"] == 1
        assert cache_enabled.get_hit_rate() == 0.5

    @pytest.mark.asyncio
    async def test_different_format_cache_miss(self, sample_image, cache_enabled):
        """Test that different output format results in cache miss"""
        converter = ImageConverter()

        # Convert to PNG
        await converter.convert_with_cache(
            input_path=sample_image,
            output_format="png",
            options={"quality": 95},
            session_id="session_1"
        )

        # Convert same file to WEBP (different format)
        await converter.convert_with_cache(
            input_path=sample_image,
            output_format="webp",
            options={"quality": 95},
            session_id="session_2"
        )

        # Both should be cache misses
        cache_info = cache_enabled.get_cache_info()
        assert cache_info["stats"]["total_requests"] == 2
        assert cache_info["stats"]["misses"] == 2
        assert cache_info["stats"]["hits"] == 0
        assert cache_info["entry_count"] == 2

    @pytest.mark.asyncio
    async def test_different_options_cache_miss(self, sample_image, cache_enabled):
        """Test that different conversion options result in cache miss"""
        converter = ImageConverter()

        # Convert with quality 95
        await converter.convert_with_cache(
            input_path=sample_image,
            output_format="png",
            options={"quality": 95},
            session_id="session_1"
        )

        # Convert same file with quality 80 (different options)
        await converter.convert_with_cache(
            input_path=sample_image,
            output_format="png",
            options={"quality": 80},
            session_id="session_2"
        )

        # Both should be cache misses (different options)
        cache_info = cache_enabled.get_cache_info()
        assert cache_info["stats"]["total_requests"] == 2
        assert cache_info["stats"]["misses"] == 2
        assert cache_info["stats"]["hits"] == 0
        assert cache_info["entry_count"] == 2

    @pytest.mark.asyncio
    async def test_different_dimensions_cache_miss(self, sample_image, cache_enabled):
        """Test that different resize dimensions result in cache miss"""
        converter = ImageConverter()

        # Convert with width 50
        await converter.convert_with_cache(
            input_path=sample_image,
            output_format="png",
            options={"width": 50},
            session_id="session_1"
        )

        # Convert same file with width 100 (different dimensions)
        await converter.convert_with_cache(
            input_path=sample_image,
            output_format="png",
            options={"width": 100},
            session_id="session_2"
        )

        # Both should be cache misses (different dimensions)
        cache_info = cache_enabled.get_cache_info()
        assert cache_info["stats"]["total_requests"] == 2
        assert cache_info["stats"]["misses"] == 2
        assert cache_info["entry_count"] == 2

    @pytest.mark.asyncio
    async def test_cache_hit_rate_calculation(self, sample_image, cache_enabled):
        """Test that cache hit rate is calculated correctly"""
        converter = ImageConverter()
        options = {"quality": 95}

        # Perform 5 conversions: 1 unique (miss) + 4 duplicates (hits)
        for i in range(5):
            await converter.convert_with_cache(
                input_path=sample_image,
                output_format="png",
                options=options,
                session_id=f"session_{i}"
            )

        # Verify hit rate: 4 hits / 5 total = 0.8
        cache_info = cache_enabled.get_cache_info()
        assert cache_info["stats"]["total_requests"] == 5
        assert cache_info["stats"]["misses"] == 1
        assert cache_info["stats"]["hits"] == 4
        assert cache_enabled.get_hit_rate() == 0.8

    @pytest.mark.asyncio
    async def test_cache_with_disabled_setting(self, sample_image, cache_enabled):
        """Test that caching is bypassed when CACHE_ENABLED=False"""
        converter = ImageConverter()
        options = {"quality": 95}

        # Disable caching
        settings.CACHE_ENABLED = False

        # Perform 2 identical conversions
        await converter.convert_with_cache(
            input_path=sample_image,
            output_format="png",
            options=options,
            session_id="session_1"
        )
        await converter.convert_with_cache(
            input_path=sample_image,
            output_format="png",
            options=options,
            session_id="session_2"
        )

        # Cache should not be used (0 requests)
        cache_info = cache_enabled.get_cache_info()
        assert cache_info["stats"]["total_requests"] == 0
        assert cache_info["entry_count"] == 0

    @pytest.mark.asyncio
    async def test_cache_stores_correct_metadata(self, sample_image, cache_enabled):
        """Test that cache metadata is stored correctly"""
        converter = ImageConverter()
        options = {"quality": 90, "width": 50}

        # Perform conversion
        output_path = await converter.convert_with_cache(
            input_path=sample_image,
            output_format="webp",
            options=options,
            session_id="session_1"
        )

        # Generate same cache key
        cache_key = cache_enabled.generate_cache_key(sample_image, "webp", options)

        # Retrieve metadata
        metadata = cache_enabled.read_metadata(cache_key)

        assert metadata is not None
        assert metadata.cache_key == cache_key
        assert metadata.original_filename == sample_image.name
        assert metadata.output_format == "webp"
        assert metadata.conversion_options == options
        assert metadata.file_size > 0
        assert not metadata.is_expired()

    @pytest.mark.asyncio
    async def test_multiple_concurrent_conversions(self, sample_image, cache_enabled):
        """Test cache behavior with multiple concurrent conversions"""
        import asyncio
        converter = ImageConverter()
        options = {"quality": 95}

        # Perform 3 concurrent conversions with same parameters
        tasks = [
            converter.convert_with_cache(
                input_path=sample_image,
                output_format="png",
                options=options,
                session_id=f"session_{i}"
            )
            for i in range(3)
        ]

        results = await asyncio.gather(*tasks)

        # All conversions should succeed
        assert len(results) == 3
        assert all(r.exists() for r in results)

        # At least one should be cached (may vary due to race condition)
        cache_info = cache_enabled.get_cache_info()
        assert cache_info["stats"]["total_requests"] >= 1


class TestCacheExpiration:
    """Test cache expiration behavior"""

    @pytest.mark.asyncio
    async def test_expired_entry_triggers_reconversion(self, sample_image, temp_dir):
        """Test that expired cache entry triggers reconversion"""
        # Initialize cache with 0 hour expiration (immediate expiration)
        cache_dir = temp_dir / "cache_short_expiry"
        cache_service = initialize_cache_service(
            cache_dir=cache_dir,
            expiration_hours=0,  # Expires immediately
            max_size_mb=100
        )
        settings.CACHE_ENABLED = True
        cache_service.clear_all()

        converter = ImageConverter()
        options = {"quality": 95}

        # First conversion (cache miss)
        await converter.convert_with_cache(
            input_path=sample_image,
            output_format="png",
            options=options,
            session_id="session_1"
        )

        # Wait a moment to ensure expiration
        time.sleep(0.1)

        # Second conversion (should be cache miss due to expiration)
        await converter.convert_with_cache(
            input_path=sample_image,
            output_format="png",
            options=options,
            session_id="session_2"
        )

        # Both should be cache misses (second one expired)
        cache_info = cache_service.get_cache_info()
        assert cache_info["stats"]["total_requests"] == 2
        assert cache_info["stats"]["misses"] == 2
        assert cache_info["stats"]["hits"] == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_entries(self, sample_image, temp_dir):
        """Test that cleanup removes expired entries"""
        # Initialize cache with short expiration
        cache_dir = temp_dir / "cache_cleanup"
        cache_service = initialize_cache_service(
            cache_dir=cache_dir,
            expiration_hours=0,
            max_size_mb=100
        )
        settings.CACHE_ENABLED = True
        cache_service.clear_all()

        converter = ImageConverter()

        # Create cache entry
        await converter.convert_with_cache(
            input_path=sample_image,
            output_format="png",
            options={"quality": 95},
            session_id="session_1"
        )

        # Verify entry exists
        assert cache_service.get_cache_info()["entry_count"] == 1

        # Wait for expiration
        time.sleep(0.1)

        # Run cleanup
        cleanup_stats = cache_service.cleanup_expired()

        # Expired entry should be removed
        assert cleanup_stats["expired_removed"] >= 1
        assert cache_service.get_cache_info()["entry_count"] == 0


class TestCacheWithRouters:
    """Test cache integration through API routers"""

    def test_api_conversion_uses_cache(self, test_client, sample_image, cache_enabled):
        """Test that API endpoints use cache correctly"""
        # Read image file
        with open(sample_image, 'rb') as f:
            image_data = f.read()

        # First API call (cache miss)
        response1 = test_client.post(
            "/api/image/convert",
            files={"file": ("sample.jpg", image_data, "image/jpeg")},
            data={"output_format": "png", "quality": 95}
        )

        assert response1.status_code == 200

        # Second API call with same parameters (cache hit)
        response2 = test_client.post(
            "/api/image/convert",
            files={"file": ("sample.jpg", image_data, "image/jpeg")},
            data={"output_format": "png", "quality": 95}
        )

        assert response2.status_code == 200

        # Verify cache was used
        cache_info = cache_enabled.get_cache_info()
        assert cache_info["stats"]["total_requests"] == 2
        assert cache_info["stats"]["hits"] >= 1

    def test_api_different_quality_cache_miss(self, test_client, sample_image, cache_enabled):
        """Test that API with different quality options results in cache miss"""
        with open(sample_image, 'rb') as f:
            image_data = f.read()

        # Convert with quality 95
        response1 = test_client.post(
            "/api/image/convert",
            files={"file": ("sample.jpg", image_data, "image/jpeg")},
            data={"output_format": "png", "quality": 95}
        )
        assert response1.status_code == 200

        # Convert with quality 80 (different options)
        response2 = test_client.post(
            "/api/image/convert",
            files={"file": ("sample.jpg", image_data, "image/jpeg")},
            data={"output_format": "png", "quality": 80}
        )
        assert response2.status_code == 200

        # Both should be cache misses
        cache_info = cache_enabled.get_cache_info()
        assert cache_info["stats"]["total_requests"] == 2
        assert cache_info["stats"]["misses"] == 2
        assert cache_info["entry_count"] == 2


class TestCacheSizeManagement:
    """Test cache size limits and cleanup"""

    @pytest.mark.asyncio
    async def test_cache_cleanup_when_size_exceeded(self, temp_dir):
        """Test that cache cleanup removes oldest entries when size limit exceeded"""
        # Initialize cache with very small size limit (1 MB)
        cache_dir = temp_dir / "cache_small"
        cache_service = initialize_cache_service(
            cache_dir=cache_dir,
            expiration_hours=24,
            max_size_mb=1
        )
        settings.CACHE_ENABLED = True
        cache_service.clear_all()

        converter = ImageConverter()

        # Create multiple cache entries
        for i in range(5):
            # Create unique image for each conversion
            image_path = temp_dir / f"image_{i}.jpg"
            img = Image.new('RGB', (200, 200), color=(i * 50, 100, 150))
            img.save(image_path, 'JPEG')

            await converter.convert_with_cache(
                input_path=image_path,
                output_format="png",
                options={"quality": 95},
                session_id=f"session_{i}"
            )

        # Run size-based cleanup
        cleanup_stats = cache_service.cleanup_by_size()

        # Some entries should be removed if size exceeded
        total_size_mb = cache_service.get_total_cache_size() / (1024 * 1024)
        assert total_size_mb <= 1.0 or cleanup_stats["entries_removed"] > 0

    @pytest.mark.asyncio
    async def test_cache_info_accuracy(self, sample_image, cache_enabled):
        """Test that cache info returns accurate statistics"""
        converter = ImageConverter()

        # Perform conversions
        await converter.convert_with_cache(
            input_path=sample_image,
            output_format="png",
            options={"quality": 95},
            session_id="session_1"
        )

        await converter.convert_with_cache(
            input_path=sample_image,
            output_format="webp",
            options={"quality": 90},
            session_id="session_2"
        )

        # Get cache info
        cache_info = cache_enabled.get_cache_info()

        assert "cache_dir" in cache_info
        assert "total_size_mb" in cache_info
        assert "max_size_mb" in cache_info
        assert cache_info["max_size_mb"] == 100
        assert "entry_count" in cache_info
        assert cache_info["entry_count"] == 2
        assert "expiration_hours" in cache_info
        assert cache_info["expiration_hours"] == 1
        assert "stats" in cache_info
        assert "hit_rate" in cache_info
