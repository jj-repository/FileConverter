"""Tests for security classes: TrustedProxyValidator, AdminAuthRateLimiter, sanitize_error_message."""

import time
from unittest.mock import MagicMock

from app.middleware.error_handler import sanitize_error_message
from app.utils.websocket_security import AdminAuthRateLimiter, TrustedProxyValidator

# ============================================================================
# TrustedProxyValidator Tests
# ============================================================================


class TestTrustedProxyValidator:
    """Test TrustedProxyValidator IP trust decisions."""

    def test_no_trusted_proxies_configured(self, monkeypatch):
        """With empty config, no IP is trusted."""
        monkeypatch.setattr("app.utils.websocket_security.settings.TRUSTED_PROXIES", "")
        validator = TrustedProxyValidator()
        assert validator.is_trusted_proxy("192.168.1.1") is False

    def test_single_ip_trusted(self, monkeypatch):
        """Single IP in config should be trusted."""
        monkeypatch.setattr(
            "app.utils.websocket_security.settings.TRUSTED_PROXIES", "10.0.0.1"
        )
        validator = TrustedProxyValidator()
        assert validator.is_trusted_proxy("10.0.0.1") is True
        assert validator.is_trusted_proxy("10.0.0.2") is False

    def test_cidr_range_trusted(self, monkeypatch):
        """CIDR range in config should trust all IPs in range."""
        monkeypatch.setattr(
            "app.utils.websocket_security.settings.TRUSTED_PROXIES", "10.0.0.0/24"
        )
        validator = TrustedProxyValidator()
        assert validator.is_trusted_proxy("10.0.0.1") is True
        assert validator.is_trusted_proxy("10.0.0.255") is True
        assert validator.is_trusted_proxy("10.0.1.1") is False

    def test_invalid_proxy_config_skipped(self, monkeypatch):
        """Invalid proxy entry should be skipped without crashing."""
        monkeypatch.setattr(
            "app.utils.websocket_security.settings.TRUSTED_PROXIES",
            "not-an-ip,10.0.0.1",
        )
        validator = TrustedProxyValidator()
        assert validator.is_trusted_proxy("10.0.0.1") is True

    def test_invalid_ip_not_trusted(self, monkeypatch):
        """Invalid IP string should return False."""
        monkeypatch.setattr(
            "app.utils.websocket_security.settings.TRUSTED_PROXIES", "10.0.0.1"
        )
        validator = TrustedProxyValidator()
        assert validator.is_trusted_proxy("not-an-ip") is False

    def test_get_client_ip_direct(self, monkeypatch):
        """Without trusted proxy, return direct client IP."""
        monkeypatch.setattr("app.utils.websocket_security.settings.TRUSTED_PROXIES", "")
        validator = TrustedProxyValidator()
        request = MagicMock()
        request.client.host = "1.2.3.4"
        request.headers = {}
        assert validator.get_client_ip(request) == "1.2.3.4"

    def test_get_client_ip_forwarded_from_trusted(self, monkeypatch):
        """From trusted proxy, respect X-Forwarded-For."""
        monkeypatch.setattr(
            "app.utils.websocket_security.settings.TRUSTED_PROXIES", "10.0.0.1"
        )
        validator = TrustedProxyValidator()
        request = MagicMock()
        request.client.host = "10.0.0.1"
        request.headers = {"X-Forwarded-For": "5.6.7.8, 10.0.0.1"}
        assert validator.get_client_ip(request) == "5.6.7.8"

    def test_get_client_ip_forwarded_from_untrusted(self, monkeypatch):
        """From untrusted source, ignore X-Forwarded-For."""
        monkeypatch.setattr(
            "app.utils.websocket_security.settings.TRUSTED_PROXIES", "10.0.0.1"
        )
        validator = TrustedProxyValidator()
        request = MagicMock()
        request.client.host = "99.99.99.99"
        request.headers = {"X-Forwarded-For": "5.6.7.8"}
        assert validator.get_client_ip(request) == "99.99.99.99"


