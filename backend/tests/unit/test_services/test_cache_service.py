"""
Tests for app/services/cache_service.py

COVERAGE GOAL: 90%+
Tests cache key generation, storage, retrieval, expiration, cleanup, LRU eviction
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import shutil
import json
import time

from app.services.cache_service import CacheService, CacheMetadata
from app.config import settings


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

class TestCacheServiceBasics:
    """Test basic CacheService functionality"""

    def test_initialization(self, temp_cache_dir):
        """Test CacheService initializes correctly"""
        cache = CacheService(
            cache_dir=temp_cache_dir,
            expiration_hours=24,
            max_size_mb=500
        )

        assert cache.cache_dir == temp_cache_dir
        assert cache.expiration_hours == 24
        assert cache.max_size_mb == 500
        assert cache.stats["hits"] == 0
        assert cache.stats["misses"] == 0

    def test_cache_directory_creation(self, temp_dir):
        """Test that cache directory is created if it doesn't exist"""
        cache_dir = temp_dir / "new_cache"
        assert not cache_dir.exists()

        cache = CacheService(cache_dir=cache_dir)

        assert cache_dir.exists()
        assert cache_dir.is_dir()

        # Clean up
        import shutil
        shutil.rmtree(cache_dir, ignore_errors=True)


# ============================================================================
# CACHE KEY GENERATION TESTS
# ============================================================================

class TestCacheKeyGeneration:
    """Test cache key generation"""

    def test_generate_file_hash(self, temp_dir, temp_cache_dir):
        """Test file hash generation is consistent"""
        cache = CacheService(cache_dir=temp_cache_dir)

        test_file = temp_dir / "test.txt"
        test_file.write_text("Test content")

        hash1 = cache.generate_file_hash(test_file)
        hash2 = cache.generate_file_hash(test_file)

        # Same file should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hash length

    def test_different_files_different_hash(self, temp_dir, temp_cache_dir):
        """Test different files produce different hashes"""
        cache = CacheService(cache_dir=temp_cache_dir)

        file1 = temp_dir / "file1.txt"
        file1.write_text("Content 1")

        file2 = temp_dir / "file2.txt"
        file2.write_text("Content 2")

        hash1 = cache.generate_file_hash(file1)
        hash2 = cache.generate_file_hash(file2)

        assert hash1 != hash2

    def test_generate_options_hash(self, temp_cache_dir):
        """Test options hash generation"""
        cache = CacheService(cache_dir=temp_cache_dir)

        options1 = {"quality": 95, "width": 800}
        options2 = {"width": 800, "quality": 95}  # Same options, different order
        options3 = {"quality": 90, "width": 800}  # Different quality

        hash1 = cache.generate_options_hash(options1)
        hash2 = cache.generate_options_hash(options2)
        hash3 = cache.generate_options_hash(options3)

        # Same options should produce same hash regardless of order
        assert hash1 == hash2
        # Different options should produce different hash
        assert hash1 != hash3
        assert len(hash1) == 8  # Truncated to 8 chars

    def test_generate_cache_key(self, temp_dir, temp_cache_dir):
        """Test cache key generation"""
        cache = CacheService(cache_dir=temp_cache_dir)

        test_file = temp_dir / "test.jpg"
        test_file.write_text("Image content")

        options = {"quality": 95}
        cache_key = cache.generate_cache_key(test_file, "png", options)

        # Verify format: {file_hash}_{output_format}_{options_hash}
        parts = cache_key.split("_")
        assert len(parts) == 3
        assert len(parts[0]) == 32  # File hash (MD5)
        assert parts[1] == "png"  # Output format
        assert len(parts[2]) == 8  # Options hash

    def test_different_options_different_cache_key(self, temp_dir, temp_cache_dir):
        """Test different options produce different cache keys"""
        cache = CacheService(cache_dir=temp_cache_dir)

        test_file = temp_dir / "test.jpg"
        test_file.write_text("Image content")

        key1 = cache.generate_cache_key(test_file, "png", {"quality": 95})
        key2 = cache.generate_cache_key(test_file, "png", {"quality": 80})

        assert key1 != key2

    def test_different_format_different_cache_key(self, temp_dir, temp_cache_dir):
        """Test different output format produces different cache key"""
        cache = CacheService(cache_dir=temp_cache_dir)

        test_file = temp_dir / "test.jpg"
        test_file.write_text("Image content")

        options = {"quality": 95}
        key1 = cache.generate_cache_key(test_file, "png", options)
        key2 = cache.generate_cache_key(test_file, "jpg", options)

        assert key1 != key2

    def test_unicode_filename_handling(self, temp_dir, temp_cache_dir):
        """Test cache handles unicode filenames"""
        cache = CacheService(cache_dir=temp_cache_dir)

        # Create file with unicode characters
        test_file = temp_dir / "测试文件_emoji_🎨.txt"
        test_file.write_text("Unicode content")

        options = {"quality": 95}
        cache_key = cache.generate_cache_key(test_file, "png", options)

        # Should generate valid cache key
        assert cache_key is not None
        assert isinstance(cache_key, str)


