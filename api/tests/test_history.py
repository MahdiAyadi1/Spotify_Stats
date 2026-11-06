import io
import json
from datetime import UTC, datetime

import pytest

from spotify_stats import history
from spotify_stats.history import (
    ExportTooLargeError,
    InvalidExportError,
    TrackEntry,
    count_audio_history_files,
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
            ended_at=datetime(2026, 2, 5, 8, 34, 23, tzinfo=UTC),
            album_name="OK Computer",
            reason_start="clickrow",
            reason_end="trackdone",
            shuffle=False,
            platform="iOS",
            offline=False,
        )
    ]


def test_reads_the_habit_fields_and_groups_the_platform():
    export_zip = make_export_zip(
        {
            "Streaming_History_Audio_2022.json": [
                track_play(
                    platform="Windows 10 (10.0.19044; x64)",
                    reason_start="fwdbtn",
                    reason_end="endplay",
                    shuffle=True,
                    offline=True,
                )
            ]
        }
    )

    (entry,) = iter_track_entries(export_zip)

    assert entry.platform == "Windows"
    assert (entry.reason_start, entry.reason_end) == ("fwdbtn", "endplay")
    assert entry.shuffle is True
    assert entry.offline is True


def test_missing_optional_fields_get_neutral_values():
    play = track_play()
    for field in ("master_metadata_album_album_name", "reason_start", "reason_end", "platform"):
        play[field] = None
    play["shuffle"] = None
    export_zip = make_export_zip({"Streaming_History_Audio_2022.json": [play]})

    (entry,) = iter_track_entries(export_zip)

    assert (entry.album_name, entry.reason_start, entry.reason_end) == ("", "unknown", "unknown")
    assert (entry.platform, entry.shuffle, entry.offline) == ("Other", False, False)


def test_a_timestamp_with_an_offset_is_converted_to_utc():
    export_zip = make_export_zip(
        {"Streaming_History_Audio_2022.json": [track_play(ts="2022-03-05T10:00:00+01:00")]}
    )

    (entry,) = iter_track_entries(export_zip)

    assert entry.ended_at == datetime(2022, 3, 5, 9, 0, tzinfo=UTC)


@pytest.mark.parametrize("timestamp", [None, "", "yesterday", 20220305])
def test_rejects_a_track_entry_without_a_valid_timestamp(timestamp):
    export_zip = make_export_zip(
        {"Streaming_History_Audio_2022.json": [track_play(ts=timestamp)]}
    )

    with pytest.raises(InvalidExportError):
        list(iter_track_entries(export_zip))


def test_counts_the_audio_history_files_only():
    export_zip = make_export_zip(
        {
            "Streaming_History_Audio_2022.json": [],
            "Streaming_History_Audio_2023_1.json": [],
            "Streaming_History_Video_2021.json": [],
        }
    )

    assert count_audio_history_files(export_zip) == 2


def test_counting_the_files_of_something_that_is_not_a_zip_is_rejected():
    with pytest.raises(InvalidExportError):
        count_audio_history_files(io.BytesIO(b"not a zip"))


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
