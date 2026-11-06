from http import HTTPStatus

from spotify_stats import history
from spotify_stats.service import build_stats_result
from tests.export_builders import make_export_zip, podcast_play, track_play


def test_a_valid_export_gives_200_and_the_statistics():
    export_zip = make_export_zip(
        {
            "Streaming_History_Audio_2022.json": [
                track_play(track="A", uri="spotify:track:a"),
                track_play(track="A", uri="spotify:track:a"),
                track_play(track="B", uri="spotify:track:b", ms_played=2_000),
                podcast_play(),
            ]
        }
    )

    result = build_stats_result(export_zip.getvalue())

    assert result.status == HTTPStatus.OK
    assert result.body["summary"] == {
        "total_plays": 2,
        "total_ms_played": 2 * 299_560,
        "total_skips": 1,
        "distinct_tracks": 1,
        "distinct_artists": 1,
    }
    assert result.body["overview"]["history_files"] == 1
    assert result.body["overview"]["track_entries"] == 3  # the podcast is not a track entry
    assert [track["track"] for track in result.body["top_tracks"]] == ["A"]
    assert [track["track"] for track in result.body["most_skipped"]] == ["B"]


def test_the_response_never_contains_the_ip_address_or_country():
    export_zip = make_export_zip({"Streaming_History_Audio_2022.json": [track_play()]})

    result = build_stats_result(export_zip.getvalue())

    assert "196.177.175.35" not in str(result.body)
    assert "conn_country" not in str(result.body)


def test_an_upload_that_is_not_a_zip_gives_400():
    result = build_stats_result(b"not a zip")

    assert result.status == HTTPStatus.BAD_REQUEST
    assert "ZIP" in result.body["error"]


def test_an_empty_upload_gives_400():
    assert build_stats_result(b"").status == HTTPStatus.BAD_REQUEST


def test_an_export_over_the_size_limit_gives_413(monkeypatch):
    monkeypatch.setattr(history, "MAX_HISTORY_FILE_BYTES", 100)
    export_zip = make_export_zip({"Streaming_History_Audio_2022.json": [track_play()] * 10})

    assert build_stats_result(export_zip.getvalue()).status == HTTPStatus.REQUEST_ENTITY_TOO_LARGE


def test_query_parameters_are_applied_and_echoed():
    export_zip = make_export_zip(
        {
            "Streaming_History_Audio_2022.json": [
                track_play(ts="2022-03-05T23:30:00Z"),
                track_play(ts="2022-05-01T10:00:00Z"),
            ]
        }
    )
    query = {"timezone": "Africa/Tunis", "date_from": "2022-03-06", "date_to": "2022-03-31"}

    result = build_stats_result(export_zip.getvalue(), query)

    assert result.status == HTTPStatus.OK
    assert result.body["summary"]["total_plays"] == 1
    assert result.body["options"]["timezone"] == "Africa/Tunis"
    assert result.body["options"]["date_from"] == "2022-03-06"


def test_an_invalid_query_parameter_gives_400_before_the_upload_is_read():
    result = build_stats_result(b"not even a zip", {"timezone": "Mars/Base"})

    assert result.status == HTTPStatus.BAD_REQUEST
    assert "timezone" in result.body["error"].lower()