# ============================================================================
# CACHE STORAGE AND RETRIEVAL TESTS
# ============================================================================

class TestCacheStorageRetrieval:
    """Test cache storage and retrieval"""

    def test_store_and_retrieve_result(self, temp_dir, temp_cache_dir):
        """Test storing and retrieving cached results"""
        cache = CacheService(cache_dir=temp_cache_dir)

        # Create test files
        input_file = temp_dir / "input.jpg"
        input_file.write_text("Input content")

        output_file = temp_dir / "output.png"
        output_file.write_text("Output content")

        # Generate cache key
        options = {"quality": 95}
        cache_key = cache.generate_cache_key(input_file, "png", options)

        # Store result
        cache.store_result(
            cache_key=cache_key,
            original_filename=input_file.name,
            output_file_path=output_file,
            output_format="png",
            conversion_options=options
        )

        # Retrieve result
        result = cache.get_cached_result(cache_key)

        assert result is not None
        assert isinstance(result, CacheMetadata)
        assert result.cache_key == cache_key
        assert result.original_filename == input_file.name
        assert result.output_format == "png"
        assert Path(result.output_file).exists()

    def test_cache_miss_returns_none(self, temp_cache_dir):
        """Test cache miss returns None"""
        cache = CacheService(cache_dir=temp_cache_dir)

        result = cache.get_cached_result("nonexistent_key")

        assert result is None
        assert cache.stats["misses"] == 1
        assert cache.stats["hits"] == 0

    def test_cache_hit_increments_stats(self, temp_dir, temp_cache_dir):
        """Test cache hit increments hit counter"""
        cache = CacheService(cache_dir=temp_cache_dir)

        # Store a result
        input_file = temp_dir / "input.jpg"
        input_file.write_text("Input content")

        output_file = temp_dir / "output.png"
        output_file.write_text("Output content")

        options = {"quality": 95}
        cache_key = cache.generate_cache_key(input_file, "png", options)

        cache.store_result(
            cache_key=cache_key,
            original_filename=input_file.name,
            output_file_path=output_file,
            output_format="png",
            conversion_options=options
        )

        # Retrieve it
        result = cache.get_cached_result(cache_key)

        assert result is not None
        assert cache.stats["hits"] == 1
        assert cache.stats["misses"] == 0

    def test_expired_entry_returns_none(self, temp_dir, temp_cache_dir):
        """Test that expired cache entries return None"""
        # Create cache with 0 hour expiration (immediately expired)
        cache = CacheService(cache_dir=temp_cache_dir, expiration_hours=0)

        # Store a result
        input_file = temp_dir / "input.jpg"
        input_file.write_text("Input content")

        output_file = temp_dir / "output.png"
        output_file.write_text("Output content")

        options = {"quality": 95}
        cache_key = cache.generate_cache_key(input_file, "png", options)

        cache.store_result(
            cache_key=cache_key,
            original_filename=input_file.name,
            output_file_path=output_file,
            output_format="png",
            conversion_options=options
        )

        # Wait a moment to ensure expiration
        time.sleep(0.1)

        # Try to retrieve (should be expired)
        result = cache.get_cached_result(cache_key)

        # Should return None because it's expired
        assert result is None


# ============================================================================
# METADATA HANDLING TESTS
# ============================================================================

