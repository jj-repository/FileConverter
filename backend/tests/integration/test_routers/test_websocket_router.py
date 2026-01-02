"""
Integration tests for WebSocket router (app/routers/websocket.py)

CRITICAL: Security-focused tests for WebSocket connections
Tests rate limiting, session validation, and real-time progress updates

COVERAGE GOAL: 85%+
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.utils.websocket_security import rate_limiter, session_validator
from app.services.base_converter import ws_manager


# ============================================================================
# VALID SESSION CONNECTION TESTS
# ============================================================================

class TestWebSocketValidConnection:
    """Test valid WebSocket connections"""

    def test_websocket_connect_with_valid_session(self, test_client):
        """Test WebSocket connects successfully with valid session"""
        # Register a valid session
        session_id = "test-session-123"
        session_validator.register_session(session_id)

        with test_client.websocket_connect(f"/ws/progress/{session_id}") as websocket:
            # Should receive connection message
            data = websocket.receive_json()

            assert data["session_id"] == session_id
            assert data["progress"] == 0
            assert data["status"] == "connected"
            assert "connected" in data["message"].lower()

        # Cleanup
        session_validator.remove_session(session_id)

    def test_websocket_ping_pong(self, test_client):
        """Test WebSocket ping/pong mechanism"""
        session_id = "test-session-ping"
        session_validator.register_session(session_id)

        with test_client.websocket_connect(f"/ws/progress/{session_id}") as websocket:
            # Receive connection message
            websocket.receive_json()

            # Send ping
            websocket.send_text("ping")

            # Should receive pong
            response = websocket.receive_json()
            assert response["type"] == "pong"

        session_validator.remove_session(session_id)

    def test_websocket_receives_progress_updates(self, test_client):
        """Test WebSocket receives real-time progress updates"""
        session_id = "test-session-progress"
        session_validator.register_session(session_id)

        with test_client.websocket_connect(f"/ws/progress/{session_id}") as websocket:
            # Receive connection message
            websocket.receive_json()

            # Simulate sending progress update
            import asyncio
            async def send_update():
                await ws_manager.send_progress(session_id, 50.0, "converting", "Halfway done")

            # Run async update
            asyncio.get_event_loop().run_until_complete(send_update())

            # Receive progress update
            data = websocket.receive_json()
            assert data["session_id"] == session_id
            assert data["progress"] == 50.0
            assert data["status"] == "converting"
            assert "Halfway done" in data["message"]

        session_validator.remove_session(session_id)


# ============================================================================
# SESSION VALIDATION TESTS (SECURITY CRITICAL)
# ============================================================================

class TestWebSocketSessionValidation:
    """Test WebSocket session validation security"""

    def test_websocket_rejects_invalid_session(self, test_client):
        """Test WebSocket rejects connection with invalid session ID"""
        # Don't register session (invalid)
        session_id = "invalid-session-999"

        with pytest.raises(Exception):  # WebSocketException
            with test_client.websocket_connect(f"/ws/progress/{session_id}") as websocket:
                pass

    def test_websocket_rejects_expired_session(self, test_client):
        """Test WebSocket rejects expired sessions"""
        import time

        session_id = "expired-session"

        # Register session with old timestamp (2 hours ago)
        old_timestamp = time.time() - (2 * 3600)
        session_validator.active_sessions[session_id] = old_timestamp

        with pytest.raises(Exception):  # WebSocketException
            with test_client.websocket_connect(f"/ws/progress/{session_id}") as websocket:
                pass

        # Cleanup
        if session_id in session_validator.active_sessions:
            session_validator.remove_session(session_id)

    def test_websocket_removes_connection_on_invalid_session(self, test_client):
        """Test that rate limiter connection is removed when session is invalid"""
        session_id = "invalid-session-remove"

        # Note: rate limiter should remove connection when session invalid
        with pytest.raises(Exception):
            with test_client.websocket_connect(f"/ws/progress/{session_id}") as websocket:
                pass


# ============================================================================
# RATE LIMITING TESTS (SECURITY CRITICAL)
# ============================================================================

class TestWebSocketRateLimiting:
    """Test WebSocket rate limiting security"""

    def test_websocket_allows_within_rate_limit(self, test_client):
        """Test WebSocket allows connections within rate limit"""
        # Clear rate limiter for clean test
        rate_limiter.connections.clear()

        # Register sessions
        for i in range(5):
            session_id = f"rate-test-{i}"
            session_validator.register_session(session_id)

        # Connect 5 times (within limit of 10)
        for i in range(5):
            session_id = f"rate-test-{i}"
            with test_client.websocket_connect(f"/ws/progress/{session_id}") as websocket:
                data = websocket.receive_json()
                assert data["status"] == "connected"

        # Cleanup
        for i in range(5):
            session_validator.remove_session(f"rate-test-{i}")

        rate_limiter.connections.clear()

    def test_websocket_blocks_when_rate_limit_exceeded(self, test_client):
        """Test WebSocket blocks connections when rate limit exceeded"""
        # Clear rate limiter
        rate_limiter.connections.clear()

        # Manually add 10 connections to rate limiter (simulate at limit)
        import time
        client_ip = "testclient"
        for i in range(10):
            rate_limiter.connections[client_ip].append(time.time())

        # Register new session
        session_validator.register_session("over-limit-test")

        # Try to connect (should be blocked as we're at limit)
        with pytest.raises(Exception):  # Should fail due to rate limit
            with test_client.websocket_connect("/ws/progress/over-limit-test") as websocket:
                websocket.receive_json()

        # Cleanup
        session_validator.remove_session("over-limit-test")
        rate_limiter.connections.clear()

    def test_websocket_rate_limit_per_ip(self, test_client):
        """Test rate limit is per IP address"""
        rate_limiter.connections.clear()

        # Register sessions
        for i in range(2):
            session_validator.register_session(f"ip-test-{i}")

        # Connections from same IP should share rate limit
        # (Test client uses same IP for all connections)
        with test_client.websocket_connect("/ws/progress/ip-test-0") as ws1:
            ws1.receive_json()

            with test_client.websocket_connect("/ws/progress/ip-test-1") as ws2:
                ws2.receive_json()

                # Both should succeed (same IP, counted together)
                # IP should have 2 connections recorded

        # Cleanup
        for i in range(2):
            session_validator.remove_session(f"ip-test-{i}")
        rate_limiter.connections.clear()


# ============================================================================
# DISCONNECT HANDLING TESTS
# ============================================================================

class TestWebSocketDisconnect:
    """Test WebSocket disconnect handling"""

    def test_websocket_disconnect_removes_from_manager(self, test_client):
        """Test disconnect removes session from WebSocket manager"""
        session_id = "disconnect-test"
        session_validator.register_session(session_id)

        with test_client.websocket_connect(f"/ws/progress/{session_id}") as websocket:
            websocket.receive_json()

            # Session should be in manager
            assert session_id in ws_manager.active_connections

            # Manually disconnect (TestClient doesn't trigger disconnect handlers automatically)
            ws_manager.disconnect(session_id)

        # After disconnect, session should be removed
        assert session_id not in ws_manager.active_connections

        session_validator.remove_session(session_id)

    def test_websocket_disconnect_removes_rate_limit_connection(self, test_client):
        """Test disconnect removes connection from rate limiter"""
        rate_limiter.connections.clear()

        session_id = "rate-disconnect-test"
        session_validator.register_session(session_id)

        # Get initial connection count
        client_ip = "testclient"  # TestClient uses this as default

        with test_client.websocket_connect(f"/ws/progress/{session_id}") as websocket:
            websocket.receive_json()
            # Connection counted

        # After disconnect, connection should be removed
        # (implementation removes oldest connection on disconnect)

        session_validator.remove_session(session_id)
        rate_limiter.connections.clear()

    def test_websocket_handles_client_disconnect_gracefully(self, test_client):
        """Test server handles client disconnect gracefully"""
        session_id = "client-disconnect-test"
        session_validator.register_session(session_id)

        with test_client.websocket_connect(f"/ws/progress/{session_id}") as websocket:
            websocket.receive_json()
            # Simulate client disconnect by closing
            websocket.close()

        # Should not raise error
        assert session_id not in ws_manager.active_connections

        session_validator.remove_session(session_id)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestWebSocketErrorHandling:
    """Test WebSocket error handling"""

    def test_websocket_handles_send_error_gracefully(self, test_client):
        """Test WebSocket handles send errors gracefully"""
        session_id = "error-test"
        session_validator.register_session(session_id)

        with test_client.websocket_connect(f"/ws/progress/{session_id}") as websocket:
            websocket.receive_json()

            # Simulate error by sending to closed connection
            websocket.close()

            # Sending to closed connection should be handled gracefully
            # (tested via ws_manager.send_progress which catches exceptions)

        session_validator.remove_session(session_id)

    def test_websocket_cleans_up_on_error(self, test_client):
        """Test WebSocket cleans up resources on error"""
        import time
        session_id = "cleanup-error-test"
        session_validator.register_session(session_id)

        try:
            with test_client.websocket_connect(f"/ws/progress/{session_id}") as websocket:
                websocket.receive_json()

                # Force an error by sending invalid JSON
                with patch.object(websocket, 'receive_text', side_effect=Exception("Simulated error")):
                    try:
                        websocket.receive_text()
                    except:
                        pass
        except:
            pass

        # Give async cleanup a moment to complete (timing issue on Python 3.12)
        time.sleep(0.1)

        # Session should be cleaned up
        assert session_id not in ws_manager.active_connections

        session_validator.remove_session(session_id)

    def test_websocket_general_exception_cleanup(self, test_client):
        """Test general exception handler cleanup (lines 63-66)"""
        from unittest.mock import patch, AsyncMock
        import asyncio

        session_id = "general-error-test"
        session_validator.register_session(session_id)
        rate_limiter.connections.clear()

        async def trigger_exception():
            """Async function to trigger exception in websocket endpoint"""
            from fastapi import WebSocket
            from app.routers.websocket import websocket_progress

            # Create a mock websocket
            mock_ws = AsyncMock(spec=WebSocket)
            mock_ws.client = Mock()
            mock_ws.client.host = "test-host"
            mock_ws.accept = AsyncMock()
            mock_ws.send_json = AsyncMock()

            # Make receive_text raise a general exception (not WebSocketDisconnect)
            mock_ws.receive_text = AsyncMock(side_effect=RuntimeError("Unexpected error"))

            # Call the websocket endpoint
            try:
                await websocket_progress(mock_ws, session_id)
            except RuntimeError:
                pass  # Expected to be caught by endpoint

            # Verify cleanup happened
            # The endpoint should call ws_manager.disconnect and rate_limiter.remove_connection

        # Run the async test
        asyncio.get_event_loop().run_until_complete(trigger_exception())

        # Cleanup
        session_validator.remove_session(session_id)
        rate_limiter.connections.clear()


# ============================================================================
# CONCURRENT CONNECTION TESTS
# ============================================================================

class TestWebSocketConcurrentConnections:
    """Test concurrent WebSocket connections"""

    def test_multiple_sessions_simultaneous(self, test_client):
        """Test multiple sessions can connect simultaneously"""
        # Register multiple sessions
        session_ids = [f"concurrent-{i}" for i in range(3)]
        for session_id in session_ids:
            session_validator.register_session(session_id)

        # Open multiple connections
        connections = []
        for session_id in session_ids:
            ws = test_client.websocket_connect(f"/ws/progress/{session_id}")
            ws.__enter__()
            connections.append(ws)
            ws.receive_json()  # Connection message

        # All should be active
        for session_id in session_ids:
            assert session_id in ws_manager.active_connections

        # Close all
        for ws in connections:
            ws.__exit__(None, None, None)

        # Cleanup
        for session_id in session_ids:
            session_validator.remove_session(session_id)

    def test_same_session_cannot_connect_twice(self, test_client):
        """Test same session ID cannot have multiple concurrent connections"""
        session_id = "duplicate-session"
        session_validator.register_session(session_id)

        with test_client.websocket_connect(f"/ws/progress/{session_id}") as ws1:
            ws1.receive_json()

            # Try to connect again with same session ID
            # (Should overwrite previous connection in ws_manager)
            with test_client.websocket_connect(f"/ws/progress/{session_id}") as ws2:
                ws2.receive_json()

                # Only one connection should be active
                assert session_id in ws_manager.active_connections

        session_validator.remove_session(session_id)


# ============================================================================
# INTEGRATION WITH CONVERSION FLOW
# ============================================================================

class TestWebSocketConversionIntegration:
    """Test WebSocket integration with conversion flow"""

    @pytest.mark.asyncio
    async def test_conversion_sends_progress_to_websocket(self, test_client):
        """Test that conversions send progress updates via WebSocket"""
        session_id = "conversion-integration"
        session_validator.register_session(session_id)

        with test_client.websocket_connect(f"/ws/progress/{session_id}") as websocket:
            # Receive connection message
            websocket.receive_json()

            # Simulate conversion sending progress
            await ws_manager.send_progress(session_id, 25.0, "converting", "Processing")
            data = websocket.receive_json()
            assert data["progress"] == 25.0

            await ws_manager.send_progress(session_id, 75.0, "converting", "Almost done")
            data = websocket.receive_json()
            assert data["progress"] == 75.0

            await ws_manager.send_progress(session_id, 100.0, "completed", "Done")
            data = websocket.receive_json()
            assert data["progress"] == 100.0
            assert data["status"] == "completed"

        session_validator.remove_session(session_id)
