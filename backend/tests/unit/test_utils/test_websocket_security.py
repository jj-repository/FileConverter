"""
Security-critical tests for app/utils/websocket_security.py

These tests focus on WebSocket rate limiting and session validation
to prevent abuse and unauthorized connections.

COVERAGE GOAL: 95%+
"""

import pytest
import time
from unittest.mock import patch

from app.utils.websocket_security import (
    WebSocketRateLimiter,
    SessionValidator,
    rate_limiter,
    session_validator
)


# ============================================================================
# RATE LIMITING TESTS (CRITICAL SECURITY)
# ============================================================================

class TestWebSocketRateLimiter:
    """Test WebSocketRateLimiter - Connection rate limiting"""

    @pytest.mark.security
    @pytest.mark.websocket
    def test_first_connection_allowed(self):
        """Test that first connection from IP is allowed"""
        limiter = WebSocketRateLimiter(max_connections_per_ip=10, time_window=60)

        allowed, reason = limiter.is_allowed("192.168.1.1")

        assert allowed is True
        assert reason == ""

    @pytest.mark.security
    @pytest.mark.websocket
    def test_rate_limit_enforced_at_max(self):
        """Test that 11th connection from same IP is blocked"""
        limiter = WebSocketRateLimiter(max_connections_per_ip=10, time_window=60)

        # Allow first 10 connections
        for i in range(10):
            allowed, _ = limiter.is_allowed("192.168.1.1")
            assert allowed is True

        # 11th connection should be blocked
        allowed, reason = limiter.is_allowed("192.168.1.1")

        assert allowed is False
        assert "Too many connections" in reason
        assert "10" in reason

    @pytest.mark.security
    @pytest.mark.websocket
    def test_rate_limit_resets_after_window(self):
        """Test that rate limit resets after time window expires"""
        limiter = WebSocketRateLimiter(max_connections_per_ip=10, time_window=1)

        # Fill up connections
        for i in range(10):
            limiter.is_allowed("192.168.1.1")

        # Should be blocked immediately
        allowed, _ = limiter.is_allowed("192.168.1.1")
        assert allowed is False

        # Wait for time window to expire
        time.sleep(1.1)

        # Should be allowed again
        allowed, reason = limiter.is_allowed("192.168.1.1")
        assert allowed is True
        assert reason == ""

    @pytest.mark.security
    @pytest.mark.websocket
    def test_different_ips_tracked_independently(self):
        """Test that different IPs are tracked independently"""
        limiter = WebSocketRateLimiter(max_connections_per_ip=10, time_window=60)

        # Fill up IP1
        for i in range(10):
            limiter.is_allowed("192.168.1.1")

        # IP1 should be blocked
        allowed, _ = limiter.is_allowed("192.168.1.1")
        assert allowed is False

        # IP2 should still be allowed
        allowed, reason = limiter.is_allowed("192.168.1.2")
        assert allowed is True
        assert reason == ""

    @pytest.mark.websocket
    def test_connection_count_accuracy(self):
        """Test that connection count is accurately tracked"""
        limiter = WebSocketRateLimiter(max_connections_per_ip=5, time_window=60)

        # Add 3 connections
        for i in range(3):
            limiter.is_allowed("192.168.1.1")

        # Check count (3 connections recorded)
        assert len(limiter.connections["192.168.1.1"]) == 3

        # Add 2 more (total 5)
        for i in range(2):
            limiter.is_allowed("192.168.1.1")

        assert len(limiter.connections["192.168.1.1"]) == 5

    @pytest.mark.websocket
    def test_remove_connection(self):
        """Test that remove_connection decreases count"""
        limiter = WebSocketRateLimiter(max_connections_per_ip=10, time_window=60)

        # Add 5 connections
        for i in range(5):
            limiter.is_allowed("192.168.1.1")

        assert len(limiter.connections["192.168.1.1"]) == 5

        # Remove one connection
        limiter.remove_connection("192.168.1.1")

        # Count should decrease (oldest removed)
        assert len(limiter.connections["192.168.1.1"]) == 4

    @pytest.mark.websocket
    def test_remove_connection_from_empty_ip(self):
        """Test that removing connection from IP with no connections is safe"""
        limiter = WebSocketRateLimiter(max_connections_per_ip=10, time_window=60)

        # Should not raise error
        limiter.remove_connection("192.168.1.99")

        # IP should either not exist or have empty list
        if "192.168.1.99" in limiter.connections:
            assert len(limiter.connections["192.168.1.99"]) == 0

    @pytest.mark.websocket
    def test_cleanup_old_timestamps(self):
        """Test that old timestamps are cleaned up during is_allowed check"""
        limiter = WebSocketRateLimiter(max_connections_per_ip=10, time_window=1)

        # Add old connections
        for i in range(5):
            limiter.is_allowed("192.168.1.1")

        # Wait for them to expire
        time.sleep(1.1)

        # New check should clean up old timestamps
        limiter.is_allowed("192.168.1.1")

        # Only 1 connection should remain (the new one)
        assert len(limiter.connections["192.168.1.1"]) == 1

    @pytest.mark.websocket
    def test_custom_limits(self):
        """Test that custom limits are respected"""
        limiter = WebSocketRateLimiter(max_connections_per_ip=3, time_window=60)

        # Allow 3 connections
        for i in range(3):
            allowed, _ = limiter.is_allowed("192.168.1.1")
            assert allowed is True

        # 4th should be blocked
        allowed, reason = limiter.is_allowed("192.168.1.1")
        assert allowed is False

    @pytest.mark.websocket
    def test_global_rate_limiter_instance(self):
        """Test that global rate_limiter instance works"""
        # The global instance should exist and have correct defaults
        assert rate_limiter.max_connections_per_ip == 10
        assert rate_limiter.time_window == 60