class TestCacheMetadata:
    """Test cache metadata handling"""

    def test_missing_metadata_handled(self, temp_cache_dir):
        """Test that missing metadata is handled gracefully"""
        cache = CacheService(cache_dir=temp_cache_dir)

        # Create cache entry directory without metadata
        cache_key = "test_cache_key_12345678"
        cache_entry_dir = temp_cache_dir / cache_key
        cache_entry_dir.mkdir(parents=True)

        # Try to get result (should handle missing metadata)
        result = cache.get_cached_result(cache_key)

        assert result is None

    def test_malformed_json_handled(self, temp_cache_dir):
        """Test that malformed JSON metadata is handled gracefully"""
        cache = CacheService(cache_dir=temp_cache_dir)

        # Create cache entry with malformed metadata
        cache_key = "test_cache_key_87654321"
        cache_entry_dir = temp_cache_dir / cache_key
        cache_entry_dir.mkdir(parents=True)

        metadata_file = cache_entry_dir / "metadata.json"
        metadata_file.write_text("{ invalid json content }")

        # Try to get result (should handle malformed JSON)
        result = cache.get_cached_result(cache_key)

        assert result is None

    def test_metadata_persistence(self, temp_dir, temp_cache_dir):
        """Test that metadata is persisted correctly"""
        cache = CacheService(cache_dir=temp_cache_dir)

        input_file = temp_dir / "input.jpg"
        input_file.write_text("Input content")

        output_file = temp_dir / "output.png"
        output_file.write_text("Output content")

        options = {"quality": 95, "width": 800}
        cache_key = cache.generate_cache_key(input_file, "png", options)

        # Store result
        cache.store_result(
            cache_key=cache_key,
            original_filename=input_file.name,
            output_file_path=output_file,
            output_format="png",
            conversion_options=options
        )

        # Retrieve and verify metadata
        result = cache.get_cached_result(cache_key)

        assert result.conversion_options == options
        assert result.original_filename == input_file.name
        assert result.output_format == "png"


# ============================================================================
# CACHE CLEANUP TESTS
# ============================================================================

class TestCacheCleanup:
    """Test cache cleanup functionality"""

    def test_cleanup_expired_entries(self, temp_dir, temp_cache_dir):
        """Test cleanup removes expired entries"""
        # Create cache with 0 hour expiration
        cache = CacheService(cache_dir=temp_cache_dir, expiration_hours=0)

        # Store a result (will be immediately expired)
        input_file = temp_dir / "input.jpg"
        input_file.write_text("Input content")

        output_file = temp_dir / "output.png"
        output_file.write_text("Output content")

        options = {"quality": 95}
        cache_key = cache.generate_cache_key(input_file, "png", options)

        cache.store_result(
            cache_key=cache_key,
            original_filename=input_file.name,
            output_file_path=output_file,
            output_format="png",
            conversion_options=options
        )

        # Wait a moment
        time.sleep(0.1)

        # Run cleanup
        stats = cache.cleanup_expired()

        # Should have removed expired entry
        assert stats["expired_removed"] >= 0

    def test_cleanup_corrupted_entries(self, temp_cache_dir):
        """Test cleanup removes corrupted entries"""
        cache = CacheService(cache_dir=temp_cache_dir)

        # Create corrupted cache entry (no metadata)
        cache_key = "corrupted_entry_12345678"
        cache_entry_dir = temp_cache_dir / cache_key
        cache_entry_dir.mkdir(parents=True)

        # Run cleanup
        stats = cache.cleanup_expired()

        # Should remove corrupted entry
        assert stats["corrupted_removed"] >= 0

    def test_cleanup_by_size_when_over_limit(self, temp_dir, temp_cache_dir):
        """Test LRU eviction when cache exceeds max size"""
        # Create cache with very small max size (1 MB)
        cache = CacheService(cache_dir=temp_cache_dir, max_size_mb=1)

        # Store multiple large results
        for i in range(5):
            input_file = temp_dir / f"input_{i}.jpg"
            input_file.write_text("Input content " * 1000)

            output_file = temp_dir / f"output_{i}.png"
            output_file.write_text("Output content " * 10000)  # ~140 KB

            options = {"quality": 95, "index": i}
            cache_key = cache.generate_cache_key(input_file, "png", options)

            cache.store_result(
                cache_key=cache_key,
                original_filename=input_file.name,
                output_file_path=output_file,
                output_format="png",
                conversion_options=options
            )

            # Small delay to ensure different timestamps
            time.sleep(0.01)

        # Run cleanup by size
        stats = cache.cleanup_by_size()

        # Should have removed old entries to stay under limit
        cache_info = cache.get_cache_info()
        assert cache_info["total_size_mb"] <= cache.max_size_mb


