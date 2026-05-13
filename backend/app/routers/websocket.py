import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket_manager import ws_manager
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

    # Validate origin to prevent cross-site WebSocket hijacking.
    # Allowed callers:
    #   - Browser dev server / API host (http://localhost, http://127.0.0.1).
    #   - Production electron renderer: Chromium emits Origin: null for the
    #     file:// scheme.
    #   - Any non-http(s) scheme (file://, app://, asar://): not reachable by
    #     a remote attacker, so safe to accept.
    # An empty origin is also allowed (some clients omit the header).
    origin = websocket.headers.get("origin", "")
    logger.info("WebSocket handshake origin=%r session=%s", origin, session_id)
    origin_ok = (
        not origin
        or origin == "null"
        or origin.startswith(("http://localhost", "http://127.0.0.1"))
        or not origin.startswith(("http://", "https://"))
    )
    if not origin_ok:
        await websocket.close(code=1008, reason="Invalid origin")
        logger.warning("WebSocket connection denied (origin %r): %s", origin, session_id)
        rate_limiter.remove_connection(client_ip)
        return
    await websocket.accept()
    await ws_manager.connect(session_id, websocket)

    try:
        # Don't send a synthetic "pending" status on connect: when the WS
        # handshake races with the convert HTTP response (the renderer opens
        # the WS as soon as it learns the session_id, but conversion may
        # already be complete), the frontend's status is already
        # `completed`. Pushing "pending" here downgrades the UI back to a
        # progress-bar state with no further events incoming, leaving the
        # download button hidden permanently.

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
