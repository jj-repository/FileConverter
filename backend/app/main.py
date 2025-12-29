from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio

from app.config import settings
from app.routers import image, video, audio, document, batch, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory for uploads/downloads
app.mount("/files", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="files")


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "FileConverter API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "image": "/api/image",
            "video": "/api/video",
            "audio": "/api/audio",
            "document": "/api/document",
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Background task to cleanup old temporary files
async def cleanup_old_files():
    """Background task that runs every hour to cleanup old temporary files"""
    import time
    from pathlib import Path

    while True:
        try:
            current_time = time.time()

            # Cleanup temp directory
            for file_path in settings.TEMP_DIR.glob("*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > settings.TEMP_FILE_LIFETIME:
                        file_path.unlink()

            # Cleanup upload directory
            for file_path in settings.UPLOAD_DIR.glob("*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > settings.TEMP_FILE_LIFETIME:
                        file_path.unlink()

        except Exception as e:
            print(f"Error during cleanup: {e}")

        # Wait 1 hour before next cleanup
        await asyncio.sleep(3600)


# Include routers
app.include_router(image.router, prefix="/api/image", tags=["Image Conversion"])
app.include_router(video.router, prefix="/api/video", tags=["Video Conversion"])
app.include_router(audio.router, prefix="/api/audio", tags=["Audio Conversion"])
app.include_router(document.router, prefix="/api/document", tags=["Document Conversion"])
app.include_router(batch.router, prefix="/api/batch", tags=["Batch Conversion"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
