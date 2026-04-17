"""Integration tests for version router endpoints."""

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest
from app import __version__ as APP_VERSION
from app.main import app
from app.routers.version import _version_newer
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ── _version_newer unit tests ────────────────────────────────────────────────


class TestVersionNewer:
    def test_newer_major(self):
        assert _version_newer("2.0.0", "1.99.99") is True

    def test_newer_minor(self):
        assert _version_newer("1.2.0", "1.1.9") is True

    def test_newer_patch(self):
        assert _version_newer("1.0.2", "1.0.1") is True

    def test_same_version(self):
        assert _version_newer("1.0.0", "1.0.0") is False

    def test_older_version(self):
        assert _version_newer("1.0.0", "2.0.0") is False

    def test_invalid_latest(self):
        assert _version_newer("not-a-version", "1.0.0") is False

    def test_invalid_current(self):
        assert _version_newer("1.0.0", "not-a-version") is False

    def test_empty_strings(self):
        assert _version_newer("", "") is False


# ── GET /api/version ─────────────────────────────────────────────────────────


class TestGetVersion:
    def test_returns_version(self, client):
        resp = client.get("/api/version")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    def test_returns_releases_url(self, client):
        resp = client.get("/api/version")
        data = resp.json()
        assert "releases_url" in data
        assert "github.com" in data["releases_url"]


# ── GET /api/version/check ───────────────────────────────────────────────────


class TestCheckForUpdates:
    def _mock_response(self, tag_name="v9.9.9", body="Release notes"):
        payload = json.dumps(
            {"tag_name": tag_name, "body": body, "published_at": "2025-01-01"}
        ).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = payload
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    def test_update_available(self, client):
        with patch("urllib.request.urlopen", return_value=self._mock_response("v9.9.9")):
            resp = client.get("/api/version/check")
        assert resp.status_code == 200
        data = resp.json()
        assert data["update_available"] is True
        assert data["latest_version"] == "9.9.9"
        assert data["current_version"] == APP_VERSION

    def test_no_update_when_on_latest(self, client):
        with patch("urllib.request.urlopen", return_value=self._mock_response(f"v{APP_VERSION}")):
            resp = client.get("/api/version/check")
        data = resp.json()
        assert data["update_available"] is False

    def test_network_error_returns_error_key(self, client):
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            resp = client.get("/api/version/check")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data
        assert data["current_version"] == APP_VERSION

    def test_missing_tag_name_returns_error(self, client):
        payload = json.dumps({"tag_name": "", "body": ""}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = payload
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            resp = client.get("/api/version/check")
        data = resp.json()
        assert "error" in data

    def test_unexpected_exception_returns_error(self, client):
        with patch("urllib.request.urlopen", side_effect=RuntimeError("unexpected")):
            resp = client.get("/api/version/check")
        data = resp.json()
        assert "error" in data
        assert data["current_version"] == APP_VERSION

    def test_response_includes_release_notes(self, client):
        with patch(
            "urllib.request.urlopen", return_value=self._mock_response("v9.9.9", "Big changes")
        ):
            resp = client.get("/api/version/check")
        data = resp.json()
        assert data.get("release_notes") == "Big changes"
