from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging

from app.services.base_converter import ws_manager
from app.utils.websocket_security import rate_limiter, session_validator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/progress/{session_id}")
async def websocket_progress(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time conversion progress updates

    Connect to: ws://localhost:8000/ws/progress/{session_id}

    Security features:
    - Session validation: Only valid session IDs can connect
    - Rate limiting: Maximum 10 connections per IP per minute
    """
    # Get client IP address
    client_ip = websocket.client.host if websocket.client else "unknown"

    # Check rate limit
    is_allowed, rate_limit_reason = rate_limiter.is_allowed(client_ip)
    if not is_allowed:
        await websocket.close(code=1008, reason=rate_limit_reason)
        logger.warning(f"WebSocket connection denied (rate limit): {client_ip}")
        return

    # Validate session ID
    is_valid, validation_reason = session_validator.is_valid_session(session_id)
    if not is_valid:
        await websocket.close(code=1008, reason=validation_reason)
        logger.warning(f"WebSocket connection denied (invalid session): {session_id}")
        rate_limiter.remove_connection(client_ip)
        return

    await websocket.accept()
    await ws_manager.connect(session_id, websocket)

    try:
        # Send initial connection message
        await websocket.send_json({
            "session_id": session_id,
            "progress": 0,
            "status": "connected",
            "message": "WebSocket connected"
        })

        # Keep connection alive
        while True:
            # Wait for messages from client (optional ping/pong)
            data = await websocket.receive_text()

            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        ws_manager.disconnect(session_id)
        rate_limiter.remove_connection(client_ip)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        ws_manager.disconnect(session_id)
        rate_limiter.remove_connection(client_ip)