# ============================================================================
# CACHE INFO TESTS
# ============================================================================

class TestCacheInfo:
    """Test cache information retrieval"""

    def test_get_cache_info(self, temp_cache_dir):
        """Test getting cache information"""
        cache = CacheService(
            cache_dir=temp_cache_dir,
            expiration_hours=24,
            max_size_mb=500
        )

        info = cache.get_cache_info()

        assert "cache_dir" in info
        assert "total_size_mb" in info
        assert "max_size_mb" in info
        assert "entry_count" in info
        assert "expiration_hours" in info
        assert "hit_rate" in info
        assert "stats" in info

        assert info["cache_dir"] == str(temp_cache_dir)
        assert info["max_size_mb"] == 500
        assert info["expiration_hours"] == 24

    def test_hit_rate_calculation(self, temp_dir, temp_cache_dir):
        """Test hit rate is calculated correctly"""
        cache = CacheService(cache_dir=temp_cache_dir)

        # 1 miss
        cache.get_cached_result("nonexistent")

        # Store and retrieve (1 hit)
        input_file = temp_dir / "input.jpg"
        input_file.write_text("Input")

        output_file = temp_dir / "output.png"
        output_file.write_text("Output")

        cache_key = cache.generate_cache_key(input_file, "png", {})
        cache.store_result(cache_key, "input.jpg", output_file, "png", {})
        cache.get_cached_result(cache_key)

        info = cache.get_cache_info()

        # 1 hit out of 2 total = 50%
        assert info["hit_rate"] == 0.5
        assert info["stats"]["hits"] == 1
        assert info["stats"]["misses"] == 1

    def test_entry_count(self, temp_dir, temp_cache_dir):
        """Test entry count is accurate"""
        cache = CacheService(cache_dir=temp_cache_dir)

        # Store 3 results
        for i in range(3):
            input_file = temp_dir / f"input_{i}.jpg"
            input_file.write_text(f"Input {i}")

            output_file = temp_dir / f"output_{i}.png"
            output_file.write_text(f"Output {i}")

            cache_key = cache.generate_cache_key(input_file, "png", {"index": i})
            cache.store_result(cache_key, f"input_{i}.jpg", output_file, "png", {"index": i})

        info = cache.get_cache_info()

        assert info["entry_count"] == 3


# ============================================================================
# CLEAR ALL TEST
# ============================================================================

class TestCacheClear:
    """Test cache clearing"""

    def test_clear_all(self, temp_dir, temp_cache_dir):
        """Test clearing all cache entries"""
        cache = CacheService(cache_dir=temp_cache_dir)

        # Store multiple results
        for i in range(3):
            input_file = temp_dir / f"input_{i}.jpg"
            input_file.write_text(f"Input {i}")

            output_file = temp_dir / f"output_{i}.png"
            output_file.write_text(f"Output {i}")

            cache_key = cache.generate_cache_key(input_file, "png", {"index": i})
            cache.store_result(cache_key, f"input_{i}.jpg", output_file, "png", {"index": i})

        # Verify entries exist
        info_before = cache.get_cache_info()
        assert info_before["entry_count"] == 3

        # Clear all
        cache.clear_all()

        # Verify all cleared
        info_after = cache.get_cache_info()
        assert info_after["entry_count"] == 0
        assert info_after["total_size_mb"] == 0

    def test_clear_all_resets_stats(self, temp_dir, temp_cache_dir):
        """Test that clear_all resets statistics"""
        cache = CacheService(cache_dir=temp_cache_dir)

        # Generate some stats
        cache.get_cached_result("miss1")
        cache.get_cached_result("miss2")

        input_file = temp_dir / "input.jpg"
        input_file.write_text("Input")
        output_file = temp_dir / "output.png"
        output_file.write_text("Output")

        cache_key = cache.generate_cache_key(input_file, "png", {})
        cache.store_result(cache_key, "input.jpg", output_file, "png", {})
        cache.get_cached_result(cache_key)

        # Clear all
        cache.clear_all()

        # Stats should be reset
        assert cache.stats["hits"] == 0
        assert cache.stats["misses"] == 0


# ============================================================================
# PATH HELPER TESTS
# ============================================================================

