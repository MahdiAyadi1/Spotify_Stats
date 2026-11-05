import io
import json

import pytest

from spotify_stats import history
from spotify_stats.history import (
    ExportTooLargeError,
    InvalidExportError,
    TrackEntry,
    iter_track_entries,
)
from tests.export_builders import make_export_zip, podcast_play, track_play


def test_yields_only_the_fields_the_statistics_need():
    export_zip = make_export_zip({"Streaming_History_Audio_2022.json": [track_play()]})

    assert list(iter_track_entries(export_zip)) == [
        TrackEntry(
            track_uri="spotify:track:1",
            track_name="Let Down",
            artist_name="Radiohead",
            ms_played=299_560,
        )
    ]


def test_reads_audio_files_only_including_split_years_and_folders():
    export_zip = make_export_zip(
        {
            "Spotify Extended Streaming History/Streaming_History_Audio_2022.json": [
                track_play(uri="spotify:track:2022")
            ],
            "Spotify Extended Streaming History/Streaming_History_Audio_2023_1.json": [
                track_play(uri="spotify:track:2023-1")
            ],
            "Spotify Extended Streaming History/Streaming_History_Audio_2023_2.json": [
                track_play(uri="spotify:track:2023-2")
            ],
            "Spotify Extended Streaming History/Streaming_History_Video_2021.json": [
                track_play(uri="spotify:track:video")
            ],
            "Spotify Extended Streaming History/ReadMeFirst_ExtendedStreamingHistory.pdf": b"%PDF",
        }
    )

    track_uris = {entry.track_uri for entry in iter_track_entries(export_zip)}

    assert track_uris == {"spotify:track:2022", "spotify:track:2023-1", "spotify:track:2023-2"}


def test_skips_podcast_entries():
    export_zip = make_export_zip(
        {"Streaming_History_Audio_2022.json": [podcast_play(), track_play()]}
    )

    assert [entry.track_name for entry in iter_track_entries(export_zip)] == ["Let Down"]


def test_yields_short_listens_too_because_skips_are_decided_by_the_aggregation():
    export_zip = make_export_zip(
        {"Streaming_History_Audio_2022.json": [track_play(ms_played=3_000)]}
    )

    assert [entry.ms_played for entry in iter_track_entries(export_zip)] == [3_000]


def test_rejects_an_upload_that_is_not_a_zip():
    with pytest.raises(InvalidExportError):
        list(iter_track_entries(io.BytesIO(b"not a zip")))


def test_rejects_a_zip_without_audio_history_files():
    export_zip = make_export_zip({"Streaming_History_Video_2021.json": [track_play()]})

    with pytest.raises(InvalidExportError):
        list(iter_track_entries(export_zip))


def test_rejects_invalid_json():
    export_zip = make_export_zip({"Streaming_History_Audio_2022.json": "{not json"})

    with pytest.raises(InvalidExportError):
        list(iter_track_entries(export_zip))


def test_rejects_a_track_entry_without_ms_played():
    broken_play = track_play()
    del broken_play["ms_played"]
    export_zip = make_export_zip({"Streaming_History_Audio_2022.json": [broken_play]})

    with pytest.raises(InvalidExportError):
        list(iter_track_entries(export_zip))


def test_rejects_a_history_file_larger_than_the_limit(monkeypatch):
    monkeypatch.setattr(history, "MAX_HISTORY_FILE_BYTES", 100)
    export_zip = make_export_zip({"Streaming_History_Audio_2022.json": [track_play()] * 10})

    with pytest.raises(ExportTooLargeError):
        list(iter_track_entries(export_zip))


def test_rejects_history_files_that_together_exceed_the_total_limit(monkeypatch):
    one_file_bytes = len(json.dumps([track_play()]))
    monkeypatch.setattr(history, "MAX_TOTAL_HISTORY_BYTES", one_file_bytes * 3 // 2)
    export_zip = make_export_zip(
        {
            "Streaming_History_Audio_2022.json": [track_play()],
            "Streaming_History_Audio_2023.json": [track_play()],
        }
    )

    with pytest.raises(ExportTooLargeError):
        list(iter_track_entries(export_zip))
