"""Tests for Plex client."""

import pytest
from unittest.mock import MagicMock, patch

from backend.models import Track


class TestPlexClientConnection:
    """Tests for Plex connection handling."""

    def test_connect_with_valid_credentials(self, mocker):
        """Should connect successfully with valid credentials."""
        from backend.plex_client import PlexClient

        mock_server = MagicMock()
        mock_server.library.section.return_value = MagicMock()

        with patch("backend.plex_client.PlexServer", return_value=mock_server):
            client = PlexClient("http://localhost:32400", "valid-token", "Music")
            assert client.is_connected() is True

    def test_connect_with_invalid_token(self, mocker):
        """Should handle invalid token gracefully."""
        from backend.plex_client import PlexClient
        from plexapi.exceptions import Unauthorized

        with patch("backend.plex_client.PlexServer", side_effect=Unauthorized("Invalid token")):
            client = PlexClient("http://localhost:32400", "invalid-token", "Music")
            assert client.is_connected() is False
            assert "invalid" in client.get_error().lower() or "unauthorized" in client.get_error().lower()

    def test_connect_with_unreachable_server(self, mocker):
        """Should handle unreachable server gracefully."""
        from backend.plex_client import PlexClient
        from requests.exceptions import ConnectionError

        with patch("backend.plex_client.PlexServer", side_effect=ConnectionError("Connection refused")):
            client = PlexClient("http://unreachable:32400", "token", "Music")
            assert client.is_connected() is False
            assert client.get_error() is not None

    def test_connect_with_missing_library(self, mocker):
        """Should handle missing music library."""
        from backend.plex_client import PlexClient
        from plexapi.exceptions import NotFound

        mock_server = MagicMock()
        mock_server.library.section.side_effect = NotFound("Library not found")

        with patch("backend.plex_client.PlexServer", return_value=mock_server):
            client = PlexClient("http://localhost:32400", "token", "NonexistentLibrary")
            assert client.is_connected() is False
            assert "library" in client.get_error().lower() or "not found" in client.get_error().lower()


class TestPlexClientLibraryStats:
    """Tests for library statistics."""

    def test_get_library_stats(self, mocker):
        """Should return library statistics."""
        from backend.plex_client import PlexClient

        # Create mock tracks
        mock_tracks = []
        for i in range(10):
            track = MagicMock()
            track.ratingKey = str(i)
            track.title = f"Track {i}"
            track.grandparentTitle = f"Artist {i % 3}"
            track.parentTitle = f"Album {i % 5}"
            track.duration = 180000 + i * 10000
            track.parentYear = 1990 + i
            track.genres = [MagicMock(tag="Rock"), MagicMock(tag="Alternative")]
            mock_tracks.append(track)

        mock_library = MagicMock()
        mock_library.search.return_value = mock_tracks

        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_library

        with patch("backend.plex_client.PlexServer", return_value=mock_server):
            client = PlexClient("http://localhost:32400", "token", "Music")
            stats = client.get_library_stats()

            assert stats["total_tracks"] == 10
            assert len(stats["genres"]) > 0
            assert len(stats["decades"]) > 0


class TestPlexClientMusicLibraries:
    """Tests for music library listing."""

    def test_get_music_libraries(self, mocker):
        """Should return list of music libraries."""
        from backend.plex_client import PlexClient

        mock_section1 = MagicMock()
        mock_section1.title = "Music"
        mock_section1.type = "artist"

        mock_section2 = MagicMock()
        mock_section2.title = "Movies"
        mock_section2.type = "movie"

        mock_section3 = MagicMock()
        mock_section3.title = "Jazz Collection"
        mock_section3.type = "artist"

        mock_server = MagicMock()
        mock_server.library.sections.return_value = [mock_section1, mock_section2, mock_section3]
        mock_server.library.section.return_value = MagicMock()

        with patch("backend.plex_client.PlexServer", return_value=mock_server):
            client = PlexClient("http://localhost:32400", "token", "Music")
            libraries = client.get_music_libraries()

            assert "Music" in libraries
            assert "Jazz Collection" in libraries
            assert "Movies" not in libraries


