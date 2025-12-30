from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


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