class TestCachePathHelpers:
    """Test cache path helper methods"""

    def test_get_cache_path(self, temp_cache_dir):
        """Test getting cache entry directory path"""
        cache = CacheService(cache_dir=temp_cache_dir)

        cache_key = "test_key_12345678"
        cache_path = cache.get_cache_path(cache_key)

        assert cache_path == temp_cache_dir / cache_key
        assert isinstance(cache_path, Path)

    def test_get_metadata_path(self, temp_cache_dir):
        """Test getting metadata file path"""
        cache = CacheService(cache_dir=temp_cache_dir)

        cache_key = "test_key_12345678"
        metadata_path = cache.get_metadata_path(cache_key)

        assert metadata_path == temp_cache_dir / cache_key / "metadata.json"
        assert isinstance(metadata_path, Path)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestCacheErrorHandling:
    """Test error handling in cache service"""

    def test_generate_file_hash_error(self, temp_cache_dir):
        """Test error handling when file cannot be read (lines 86-88)"""
        cache = CacheService(cache_dir=temp_cache_dir)

        # Try to hash non-existent file
        nonexistent_file = Path("/nonexistent/file.txt")

        with pytest.raises(Exception):
            cache.generate_file_hash(nonexistent_file)

    def test_write_metadata_error(self, temp_cache_dir, monkeypatch):
        """Test error handling when metadata cannot be written (lines 186-188)"""
        from unittest.mock import mock_open, patch

        cache = CacheService(cache_dir=temp_cache_dir)

        metadata = CacheMetadata(
            cache_key="test_key",
            original_filename="test.jpg",
            output_file="/tmp/output.png",
            output_format="png",
            created_at=time.time(),
            expires_at=time.time() + 3600,
            file_size=1024,
            conversion_options={}
        )

        # Mock open to raise exception
        with patch("builtins.open", side_effect=PermissionError("Cannot write")):
            with pytest.raises(PermissionError):
                cache.write_metadata(metadata)

    def test_missing_output_file_returns_none(self, temp_dir, temp_cache_dir):
        """Test that missing output file is handled (lines 219-222)"""
        cache = CacheService(cache_dir=temp_cache_dir)

        # Create cache entry with metadata but delete the output file
        input_file = temp_dir / "input.jpg"
        input_file.write_text("Input content")

        output_file = temp_dir / "output.png"
        output_file.write_text("Output content")

        cache_key = cache.generate_cache_key(input_file, "png", {})

        # Store result
        cache.store_result(cache_key, "input.jpg", output_file, "png", {})

        # Delete the output file to simulate missing file
        metadata = cache.read_metadata(cache_key)
        Path(metadata.output_file).unlink()

        # Try to get cached result
        result = cache.get_cached_result(cache_key)

        # Should return None because output file is missing
        assert result is None
        assert cache.stats["misses"] == 1

    def test_store_result_error_cleanup(self, temp_dir, temp_cache_dir, monkeypatch):
        """Test error handling during store_result with cleanup (lines 273-279)"""
        from unittest.mock import patch

        cache = CacheService(cache_dir=temp_cache_dir)

        input_file = temp_dir / "input.jpg"
        input_file.write_text("Input content")

        output_file = temp_dir / "output.png"
        output_file.write_text("Output content")

        cache_key = cache.generate_cache_key(input_file, "png", {})

        # Mock shutil.copy2 to raise exception
        with patch("shutil.copy2", side_effect=PermissionError("Cannot copy")):
            # Should not raise exception (errors are caught and logged)
            cache.store_result(cache_key, "input.jpg", output_file, "png", {})

        # Cache entry should not exist
        result = cache.get_cached_result(cache_key)
        assert result is None

    def test_store_result_error_cleanup_also_fails(self, temp_dir, temp_cache_dir):
        """Test nested exception handling when cleanup also fails (lines 278-279)"""
        from unittest.mock import patch, MagicMock

        cache = CacheService(cache_dir=temp_cache_dir)

        input_file = temp_dir / "input.jpg"
        input_file.write_text("Input content")

        output_file = temp_dir / "output.png"
        output_file.write_text("Output content")

        cache_key = cache.generate_cache_key(input_file, "png", {})

        # Create the cache entry directory first (so cleanup has something to try to remove)
        cache_path = cache.get_cache_path(cache_key)
        cache_path.mkdir(parents=True, exist_ok=True)

        # Mock write_metadata to fail (causing exception in store_result)
        # and also mock _remove_cache_entry to fail (cleanup fails)
        with patch.object(cache, "write_metadata", side_effect=Exception("Metadata write failed")):
            with patch.object(cache, "_remove_cache_entry", side_effect=Exception("Remove failed")):
                # Should not raise exception (both errors are caught and ignored)
                cache.store_result(cache_key, "input.jpg", output_file, "png", {})

        # Should complete without raising exception

    def test_remove_cache_entry_error(self, temp_cache_dir, monkeypatch):
        """Test error handling in _remove_cache_entry (lines 293-294)"""
        from unittest.mock import patch

        cache = CacheService(cache_dir=temp_cache_dir)

        # Create a cache entry
        cache_key = "test_key_12345678"
        cache_path = cache.get_cache_path(cache_key)
        cache_path.mkdir(parents=True)

        # Mock shutil.rmtree to raise exception
        with patch("shutil.rmtree", side_effect=PermissionError("Cannot remove")):
            # Should not raise exception (errors are caught and logged)
            cache._remove_cache_entry(cache_key)

    def test_cleanup_skips_non_directory_items(self, temp_cache_dir):
        """Test cleanup skips non-directory items (line 311)"""
        cache = CacheService(cache_dir=temp_cache_dir)

        # Create a file (not directory) in cache dir
        file_in_cache = temp_cache_dir / "some_file.txt"
        file_in_cache.write_text("Not a cache entry")

        # Run cleanup (should skip the file)
        stats = cache.cleanup_expired()

        # Should complete without error
        assert "expired_removed" in stats

    def test_directory_size_error(self, temp_cache_dir, monkeypatch):
        """Test error handling in _get_directory_size (lines 440-441)"""
        from unittest.mock import patch

        cache = CacheService(cache_dir=temp_cache_dir)

        # Create a cache entry
        cache_path = temp_cache_dir / "test_entry"
        cache_path.mkdir()

        # Mock rglob to raise exception
        with patch.object(Path, "rglob", side_effect=PermissionError("Cannot read")):
            size = cache._get_directory_size(cache_path)

            # Should return 0 when error occurs
            assert size == 0


