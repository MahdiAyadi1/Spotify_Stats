from dataclasses import asdict

from spotify_stats.aggregation import compute_listening_stats
from spotify_stats.constants import MIN_PLAY_MS
from spotify_stats.history import TrackEntry


def track_entry(track="Let Down", artist="Radiohead", ms_played=200_000, uri=None):
    return TrackEntry(
        track_uri=uri or f"spotify:track:{track}",
        track_name=track,
        artist_name=artist,
        ms_played=ms_played,
    )


def test_a_listen_of_exactly_the_minimum_is_a_play_and_one_millisecond_less_is_a_skip():
    stats = compute_listening_stats(
        [track_entry(ms_played=MIN_PLAY_MS), track_entry(ms_played=MIN_PLAY_MS - 1)]
    )

    assert stats.summary.total_plays == 1
    assert stats.most_skipped[0].skips == 1


def test_skips_add_neither_plays_nor_listening_time():
    stats = compute_listening_stats(
        [track_entry(ms_played=200_000), track_entry(ms_played=5_000), track_entry(ms_played=1)]
    )

    assert stats.top_tracks[0].plays == 1
    assert stats.top_tracks[0].ms_played == 200_000
    assert stats.summary.total_ms_played == 200_000


def test_groups_plays_by_track_uri_even_when_the_name_differs():
    stats = compute_listening_stats(
        [
            track_entry(track="Let Down", uri="spotify:track:1"),
            track_entry(track="Let Down - Remastered", uri="spotify:track:1"),
        ]
    )

    assert len(stats.top_tracks) == 1
    assert stats.top_tracks[0].plays == 2
    assert stats.top_tracks[0].track == "Let Down"


def test_ranks_by_plays_then_listening_time_starting_at_one():
    stats = compute_listening_stats(
        [
            track_entry(track="A", ms_played=100_000),
            track_entry(track="B", ms_played=100_000),
            track_entry(track="B", ms_played=100_000),
            track_entry(track="C", ms_played=300_000),
            track_entry(track="D", ms_played=100_000),
        ]
    )

    assert [(t.rank, t.track) for t in stats.top_tracks] == [(1, "B"), (2, "C"), (3, "A"), (4, "D")]


def test_a_track_that_was_only_skipped_is_not_in_the_top_tracks():
    stats = compute_listening_stats([track_entry(track="Skipped", ms_played=2_000)])

    assert stats.top_tracks == []
    assert stats.summary.distinct_tracks == 0
    assert [t.track for t in stats.most_skipped] == ["Skipped"]


def test_most_skipped_ranks_by_skips_then_prefers_the_track_with_fewer_plays():
    stats = compute_listening_stats(
        [
            track_entry(track="Rarely", ms_played=1_000),
            track_entry(track="Often", ms_played=1_000),
            track_entry(track="Often", ms_played=1_000),
            track_entry(track="Liked", ms_played=1_000),
            track_entry(track="Liked", ms_played=200_000),
        ]
    )

    assert [(t.rank, t.track, t.skips) for t in stats.most_skipped] == [
        (1, "Often", 2),
        (2, "Rarely", 1),
        (3, "Liked", 1),
    ]


def test_no_entries_gives_empty_statistics():
    stats = compute_listening_stats([])

    assert asdict(stats) == {
        "summary": {"total_plays": 0, "total_ms_played": 0, "distinct_tracks": 0},
        "top_tracks": [],
        "most_skipped": [],
    }


def test_statistics_have_the_shape_of_the_api_contract():
    stats = asdict(compute_listening_stats([track_entry(), track_entry(track="B", ms_played=1)]))

    assert set(stats) == {"summary", "top_tracks", "most_skipped"}
    assert set(stats["summary"]) == {"total_plays", "total_ms_played", "distinct_tracks"}
    assert set(stats["top_tracks"][0]) == {"rank", "track", "artist", "plays", "ms_played"}
    assert set(stats["most_skipped"][0]) == {"rank", "track", "artist", "skips"}