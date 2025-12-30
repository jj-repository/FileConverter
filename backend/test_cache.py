"""
Simple test script to verify cache implementation
"""

import sys
import asyncio
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.cache_service import CacheService
from app.config import CACHE_DIR
import tempfile
import hashlib


async def test_cache_service():
    """Test basic cache service functionality"""
    print("=" * 60)
    print("Testing FileConverter Cache Service")
    print("=" * 60)

    # Create a temporary cache directory for testing
    test_cache_dir = Path(tempfile.mkdtemp(prefix="cache_test_"))
    print(f"\n1. Created test cache directory: {test_cache_dir}")

    # Initialize cache service
    cache_service = CacheService(
        cache_dir=test_cache_dir,
        expiration_hours=1,
        max_size_mb=100
    )
    print("2. Initialized cache service")

    # Create a test file
    test_file = Path(tempfile.mktemp(suffix=".txt"))
    test_content = "This is a test file for cache validation"
    test_file.write_text(test_content)
    print(f"3. Created test file: {test_file}")

    # Test 1: Generate cache key
    print("\n" + "-" * 60)
    print("TEST 1: Cache Key Generation")
    print("-" * 60)

    options = {"quality": 95, "width": 800}
    cache_key = cache_service.generate_cache_key(test_file, "png", options)
    print(f"Generated cache key: {cache_key}")

    file_hash = cache_service.generate_file_hash(test_file)
    print(f"File hash: {file_hash}")

    options_hash = cache_service.generate_options_hash(options)
    print(f"Options hash: {options_hash}")

    expected_key = f"{file_hash}_png_{options_hash}"
    assert cache_key == expected_key, "Cache key mismatch!"
    print("✓ Cache key generation: PASSED")

    # Test 2: Cache miss
    print("\n" + "-" * 60)
    print("TEST 2: Cache Miss")
    print("-" * 60)

    cached_result = cache_service.get_cached_result(cache_key)
    assert cached_result is None, "Expected cache miss!"
    print(f"Cache misses: {cache_service.stats['misses']}")
    print("✓ Cache miss detection: PASSED")

    # Test 3: Store result
    print("\n" + "-" * 60)
    print("TEST 3: Store Cache Result")
    print("-" * 60)

    # Create a mock output file
    output_file = Path(tempfile.mktemp(suffix=".png"))
    output_file.write_text("Mock converted file content")

    cache_service.store_result(
        cache_key=cache_key,
        original_filename=test_file.name,
        output_file_path=output_file,
        output_format="png",
        conversion_options=options
    )
    print(f"Stored result for cache key: {cache_key}")

    # Verify cache directory was created
    cache_path = cache_service.get_cache_path(cache_key)
    assert cache_path.exists(), "Cache directory not created!"
    print(f"Cache directory created: {cache_path}")

    # Verify metadata was created
    metadata_path = cache_service.get_metadata_path(cache_key)
    assert metadata_path.exists(), "Metadata file not created!"
    print(f"Metadata file created: {metadata_path}")
    print("✓ Cache storage: PASSED")

    # Test 4: Cache hit
    print("\n" + "-" * 60)
    print("TEST 4: Cache Hit")
    print("-" * 60)

    cached_result = cache_service.get_cached_result(cache_key)
    assert cached_result is not None, "Expected cache hit!"
    print(f"Cache hits: {cache_service.stats['hits']}")
    print(f"Cached file: {cached_result.output_file}")
    print(f"Original filename: {cached_result.original_filename}")
    print(f"Output format: {cached_result.output_format}")
    print(f"File size: {cached_result.file_size} bytes")
    print("✓ Cache hit detection: PASSED")

    # Test 5: Cache info
    print("\n" + "-" * 60)
    print("TEST 5: Cache Information")
    print("-" * 60)

    cache_info = cache_service.get_cache_info()
    print(f"Cache directory: {cache_info['cache_dir']}")
    print(f"Total size: {cache_info['total_size_mb']:.4f} MB")
    print(f"Max size: {cache_info['max_size_mb']} MB")
    print(f"Entry count: {cache_info['entry_count']}")
    print(f"Expiration: {cache_info['expiration_hours']} hours")
    print(f"Hit rate: {cache_info['hit_rate']:.2%}")
    print(f"Stats: {cache_info['stats']}")
    print("✓ Cache info retrieval: PASSED")

    # Test 6: Different options = different cache key
    print("\n" + "-" * 60)
    print("TEST 6: Different Options Cache Key")
    print("-" * 60)

    different_options = {"quality": 80, "width": 1024}
    different_cache_key = cache_service.generate_cache_key(test_file, "png", different_options)
    assert different_cache_key != cache_key, "Different options should produce different cache key!"
    print(f"Original cache key: {cache_key}")
    print(f"Different cache key: {different_cache_key}")
    print("✓ Cache key differentiation: PASSED")

    # Test 7: Cleanup
    print("\n" + "-" * 60)
    print("TEST 7: Cache Cleanup")
    print("-" * 60)

    # Store the second result
    output_file2 = Path(tempfile.mktemp(suffix=".png"))
    output_file2.write_text("Another mock converted file")
    cache_service.store_result(
        cache_key=different_cache_key,
        original_filename=test_file.name,
        output_file_path=output_file2,
        output_format="png",
        conversion_options=different_options
    )

    cleanup_stats = cache_service.cleanup_expired()
    print(f"Expired entries removed: {cleanup_stats['expired_removed']}")
    print(f"Corrupted entries removed: {cleanup_stats['corrupted_removed']}")
    print(f"Space freed: {cleanup_stats['space_freed_mb']:.4f} MB")
    print("✓ Cache cleanup: PASSED")

    # Test 8: Clear all
    print("\n" + "-" * 60)
    print("TEST 8: Clear All Cache")
    print("-" * 60)

    cache_service.clear_all()
    cache_info = cache_service.get_cache_info()
    assert cache_info['entry_count'] == 0, "Cache should be empty!"
    print(f"Cache entries after clear: {cache_info['entry_count']}")
    print("✓ Cache clear: PASSED")

    # Cleanup test files
    print("\n" + "-" * 60)
    print("Cleaning up test files...")
    test_file.unlink(missing_ok=True)
    output_file.unlink(missing_ok=True)
    output_file2.unlink(missing_ok=True)

    import shutil
    shutil.rmtree(test_cache_dir, ignore_errors=True)
    print("Test files cleaned up")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! ✓")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_cache_service())