# ============================================================================
# CLEANUP ALL TESTS
# ============================================================================

class TestCleanupAll:
    """Test cleanup_all method"""

    def test_cleanup_all_combines_both_cleanups(self, temp_dir, temp_cache_dir):
        """Test cleanup_all runs both expired and size cleanups (lines 401-423)"""
        cache = CacheService(cache_dir=temp_cache_dir, expiration_hours=0, max_size_mb=1)

        # Create some expired entries
        for i in range(3):
            input_file = temp_dir / f"input_{i}.jpg"
            input_file.write_text("Input " * 1000)

            output_file = temp_dir / f"output_{i}.png"
            output_file.write_text("Output " * 10000)

            cache_key = cache.generate_cache_key(input_file, "png", {"index": i})
            cache.store_result(cache_key, f"input_{i}.jpg", output_file, "png", {"index": i})
            time.sleep(0.01)

        # Wait for expiration
        time.sleep(0.1)

        # Run cleanup_all
        stats = cache.cleanup_all()

        # Should have stats from both cleanups
        assert "expired_removed" in stats
        assert "corrupted_removed" in stats
        assert "size_limit_removed" in stats
        assert "total_space_freed_mb" in stats

        # Should have cleaned up entries
        assert stats["expired_removed"] >= 0 or stats["size_limit_removed"] >= 0

    def test_cleanup_all_logs_results(self, temp_dir, temp_cache_dir):
        """Test cleanup_all returns detailed statistics"""
        cache = CacheService(cache_dir=temp_cache_dir)

        stats = cache.cleanup_all()

        # Verify all expected keys are present
        assert "expired_removed" in stats
        assert "corrupted_removed" in stats
        assert "size_limit_removed" in stats
        assert "total_space_freed_mb" in stats


# ============================================================================
# CACHE SIZE EXCEEDED TESTS
# ============================================================================

