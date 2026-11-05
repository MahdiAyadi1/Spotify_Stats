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
        "distinct_tracks": 1,
    }
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