# ============================================================================
# AdminAuthRateLimiter Tests
# ============================================================================


class TestAdminAuthRateLimiter:
    """Test AdminAuthRateLimiter brute-force protection."""

    def test_no_lockout_initially(self):
        limiter = AdminAuthRateLimiter(max_failures=3, lockout_seconds=60)
        locked, remaining = limiter.is_locked_out("1.2.3.4")
        assert locked is False
        assert remaining is None

    def test_record_failure_increments(self):
        limiter = AdminAuthRateLimiter(max_failures=3, lockout_seconds=60)
        limiter.record_failure("1.2.3.4")
        assert len(limiter.failures["1.2.3.4"]) == 1

    def test_lockout_after_max_failures(self):
        limiter = AdminAuthRateLimiter(max_failures=3, lockout_seconds=60)
        for _ in range(3):
            limiter.record_failure("1.2.3.4")
        locked, remaining = limiter.is_locked_out("1.2.3.4")
        assert locked is True
        assert remaining is not None and remaining > 0

    def test_lockout_expires(self):
        limiter = AdminAuthRateLimiter(max_failures=2, lockout_seconds=1)
        limiter.record_failure("1.2.3.4")
        limiter.record_failure("1.2.3.4")
        locked, _ = limiter.is_locked_out("1.2.3.4")
        assert locked is True
        time.sleep(1.1)
        locked, _ = limiter.is_locked_out("1.2.3.4")
        assert locked is False

    def test_clear_failures(self):
        limiter = AdminAuthRateLimiter(max_failures=3, lockout_seconds=60)
        limiter.record_failure("1.2.3.4")
        limiter.record_failure("1.2.3.4")
        limiter.clear_failures("1.2.3.4")
        assert "1.2.3.4" not in limiter.failures

    def test_reset_clears_all(self):
        limiter = AdminAuthRateLimiter(max_failures=2, lockout_seconds=60)
        limiter.record_failure("1.1.1.1")
        limiter.record_failure("2.2.2.2")
        limiter.reset()
        assert len(limiter.failures) == 0
        assert len(limiter.lockouts) == 0

    def test_different_ips_independent(self):
        limiter = AdminAuthRateLimiter(max_failures=2, lockout_seconds=60)
        limiter.record_failure("1.1.1.1")
        limiter.record_failure("1.1.1.1")
        locked_1, _ = limiter.is_locked_out("1.1.1.1")
        locked_2, _ = limiter.is_locked_out("2.2.2.2")
        assert locked_1 is True
        assert locked_2 is False


# ============================================================================
# sanitize_error_message Tests
# ============================================================================


class TestSanitizeErrorMessage:
    """Test error message sanitization prevents info leakage."""

    def test_strips_unix_paths(self):
        msg = "Error reading /home/user/secret/file.txt"
        result = sanitize_error_message(msg)
        assert "/home/user" not in result
        assert "[path]" in result

    def test_strips_windows_paths(self):
        msg = "Error reading C:\\Users\\Admin\\secrets.txt"
        result = sanitize_error_message(msg)
        assert "C:\\Users" not in result
        assert "[path]" in result

    def test_strips_ip_addresses(self):
        msg = "Connection to 192.168.1.100 failed"
        result = sanitize_error_message(msg)
        assert "192.168.1.100" not in result
        assert "[ip]" in result

    def test_strips_uuids(self):
        msg = "Session a1b2c3d4-e5f6-7890-abcd-ef1234567890 expired"
        result = sanitize_error_message(msg)
        assert "a1b2c3d4-e5f6-7890-abcd-ef1234567890" not in result
        assert "[id]" in result

    def test_empty_message(self):
        assert sanitize_error_message("") == ""

    def test_none_message(self):
        assert sanitize_error_message(None) is None

    def test_safe_message_passes_through(self):
        msg = "Conversion failed: unsupported format"
        result = sanitize_error_message(msg)
        assert "unsupported format" in result
