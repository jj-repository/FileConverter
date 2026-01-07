from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging

from app.config import settings, CACHE_DIR


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Prevent caching of sensitive data
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"

        # Content Security Policy - restrict resource loading
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"

        # Permissions Policy - disable unnecessary browser features
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


from app.routers import image, video, audio, document, data, archive, spreadsheet, subtitle, ebook, font, batch, websocket, cache, version
from app.middleware.error_handler import register_exception_handlers
from app.services.cache_service import initialize_cache_service, get_cache_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize cache service
    if settings.CACHE_ENABLED:
        logger.info("Initializing cache service...")
        initialize_cache_service(
            cache_dir=CACHE_DIR,
            expiration_hours=settings.CACHE_EXPIRATION_HOURS,
            max_size_mb=settings.CACHE_MAX_SIZE_MB
        )

        # Clean up cache on startup
        cache_service = get_cache_service()
        if cache_service:
            logger.info("Running cache cleanup on startup...")
            cleanup_stats = cache_service.cleanup_all()
            logger.info(f"Cache cleanup stats: {cleanup_stats}")

    # Startup: Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_old_files())
    yield
    # Shutdown: Cancel cleanup task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="FileConverter API",
    description="A modern file conversion API supporting images, videos, audio, and documents",
    version="1.1.1",
    lifespan=lifespan,
)

# Register exception handlers
register_exception_handlers(app)

# Security headers middleware (must be added first to wrap all responses)
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware - restrict methods and headers for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],  # Only needed methods
    allow_headers=["Content-Type", "Authorization", "X-Admin-Key", "X-Requested-With"],
)

# Mount static files directory for uploads/downloads
app.mount("/files", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="files")


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "FileConverter API",
        "version": "1.1.1",
        "endpoints": {
            "docs": "/docs",
            "image": "/api/image",
            "video": "/api/video",
            "audio": "/api/audio",
            "document": "/api/document",
            "data": "/api/data",
            "archive": "/api/archive",
            "spreadsheet": "/api/spreadsheet",
            "subtitle": "/api/subtitle",
            "ebook": "/api/ebook",
            "font": "/api/font",
            "cache": "/api/cache",
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Background task to cleanup old temporary files
async def cleanup_old_files():
    """Background task that runs every hour to cleanup old temporary files and cache"""
    import time
    from pathlib import Path

    def _sync_cleanup_directory(directory: Path, lifetime: float) -> None:
        """Synchronous helper for file cleanup - runs in thread pool"""
        current_time = time.time()
        try:
            for file_path in directory.glob("*"):
                try:
                    if file_path.is_file():
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > lifetime:
                            file_path.unlink()
                except (OSError, PermissionError) as e:
                    logger.warning(f"Failed to cleanup file {file_path}: {e}")
        except (OSError, PermissionError) as e:
            logger.warning(f"Failed to scan directory {directory}: {e}")

    while True:
        try:
            # Cleanup temp directory (run in thread to avoid blocking event loop)
            await asyncio.to_thread(
                _sync_cleanup_directory,
                settings.TEMP_DIR,
                settings.TEMP_FILE_LIFETIME
            )

            # Cleanup upload directory (excluding cache directory)
            await asyncio.to_thread(
                _sync_cleanup_directory,
                settings.UPLOAD_DIR,
                settings.TEMP_FILE_LIFETIME
            )

            # Cleanup cache (also blocking I/O, run in thread)
            if settings.CACHE_ENABLED:
                cache_service = get_cache_service()
                if cache_service:
                    logger.debug("Running periodic cache cleanup...")
                    cleanup_stats = await asyncio.to_thread(cache_service.cleanup_all)
                    if cleanup_stats['expired_removed'] > 0 or cleanup_stats['size_limit_removed'] > 0:
                        logger.info(f"Periodic cache cleanup: {cleanup_stats}")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

        # Wait 1 hour before next cleanup
        await asyncio.sleep(3600)


# Include routers
app.include_router(image.router, prefix="/api/image", tags=["Image Conversion"])
app.include_router(video.router, prefix="/api/video", tags=["Video Conversion"])
app.include_router(audio.router, prefix="/api/audio", tags=["Audio Conversion"])
app.include_router(document.router, prefix="/api/document", tags=["Document Conversion"])
app.include_router(data.router, prefix="/api/data", tags=["Data Conversion"])
app.include_router(archive.router, prefix="/api/archive", tags=["Archive Conversion"])
app.include_router(spreadsheet.router, prefix="/api/spreadsheet", tags=["Spreadsheet Conversion"])
app.include_router(subtitle.router, prefix="/api/subtitle", tags=["Subtitle Conversion"])
app.include_router(ebook.router, prefix="/api/ebook", tags=["eBook Conversion"])
app.include_router(font.router, prefix="/api/font", tags=["Font Conversion"])
app.include_router(batch.router, prefix="/api/batch", tags=["Batch Conversion"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
app.include_router(cache.router, prefix="/api/cache", tags=["Cache Management"])
app.include_router(version.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
