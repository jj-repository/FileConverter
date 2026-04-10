"""WebSocket connection manager for progress updates."""

import logging
from typing import Any, Dict

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

    async def send_progress(
        self, session_id: str, progress: float, status: str, message: str
    ):
        """Send progress update to specific session"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(
                    {
                        "type": "progress",
                        "session_id": session_id,
                        "progress": progress,
                        "status": status,
                        "message": message,
                    }
                )
            except Exception as e:
                logger.error(f"Error sending progress update: {e}")
                self.disconnect(session_id)


# Global WebSocket manager instance
ws_manager = WebSocketManager()
