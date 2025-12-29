from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.base_converter import ws_manager


router = APIRouter()


@router.websocket("/progress/{session_id}")
async def websocket_progress(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time conversion progress updates

    Connect to: ws://localhost:8000/ws/progress/{session_id}
    """
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
    except Exception as e:
        print(f"WebSocket error for session {session_id}: {e}")
        ws_manager.disconnect(session_id)