# ============================================================================
# SESSION VALIDATION TESTS (CRITICAL SECURITY)
# ============================================================================

class TestSessionValidator:
    """Test SessionValidator - Session ID validation"""

    @pytest.mark.security
    @pytest.mark.websocket
    def test_register_session_creates_entry(self):
        """Test that registering a session creates an entry"""
        validator = SessionValidator()

        validator.register_session("test-session-123")

        assert "test-session-123" in validator.active_sessions
        assert isinstance(validator.active_sessions["test-session-123"], float)

    @pytest.mark.security
    @pytest.mark.websocket
    def test_valid_session_accepted(self):
        """Test that valid session passes validation"""
        validator = SessionValidator()

        validator.register_session("test-session-123")

        is_valid, reason = validator.is_valid_session("test-session-123")

        assert is_valid is True
        assert reason == ""

    @pytest.mark.security
    @pytest.mark.websocket
    def test_invalid_session_rejected(self):
        """Test that unknown session ID is rejected"""
        validator = SessionValidator()

        is_valid, reason = validator.is_valid_session("unknown-session-999")

        assert is_valid is False
        assert "Invalid or expired" in reason

    @pytest.mark.security
    @pytest.mark.websocket
    def test_expired_session_rejected(self):
        """Test that session older than 1 hour is rejected"""
        validator = SessionValidator()

        # Register session with old timestamp (2 hours ago)
        old_timestamp = time.time() - (2 * 3600)
        validator.active_sessions["old-session"] = old_timestamp

        # Should be rejected and cleaned up
        is_valid, reason = validator.is_valid_session("old-session")

        assert is_valid is False
        assert "old-session" not in validator.active_sessions

    @pytest.mark.websocket
    def test_session_timeout_configurable(self):
        """Test that session timeout is set correctly"""
        validator = SessionValidator()

        assert validator.session_timeout == 3600  # 1 hour in seconds

    @pytest.mark.websocket
    def test_remove_session(self):
        """Test that remove_session deletes session"""
        validator = SessionValidator()

        validator.register_session("test-session-123")
        assert "test-session-123" in validator.active_sessions

        validator.remove_session("test-session-123")

        assert "test-session-123" not in validator.active_sessions

    @pytest.mark.websocket
    def test_remove_nonexistent_session(self):
        """Test that removing nonexistent session is safe"""
        validator = SessionValidator()

        # Should not raise error
        validator.remove_session("nonexistent-session")

    @pytest.mark.websocket
    def test_cleanup_multiple_expired_sessions(self):
        """Test that multiple expired sessions are cleaned up"""
        validator = SessionValidator()

        # Add expired sessions
        old_timestamp = time.time() - (2 * 3600)
        validator.active_sessions["expired-1"] = old_timestamp
        validator.active_sessions["expired-2"] = old_timestamp
        validator.active_sessions["expired-3"] = old_timestamp

        # Add valid session
        validator.register_session("valid-session")

        # Trigger cleanup
        validator.is_valid_session("valid-session")

        # Expired sessions should be gone
        assert "expired-1" not in validator.active_sessions
        assert "expired-2" not in validator.active_sessions
        assert "expired-3" not in validator.active_sessions

        # Valid session should remain
        assert "valid-session" in validator.active_sessions

    @pytest.mark.websocket
    def test_session_timestamp_is_current(self):
        """Test that registered session has current timestamp"""
        validator = SessionValidator()

        before = time.time()
        validator.register_session("test-session")
        after = time.time()

        session_time = validator.active_sessions["test-session"]

        assert before <= session_time <= after

    @pytest.mark.websocket
    def test_session_not_expired_within_timeout(self):
        """Test that session is valid within timeout period"""
        validator = SessionValidator()
        validator.session_timeout = 10  # 10 seconds for testing

        # Register session
        validator.register_session("test-session")

        # Wait less than timeout
        time.sleep(0.5)

        # Should still be valid
        is_valid, _ = validator.is_valid_session("test-session")
        assert is_valid is True

    @pytest.mark.websocket
    def test_global_session_validator_instance(self):
        """Test that global session_validator instance works"""
        # The global instance should exist
        assert session_validator.session_timeout == 3600

    @pytest.mark.websocket
    def test_multiple_sessions_independent(self):
        """Test that multiple sessions are tracked independently"""
        validator = SessionValidator()

        validator.register_session("session-1")
        validator.register_session("session-2")
        validator.register_session("session-3")

        # All should be valid
        assert validator.is_valid_session("session-1")[0] is True
        assert validator.is_valid_session("session-2")[0] is True
        assert validator.is_valid_session("session-3")[0] is True

        # Remove one
        validator.remove_session("session-2")

        # Others should still be valid
        assert validator.is_valid_session("session-1")[0] is True
        assert validator.is_valid_session("session-3")[0] is True
        assert validator.is_valid_session("session-2")[0] is False


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestRateLimiterSessionValidatorIntegration:
    """Test integration between rate limiter and session validator"""

    @pytest.mark.security
    @pytest.mark.websocket
    def test_rate_limited_ip_can_connect_with_valid_session(self):
        """Test that rate limiting and session validation work together"""
        limiter = WebSocketRateLimiter(max_connections_per_ip=2, time_window=60)
        validator = SessionValidator()

        # Register sessions
        validator.register_session("session-1")
        validator.register_session("session-2")
        validator.register_session("session-3")

        # IP connects twice (allowed)
        assert limiter.is_allowed("192.168.1.1")[0] is True
        assert limiter.is_allowed("192.168.1.1")[0] is True

        # 3rd connection rate-limited
        assert limiter.is_allowed("192.168.1.1")[0] is False

        # But sessions are still valid (independent systems)
        assert validator.is_valid_session("session-1")[0] is True
        assert validator.is_valid_session("session-2")[0] is True
        assert validator.is_valid_session("session-3")[0] is True

    @pytest.mark.websocket
    def test_session_lifecycle_with_rate_limiting(self):
        """Test realistic session lifecycle with rate limiting"""
        limiter = WebSocketRateLimiter(max_connections_per_ip=10, time_window=60)
        validator = SessionValidator()

        # User starts conversion (registers session)
        session_id = "conversion-abc123"
        validator.register_session(session_id)

        # WebSocket connects (rate limit check)
        allowed, _ = limiter.is_allowed("192.168.1.1")
        assert allowed is True

        # Session validation
        is_valid, _ = validator.is_valid_session(session_id)
        assert is_valid is True

        # Conversion completes (cleanup)
        validator.remove_session(session_id)
        limiter.remove_connection("192.168.1.1")

        # Session no longer valid
        assert validator.is_valid_session(session_id)[0] is False