class TestPlexClientTrackSearch:
    """Tests for track search functionality."""

    def test_search_tracks_by_title(self, mocker):
        """Should find tracks by title."""
        from backend.plex_client import PlexClient

        mock_track = MagicMock()
        mock_track.ratingKey = "123"
        mock_track.title = "Fake Plastic Trees"
        mock_track.grandparentTitle = "Radiohead"
        mock_track.parentTitle = "The Bends"
        mock_track.duration = 290000
        mock_track.parentYear = 1995
        mock_track.genres = [MagicMock(tag="Alternative")]

        mock_library = MagicMock()
        mock_library.searchTracks.return_value = [mock_track]
        mock_library.search.return_value = []

        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_library

        with patch("backend.plex_client.PlexServer", return_value=mock_server):
            client = PlexClient("http://localhost:32400", "token", "Music")
            results = client.search_tracks("Fake Plastic")

            assert len(results) == 1
            assert results[0].title == "Fake Plastic Trees"
            assert results[0].artist == "Radiohead"

    def test_search_tracks_by_artist(self, mocker):
        """Should find tracks by artist name."""
        from backend.plex_client import PlexClient

        mock_track = MagicMock()
        mock_track.ratingKey = "456"
        mock_track.title = "Creep"
        mock_track.grandparentTitle = "Radiohead"
        mock_track.parentTitle = "Pablo Honey"
        mock_track.duration = 238000
        mock_track.parentYear = 1993
        mock_track.genres = []

        mock_library = MagicMock()
        mock_library.searchTracks.return_value = []
        mock_library.search.return_value = [mock_track]

        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_library

        with patch("backend.plex_client.PlexServer", return_value=mock_server):
            client = PlexClient("http://localhost:32400", "token", "Music")
            results = client.search_tracks("Radiohead")

            assert len(results) == 1
            assert results[0].artist == "Radiohead"

    def test_search_tracks_returns_formatted_results(self, mocker):
        """Search results should include album art URLs."""
        from backend.plex_client import PlexClient

        mock_track = MagicMock()
        mock_track.ratingKey = "789"
        mock_track.title = "Black"
        mock_track.grandparentTitle = "Pearl Jam"
        mock_track.parentTitle = "Ten"
        mock_track.duration = 340000
        mock_track.parentYear = 1991
        mock_track.genres = [MagicMock(tag="Grunge")]

        mock_library = MagicMock()
        mock_library.searchTracks.return_value = [mock_track]
        mock_library.search.return_value = []

        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_library

        with patch("backend.plex_client.PlexServer", return_value=mock_server):
            client = PlexClient("http://localhost:32400", "token", "Music")
            results = client.search_tracks("Black")

            assert len(results) == 1
            assert results[0].art_url == "/api/art/789"


class TestPlexClientPlaylistCreation:
    """Tests for playlist creation."""

    def test_create_playlist_success(self, mocker):
        """Should create playlist successfully."""
        from backend.plex_client import PlexClient

        mock_track = MagicMock()
        mock_playlist = MagicMock()
        mock_playlist.ratingKey = "999"

        mock_server = MagicMock()
        mock_server.library.section.return_value = MagicMock()
        mock_server.fetchItem.return_value = mock_track
        mock_server.createPlaylist.return_value = mock_playlist

        with patch("backend.plex_client.PlexServer", return_value=mock_server):
            client = PlexClient("http://localhost:32400", "token", "Music")
            result = client.create_playlist("Test Playlist", ["1", "2", "3"])

            assert result["success"] is True
            assert result["playlist_id"] == "999"

    def test_create_playlist_handles_invalid_tracks(self, mocker):
        """Should skip invalid track keys gracefully."""
        from backend.plex_client import PlexClient

        mock_server = MagicMock()
        mock_server.library.section.return_value = MagicMock()
        mock_server.fetchItem.side_effect = Exception("Not found")

        with patch("backend.plex_client.PlexServer", return_value=mock_server):
            client = PlexClient("http://localhost:32400", "token", "Music")
            result = client.create_playlist("Test Playlist", ["invalid"])

            assert result["success"] is False
            assert "error" in result
