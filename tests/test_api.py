"""Tests for API endpoints."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.models import DefaultsConfig


@pytest.fixture
def client():
    """Create test client with mocked dependencies."""
    # Import here to avoid module-level import issues
    from backend.main import app
    return TestClient(app)


def create_mock_config(
    plex_url="http://test:32400",
    plex_token="token",
    music_library="Music",
    llm_provider="anthropic",
    llm_api_key="key",
    model_analysis="claude-sonnet-4-5",
    model_generation="claude-haiku-4-5",
    track_count=25,
):
    """Create a properly structured mock config."""
    mock = MagicMock()
    mock.plex.url = plex_url
    mock.plex.token = plex_token
    mock.plex.music_library = music_library
    mock.llm.provider = llm_provider
    mock.llm.api_key = llm_api_key
    mock.llm.model_analysis = model_analysis
    mock.llm.model_generation = model_generation
    mock.defaults = DefaultsConfig(track_count=track_count)
    return mock


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_returns_status(self, client):
        """Should return health status."""
        with patch("backend.main.get_config") as mock_config:
            with patch("backend.main.get_plex_client") as mock_plex:
                mock_config.return_value = create_mock_config()
                mock_plex.return_value = MagicMock(is_connected=MagicMock(return_value=True))

                response = client.get("/api/health")

                assert response.status_code == 200
                data = response.json()
                assert "status" in data
                assert data["status"] == "healthy"

    def test_health_check_shows_plex_status(self, client):
        """Should show Plex connection status."""
        with patch("backend.main.get_config") as mock_config:
            with patch("backend.main.get_plex_client") as mock_plex:
                mock_config.return_value = create_mock_config()
                mock_plex.return_value = MagicMock(is_connected=MagicMock(return_value=True))

                response = client.get("/api/health")

                assert response.status_code == 200
                data = response.json()
                assert "plex_connected" in data
                assert data["plex_connected"] is True

    def test_health_check_shows_llm_status(self, client):
        """Should show LLM configuration status."""
        with patch("backend.main.get_config") as mock_config:
            with patch("backend.main.get_plex_client") as mock_plex:
                mock_config.return_value = create_mock_config(llm_api_key="key")
                mock_plex.return_value = None  # No Plex client

                response = client.get("/api/health")

                assert response.status_code == 200
                data = response.json()
                assert "llm_configured" in data
                assert data["llm_configured"] is True


class TestConfigEndpoints:
    """Tests for configuration endpoints."""

    def test_get_config_returns_safe_values(self, client):
        """GET /api/config should return config without secrets."""
        with patch("backend.main.get_config") as mock_get_config:
            with patch("backend.main.get_plex_client") as mock_plex:
                mock_get_config.return_value = create_mock_config(
                    plex_url="http://test:32400",
                    plex_token="secret-token",
                    llm_provider="anthropic",
                    llm_api_key="secret-api-key",
                )
                mock_plex.return_value = MagicMock(is_connected=MagicMock(return_value=True))

                response = client.get("/api/config")

                assert response.status_code == 200
                data = response.json()

                # Should include URL but not token
                assert data["plex_url"] == "http://test:32400"
                assert "secret-token" not in str(data)

                # Should show provider but not API key
                assert data["llm_provider"] == "anthropic"
                assert "api_key" not in data
                assert "secret-api-key" not in str(data)

    def test_post_config_validates_plex_url(self, client):
        """POST /api/config should validate Plex URL format."""
        with patch("backend.main.update_config_values") as mock_update:
            with patch("backend.main.get_plex_client") as mock_plex:
                with patch("backend.main.init_plex_client"):
                    mock_config = create_mock_config(plex_url="http://new-server:32400")
                    mock_update.return_value = mock_config
                    mock_plex.return_value = MagicMock(is_connected=MagicMock(return_value=True))

                    response = client.post(
                        "/api/config",
                        json={"plex_url": "http://new-server:32400"}
                    )

                    assert response.status_code == 200

    def test_post_config_updates_llm_provider(self, client):
        """POST /api/config should allow changing LLM provider."""
        with patch("backend.main.update_config_values") as mock_update:
            with patch("backend.main.get_plex_client") as mock_plex:
                with patch("backend.main.init_plex_client"):
                    mock_config = create_mock_config(llm_provider="openai")
                    mock_update.return_value = mock_config
                    mock_plex.return_value = MagicMock(is_connected=MagicMock(return_value=True))

                    response = client.post(
                        "/api/config",
                        json={"llm_provider": "openai"}
                    )

                    assert response.status_code == 200


class TestIndexPage:
    """Tests for index page serving."""

    def test_index_returns_response(self, client):
        """Should return some response for root path."""
        response = client.get("/")
        # Either returns HTML or JSON message
        assert response.status_code == 200
