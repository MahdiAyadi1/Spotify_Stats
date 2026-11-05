"""Helpers that build fake Spotify export entries and ZIPs for the tests."""

import io
import json
import zipfile


def track_play(track="Let Down", artist="Radiohead", uri="spotify:track:1", ms_played=299_560):
    return {
        "ts": "2026-02-05T08:34:23Z",
        "ms_played": ms_played,
        "ip_addr": "196.177.175.35",
        "conn_country": "TN",
        "master_metadata_track_name": track,
        "master_metadata_album_artist_name": artist,
        "spotify_track_uri": uri,
        "episode_name": None,
    }


def podcast_play():
    return {
        "ts": "2026-02-05T09:00:00Z",
        "ms_played": 1_200_000,
        "master_metadata_track_name": None,
        "master_metadata_album_artist_name": None,
        "spotify_track_uri": None,
        "episode_name": "Some episode",
        "spotify_episode_uri": "spotify:episode:1",
    }


def make_export_zip(files: dict[str, object]) -> io.BytesIO:
    """In-memory ZIP; dict values are dumped as JSON, bytes and str are stored as-is."""
    export_zip = io.BytesIO()
    with zipfile.ZipFile(export_zip, "w") as archive:
        for file_name, content in files.items():
            if not isinstance(content, bytes | str):
                content = json.dumps(content)
            archive.writestr(file_name, content)
    export_zip.seek(0)
    return export_zip
