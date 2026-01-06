from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
import logging
import shutil
import time

logger = logging.getLogger(__name__)

# Global lock for cache file operations to prevent race conditions
_cache_locks: Dict[str, tuple[asyncio.Lock, float]] = {}  # cache_key -> (lock, last_used_timestamp)
_cache_locks_lock = asyncio.Lock()
_CACHE_LOCK_MAX_AGE = 300  # Remove unused locks after 5 minutes
_CACHE_LOCK_MAX_SIZE = 1000  # Maximum number of locks to keep


async def _cleanup_stale_locks():
    """Remove locks that haven't been used recently"""
    current_time = time.time()
    stale_keys = []

    for key, (lock, last_used) in _cache_locks.items():
        # Only remove if lock is not currently held and is old enough
        if not lock.locked() and (current_time - last_used) > _CACHE_LOCK_MAX_AGE:
            stale_keys.append(key)

    for key in stale_keys:
        if key in _cache_locks and not _cache_locks[key][0].locked():
            del _cache_locks[key]

    if stale_keys:
        logger.debug(f"Cleaned up {len(stale_keys)} stale cache locks")


class WebSocketManager:
    """Manager for WebSocket connections and progress updates"""

    def __init__(self):
        self.active_connections: Dict[str, Any] = {}

    async def connect(self, session_id: str, websocket):
        """Connect a new WebSocket"""
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        """Disconnect a WebSocket"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_progress(self, session_id: str, progress: float, status: str, message: str):
        """Send progress update to specific session"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json({
                    "session_id": session_id,
                    "progress": progress,
                    "status": status,
                    "message": message,
                })
            except Exception as e:
                logger.error(f"Error sending progress update: {e}")
                self.disconnect(session_id)


# Global WebSocket manager instance
ws_manager = WebSocketManager()


class BaseConverter(ABC):
    """Abstract base class for all file converters"""

    def __init__(self, websocket_manager: Optional[WebSocketManager] = None):
        self.websocket_manager = websocket_manager or ws_manager
        self._cache_enabled = True  # Can be disabled per converter if needed

    async def convert_with_cache(
        self,
        input_path: Path,
        output_format: str,
        options: Dict[str, Any],
        session_id: str
    ) -> Path:
        """
        Convert file to target format with caching support

        This method wraps the actual convert() implementation with cache logic.
        It checks cache before conversion and stores results after conversion.

        Args:
            input_path: Path to input file
            output_format: Target output format
            options: Conversion options (quality, resolution, etc.)
            session_id: Unique session ID for progress tracking

        Returns:
            Path to converted file
        """
        from app.services.cache_service import get_cache_service
        from app.config import settings

        cache_service = get_cache_service()

        # If cache is disabled or not available, proceed with normal conversion
        if not settings.CACHE_ENABLED or not self._cache_enabled or cache_service is None:
            return await self.convert(input_path, output_format, options, session_id)

        try:
            # Generate cache key
            cache_key = cache_service.generate_cache_key(input_path, output_format, options)
            logger.debug(f"Cache key generated: {cache_key}")

            # Check cache
            cached_result = cache_service.get_cached_result(cache_key)

            if cached_result is not None:
                # Cache hit - return cached result
                logger.info(f"Cache hit for {cache_key} (session: {session_id})")
                await self.send_progress(session_id, 100, "completed", "Retrieved from cache")

                # Copy cached file to output location with lock to prevent race conditions
                cached_file = Path(cached_result.output_file)
                output_path = settings.UPLOAD_DIR / cached_file.name

                # If cached file and output path are different, copy it
                if cached_file != output_path:
                    # Get or create lock for this cache file atomically
                    async with _cache_locks_lock:
                        # Cleanup stale locks if we have too many
                        if len(_cache_locks) > _CACHE_LOCK_MAX_SIZE:
                            await _cleanup_stale_locks()

                        current_time = time.time()
                        if cache_key not in _cache_locks:
                            _cache_locks[cache_key] = (asyncio.Lock(), current_time)
                        else:
                            # Update last used timestamp
                            _cache_locks[cache_key] = (_cache_locks[cache_key][0], current_time)
                        file_lock = _cache_locks[cache_key][0]

                    # Use file-specific lock to prevent concurrent copies
                    async with file_lock:
                        # Double-check file still exists before copying
                        if cached_file.exists():
                            await asyncio.to_thread(shutil.copy2, cached_file, output_path)
                        else:
                            # Cached file was deleted, need to reconvert
                            logger.warning(f"Cached file {cached_file} no longer exists, reconverting")
                            return await self.convert(input_path, output_format, options, session_id)

                return output_path

            # Cache miss - perform conversion
            logger.debug(f"Cache miss for {cache_key} (session: {session_id})")

            # Perform actual conversion
            output_path = await self.convert(input_path, output_format, options, session_id)

            # Store result in cache
            try:
                cache_service.store_result(
                    cache_key=cache_key,
                    original_filename=input_path.name,
                    output_file_path=output_path,
                    output_format=output_format,
                    conversion_options=options
                )
                logger.debug(f"Cached conversion result: {cache_key}")
            except Exception as cache_error:
                # Log error but don't fail conversion if cache storage fails
                logger.error(f"Failed to cache result for {cache_key}: {cache_error}")

            return output_path

        except Exception as e:
            # If any cache operation fails, fall back to normal conversion
            logger.error(f"Cache operation failed, falling back to normal conversion: {e}")
            return await self.convert(input_path, output_format, options, session_id)

    @abstractmethod
    async def convert(
        self,
        input_path: Path,
        output_format: str,
        options: Dict[str, Any],
        session_id: str
    ) -> Path:
        """
        Convert file to target format

        This is the actual conversion implementation that should be overridden
        by subclasses. Use convert_with_cache() instead of calling this directly
        to benefit from caching.

        Args:
            input_path: Path to input file
            output_format: Target output format
            options: Conversion options (quality, resolution, etc.)
            session_id: Unique session ID for progress tracking

        Returns:
            Path to converted file
        """
        pass

    @abstractmethod
    async def get_supported_formats(self) -> Dict[str, list]:
        """
        Get supported input and output formats

        Returns:
            Dictionary with 'input' and 'output' format lists
        """
        pass

    async def send_progress(
        self,
        session_id: str,
        progress: float,
        status: str = "converting",
        message: str = ""
    ):
        """Send progress update via WebSocket"""
        if self.websocket_manager:
            await self.websocket_manager.send_progress(
                session_id=session_id,
                progress=progress,
                status=status,
                message=message
            )

    def validate_format(self, input_format: str, output_format: str, supported_formats: Dict[str, list]) -> bool:
        """Validate that input and output formats are supported"""
        return (
            input_format in supported_formats.get("input", []) and
            output_format in supported_formats.get("output", [])
        )
