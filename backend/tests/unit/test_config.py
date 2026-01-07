"""
Unit tests for app configuration settings.

Tests:
- CORS origins parsing (string vs list)
- Settings initialization
- Property methods
"""

import pytest
from unittest.mock import patch


class TestSettingsCorsOrigins:
    """Test Settings.cors_origins property"""

    def test_cors_origins_from_string(self):
        """Test cors_origins property when ALLOWED_ORIGINS is a string"""
        from app.config import Settings

        settings = Settings()
        settings.ALLOWED_ORIGINS = "http://localhost:3000,http://localhost:5173"

        origins = settings.cors_origins
        assert isinstance(origins, list)
        assert len(origins) == 2
        assert "http://localhost:3000" in origins
        assert "http://localhost:5173" in origins

    def test_cors_origins_from_list(self):
        """Test cors_origins property when ALLOWED_ORIGINS is already a list"""
        from app.config import Settings

        settings = Settings()
        # Set ALLOWED_ORIGINS as a list instead of string (for testing flexibility)
        settings.ALLOWED_ORIGINS = ["http://example.com", "http://test.com"]

        origins = settings.cors_origins
        # Should return the list as-is when already a list
        assert isinstance(origins, list)
        assert len(origins) == 2
        assert "http://example.com" in origins
        assert "http://test.com" in origins

    def test_cors_origins_handles_whitespace(self):
        """Test cors_origins strips whitespace from string values"""
        from app.config import Settings

        settings = Settings()
        settings.ALLOWED_ORIGINS = "  http://localhost:3000  ,  http://localhost:5173  "

        origins = settings.cors_origins
        assert len(origins) == 2
        assert "http://localhost:3000" in origins
        assert "http://localhost:5173" in origins
        # Verify no whitespace in results
        assert all(not origin.startswith(" ") and not origin.endswith(" ") for origin in origins)

    def test_cors_origins_filters_empty_strings(self):
        """Test cors_origins filters out empty strings"""
        from app.config import Settings

        settings = Settings()
        settings.ALLOWED_ORIGINS = "http://localhost:3000,,,http://localhost:5173,"

        origins = settings.cors_origins
        assert len(origins) == 2
        assert "" not in origins