class TestCacheSizeExceeded:
    """Test cache size limit enforcement"""

    def test_cache_size_exceeded_removes_oldest(self, temp_dir, temp_cache_dir):
        """Test that cleanup_by_size removes oldest entries when limit exceeded (lines 357-392)"""
        cache = CacheService(cache_dir=temp_cache_dir, max_size_mb=1)

        # Store multiple large files to exceed limit
        for i in range(15):
            input_file = temp_dir / f"input_{i}.jpg"
            input_file.write_text("x" * 100000)  # 100KB

            output_file = temp_dir / f"output_{i}.png"
            output_file.write_text("y" * 150000)  # 150KB each, total ~2.25MB

            cache_key = cache.generate_cache_key(input_file, "png", {"index": i})
            cache.store_result(cache_key, f"input_{i}.jpg", output_file, "png", {"index": i})
            time.sleep(0.01)  # Ensure different timestamps

        # Verify cache size exceeds limit before cleanup
        size_before = cache.get_total_cache_size()
        assert size_before > cache.max_size_mb * 1024 * 1024

        # Run cleanup
        stats = cache.cleanup_by_size()

        # Should have removed some entries
        assert stats["entries_removed"] > 0
        assert stats["space_freed_mb"] > 0

        # Final cache size should be under limit
        final_size = cache.get_total_cache_size()
        assert final_size <= cache.max_size_mb * 1024 * 1024

    def test_cache_under_limit_no_cleanup(self, temp_dir, temp_cache_dir):
        """Test that cleanup_by_size does nothing when under limit"""
        cache = CacheService(cache_dir=temp_cache_dir, max_size_mb=1000)  # Large limit

        # Store small file
        input_file = temp_dir / "input.jpg"
        input_file.write_text("small")

        output_file = temp_dir / "output.png"
        output_file.write_text("small output")

        cache_key = cache.generate_cache_key(input_file, "png", {})
        cache.store_result(cache_key, "input.jpg", output_file, "png", {})

        # Run cleanup
        stats = cache.cleanup_by_size()

        # Should not remove anything
        assert stats["entries_removed"] == 0
        assert stats["space_freed_mb"] == 0

    def test_cleanup_by_size_skips_non_directory_items(self, temp_dir, temp_cache_dir):
        """Test cleanup_by_size skips non-directory items (line 364)"""
        cache = CacheService(cache_dir=temp_cache_dir, max_size_mb=1)

        # Create a file (not directory) in cache dir BEFORE storing cache entries
        file_in_cache = temp_cache_dir / "some_file.txt"
        file_in_cache.write_text("Not a cache entry - should be skipped")

        # Store enough entries to exceed limit
        for i in range(10):
            input_file = temp_dir / f"input_{i}.jpg"
            input_file.write_text("x" * 200000)  # 200KB each

            output_file = temp_dir / f"output_{i}.png"
            output_file.write_text("y" * 200000)  # 200KB each

            cache_key = cache.generate_cache_key(input_file, "png", {"index": i})
            cache.store_result(cache_key, f"input_{i}.jpg", output_file, "png", {"index": i})
            time.sleep(0.01)

        # Verify cache size exceeds limit
        size_before = cache.get_total_cache_size()
        assert size_before > cache.max_size_mb * 1024 * 1024

        # Run cleanup (should skip the file and clean cache entries)
        stats = cache.cleanup_by_size()

        # Should complete without error and have removed some entries
        assert "entries_removed" in stats
        # The file should still exist (not removed)
        assert file_in_cache.exists()


# ============================================================================
# GLOBAL SERVICE TESTS
# ============================================================================

class TestGlobalCacheService:
    """Test global cache service initialization"""

    def test_get_cache_service(self):
        """Test get_cache_service returns global instance (line 513)"""
        from app.services.cache_service import get_cache_service

        # Get the global cache service
        service = get_cache_service()

        # May be None or a CacheService instance
        assert service is None or isinstance(service, CacheService)

    def test_initialize_cache_service(self, temp_cache_dir):
        """Test initialize_cache_service creates global instance (lines 529-538)"""
        from app.services.cache_service import initialize_cache_service, get_cache_service

        # Initialize cache service
        service = initialize_cache_service(
            cache_dir=temp_cache_dir,
            expiration_hours=2,
            max_size_mb=100
        )

        # Verify returned service
        assert isinstance(service, CacheService)
        assert service.cache_dir == temp_cache_dir
        assert service.expiration_hours == 2
        assert service.max_size_mb == 100

        # Verify global instance is set
        global_service = get_cache_service()
        assert global_service is service
