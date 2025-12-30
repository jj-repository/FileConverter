"""
Cache service for file conversion results.

This service implements a comprehensive caching layer to avoid redundant conversions
by storing and retrieving previously converted files.
"""

import hashlib
import json
import logging
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CacheMetadata:
    """Metadata for a cached conversion result"""
    cache_key: str
    original_filename: str
    output_file: str
    output_format: str
    created_at: float
    expires_at: float
    file_size: int
    conversion_options: Dict[str, Any]

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheMetadata':
        """Create instance from dictionary"""
        return cls(**data)


class CacheService:
    """Service for managing conversion result caching"""

    def __init__(self, cache_dir: Path, expiration_hours: int = 1, max_size_mb: int = 1000):
        """
        Initialize cache service

        Args:
            cache_dir: Directory to store cached files
            expiration_hours: Default cache lifetime in hours
            max_size_mb: Maximum cache size in MB
        """
        self.cache_dir = cache_dir
        self.expiration_hours = expiration_hours
        self.max_size_mb = max_size_mb
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0
        }

    def generate_file_hash(self, file_path: Path) -> str:
        """
        Generate MD5 hash of file content

        Args:
            file_path: Path to file

        Returns:
            MD5 hash as hex string
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error generating file hash for {file_path}: {e}")
            raise

    def generate_options_hash(self, options: Dict[str, Any]) -> str:
        """
        Generate hash of conversion options

        Args:
            options: Conversion options dictionary

        Returns:
            MD5 hash (first 8 chars) of sorted options
        """
        # Sort options for consistent hashing
        options_str = json.dumps(options, sort_keys=True)
        options_hash = hashlib.md5(options_str.encode()).hexdigest()
        return options_hash[:8]

    def generate_cache_key(self, file_path: Path, output_format: str, options: Dict[str, Any]) -> str:
        """
        Generate unique cache key from file hash + output format + options

        Args:
            file_path: Path to input file
            output_format: Target output format
            options: Conversion options

        Returns:
            Cache key string in format: {file_hash}_{output_format}_{options_hash}
        """
        file_hash = self.generate_file_hash(file_path)
        options_hash = self.generate_options_hash(options)
        cache_key = f"{file_hash}_{output_format}_{options_hash}"
        return cache_key

    def get_cache_path(self, cache_key: str) -> Path:
        """
        Get cache directory path for a given cache key

        Args:
            cache_key: Cache key

        Returns:
            Path to cache directory
        """
        return self.cache_dir / cache_key

    def get_metadata_path(self, cache_key: str) -> Path:
        """
        Get metadata file path for a given cache key

        Args:
            cache_key: Cache key

        Returns:
            Path to metadata.json file
        """
        return self.get_cache_path(cache_key) / "metadata.json"

    def read_metadata(self, cache_key: str) -> Optional[CacheMetadata]:
        """
        Read metadata for a cached result

        Args:
            cache_key: Cache key

        Returns:
            CacheMetadata object or None if not found or corrupted
        """
        metadata_path = self.get_metadata_path(cache_key)

        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path, 'r') as f:
                data = json.load(f)
            return CacheMetadata.from_dict(data)
        except Exception as e:
            logger.error(f"Error reading cache metadata for {cache_key}: {e}")
            # Corrupted metadata, clean up
            self._remove_cache_entry(cache_key)
            return None

    def write_metadata(self, metadata: CacheMetadata) -> None:
        """
        Write metadata for a cached result

        Args:
            metadata: CacheMetadata object to write
        """
        cache_path = self.get_cache_path(metadata.cache_key)
        cache_path.mkdir(parents=True, exist_ok=True)

        metadata_path = self.get_metadata_path(metadata.cache_key)

        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error writing cache metadata for {metadata.cache_key}: {e}")
            raise

    def get_cached_result(self, cache_key: str) -> Optional[CacheMetadata]:
        """
        Get cached conversion result if it exists and is not expired

        Args:
            cache_key: Cache key to lookup

        Returns:
            CacheMetadata if cache hit and not expired, None otherwise
        """
        self.stats["total_requests"] += 1

        metadata = self.read_metadata(cache_key)

        if metadata is None:
            self.stats["misses"] += 1
            logger.debug(f"Cache miss: {cache_key}")
            return None

        # Check if expired
        if metadata.is_expired():
            logger.debug(f"Cache expired: {cache_key}")
            self._remove_cache_entry(cache_key)
            self.stats["misses"] += 1
            return None

        # Verify output file exists
        output_file_path = Path(metadata.output_file)
        if not output_file_path.exists():
            logger.warning(f"Cache entry exists but output file missing: {cache_key}")
            self._remove_cache_entry(cache_key)
            self.stats["misses"] += 1
            return None

        self.stats["hits"] += 1
        logger.info(f"Cache hit: {cache_key} (hit rate: {self.get_hit_rate():.2%})")
        return metadata

    def store_result(
        self,
        cache_key: str,
        original_filename: str,
        output_file_path: Path,
        output_format: str,
        conversion_options: Dict[str, Any]
    ) -> None:
        """
        Store conversion result in cache

        Args:
            cache_key: Cache key
            original_filename: Original input filename
            output_file_path: Path to converted output file
            output_format: Output format
            conversion_options: Conversion options used
        """
        try:
            cache_path = self.get_cache_path(cache_key)
            cache_path.mkdir(parents=True, exist_ok=True)

            # Copy output file to cache directory
            cached_file = cache_path / output_file_path.name
            shutil.copy2(output_file_path, cached_file)

            # Create metadata
            file_size = cached_file.stat().st_size
            created_at = time.time()
            expires_at = created_at + (self.expiration_hours * 3600)

            metadata = CacheMetadata(
                cache_key=cache_key,
                original_filename=original_filename,
                output_file=str(cached_file),
                output_format=output_format,
                created_at=created_at,
                expires_at=expires_at,
                file_size=file_size,
                conversion_options=conversion_options
            )

            self.write_metadata(metadata)
            logger.info(f"Cached result: {cache_key} (size: {file_size / 1024:.2f} KB)")

        except Exception as e:
            logger.error(f"Error storing cache result for {cache_key}: {e}")
            # Don't fail conversion if cache storage fails
            try:
                self._remove_cache_entry(cache_key)
            except:
                pass

    def _remove_cache_entry(self, cache_key: str) -> None:
        """
        Remove a cache entry and its files

        Args:
            cache_key: Cache key to remove
        """
        cache_path = self.get_cache_path(cache_key)
        if cache_path.exists():
            try:
                shutil.rmtree(cache_path)
                logger.debug(f"Removed cache entry: {cache_key}")
            except Exception as e:
                logger.error(f"Error removing cache entry {cache_key}: {e}")

    def cleanup_expired(self) -> Dict[str, int]:
        """
        Remove all expired cache entries

        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            "expired_removed": 0,
            "corrupted_removed": 0,
            "space_freed_mb": 0
        }

        for cache_path in self.cache_dir.iterdir():
            if not cache_path.is_dir():
                continue

            cache_key = cache_path.name
            metadata = self.read_metadata(cache_key)

            if metadata is None:
                # Corrupted or missing metadata
                stats["corrupted_removed"] += 1
                size_before = self._get_directory_size(cache_path)
                self._remove_cache_entry(cache_key)
                stats["space_freed_mb"] += size_before / (1024 * 1024)
                continue

            if metadata.is_expired():
                stats["expired_removed"] += 1
                size_before = self._get_directory_size(cache_path)
                self._remove_cache_entry(cache_key)
                stats["space_freed_mb"] += size_before / (1024 * 1024)

        logger.info(
            f"Cache cleanup: {stats['expired_removed']} expired, "
            f"{stats['corrupted_removed']} corrupted, "
            f"{stats['space_freed_mb']:.2f} MB freed"
        )

        return stats

    def cleanup_by_size(self) -> Dict[str, int]:
        """
        Remove oldest cache entries if total cache size exceeds limit

        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            "entries_removed": 0,
            "space_freed_mb": 0
        }

        total_size = self.get_total_cache_size()
        max_size_bytes = self.max_size_mb * 1024 * 1024

        if total_size <= max_size_bytes:
            logger.debug(f"Cache size OK: {total_size / (1024 * 1024):.2f} MB / {self.max_size_mb} MB")
            return stats

        logger.info(f"Cache size exceeded: {total_size / (1024 * 1024):.2f} MB / {self.max_size_mb} MB")

        # Get all cache entries with their metadata
        entries: List[tuple[str, CacheMetadata, int]] = []

        for cache_path in self.cache_dir.iterdir():
            if not cache_path.is_dir():
                continue

            cache_key = cache_path.name
            metadata = self.read_metadata(cache_key)

            if metadata is not None:
                size = self._get_directory_size(cache_path)
                entries.append((cache_key, metadata, size))

        # Sort by creation time (oldest first)
        entries.sort(key=lambda x: x[1].created_at)

        # Remove oldest entries until we're under the limit
        current_size = total_size
        for cache_key, metadata, size in entries:
            if current_size <= max_size_bytes:
                break

            self._remove_cache_entry(cache_key)
            current_size -= size
            stats["entries_removed"] += 1
            stats["space_freed_mb"] += size / (1024 * 1024)

        logger.info(
            f"Size cleanup: {stats['entries_removed']} entries removed, "
            f"{stats['space_freed_mb']:.2f} MB freed"
        )

        return stats

    def cleanup_all(self) -> Dict[str, int]:
        """
        Run all cleanup operations (expired + size-based)

        Returns:
            Combined cleanup statistics
        """
        logger.info("Starting cache cleanup...")

        # First remove expired entries
        expired_stats = self.cleanup_expired()

        # Then check size limit
        size_stats = self.cleanup_by_size()

        combined_stats = {
            "expired_removed": expired_stats["expired_removed"],
            "corrupted_removed": expired_stats["corrupted_removed"],
            "size_limit_removed": size_stats["entries_removed"],
            "total_space_freed_mb": expired_stats["space_freed_mb"] + size_stats["space_freed_mb"]
        }

        logger.info(
            f"Cache cleanup complete: {combined_stats['expired_removed']} expired, "
            f"{combined_stats['corrupted_removed']} corrupted, "
            f"{combined_stats['size_limit_removed']} by size limit, "
            f"{combined_stats['total_space_freed_mb']:.2f} MB total freed"
        )

        return combined_stats

    def _get_directory_size(self, directory: Path) -> int:
        """
        Get total size of directory in bytes

        Args:
            directory: Directory path

        Returns:
            Size in bytes
        """
        total_size = 0
        try:
            for item in directory.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception as e:
            logger.error(f"Error calculating directory size for {directory}: {e}")
        return total_size

    def get_total_cache_size(self) -> int:
        """
        Get total size of cache in bytes

        Returns:
            Total cache size in bytes
        """
        return self._get_directory_size(self.cache_dir)

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cache status

        Returns:
            Dictionary with cache statistics
        """
        total_size = self.get_total_cache_size()
        entry_count = sum(1 for p in self.cache_dir.iterdir() if p.is_dir())

        return {
            "cache_dir": str(self.cache_dir),
            "total_size_mb": total_size / (1024 * 1024),
            "max_size_mb": self.max_size_mb,
            "entry_count": entry_count,
            "expiration_hours": self.expiration_hours,
            "stats": self.stats.copy(),
            "hit_rate": self.get_hit_rate()
        }

    def get_hit_rate(self) -> float:
        """
        Calculate cache hit rate

        Returns:
            Hit rate as decimal (0.0 to 1.0)
        """
        total = self.stats["total_requests"]
        if total == 0:
            return 0.0
        return self.stats["hits"] / total

    def clear_all(self) -> None:
        """
        Remove all cache entries and reset statistics (for testing/maintenance)
        """
        logger.warning("Clearing entire cache...")
        removed = 0

        for cache_path in self.cache_dir.iterdir():
            if cache_path.is_dir():
                self._remove_cache_entry(cache_path.name)
                removed += 1

        # Reset statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0
        }

        logger.info(f"Cleared {removed} cache entries and reset statistics")


# Global cache service instance (will be initialized in main.py)
cache_service: Optional[CacheService] = None


def get_cache_service() -> Optional[CacheService]:
    """Get the global cache service instance"""
    return cache_service


def initialize_cache_service(cache_dir: Path, expiration_hours: int, max_size_mb: int) -> CacheService:
    """
    Initialize the global cache service

    Args:
        cache_dir: Directory to store cached files
        expiration_hours: Default cache lifetime in hours
        max_size_mb: Maximum cache size in MB

    Returns:
        Initialized CacheService instance
    """
    global cache_service
    cache_service = CacheService(
        cache_dir=cache_dir,
        expiration_hours=expiration_hours,
        max_size_mb=max_size_mb
    )
    logger.info(
        f"Cache service initialized: dir={cache_dir}, "
        f"expiration={expiration_hours}h, max_size={max_size_mb}MB"
    )
    return cache_service
