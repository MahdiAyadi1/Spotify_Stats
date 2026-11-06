from dataclasses import asdict
from datetime import date

from spotify_stats.aggregation import ListeningSummary, compute_listening_stats
from spotify_stats.constants import MIN_PLAY_MS
from spotify_stats.options import StatsOptions, parse_options
from tests.entries import track_entry


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

    assert stats.summary == ListeningSummary(0, 0, 0, 0, 0)
    assert stats.top_tracks == stats.top_artists == stats.top_albums == []
    assert stats.most_skipped == stats.yearly_top_tracks == stats.discovery == []
    assert stats.timeline.months == []
    assert len(stats.clock.hours) == 24
    assert stats.sessions.count == 0
    assert stats.overview.first_entry is None


def test_statistics_have_the_shape_of_the_api_contract():
    stats = asdict(compute_listening_stats([track_entry(), track_entry(track="B", ms_played=1)]))

    assert set(stats) == {
        "options", "overview", "summary", "top_tracks", "top_artists", "top_albums",
        "most_skipped", "yearly_top_tracks", "discovery", "timeline", "clock",
        "obsessions", "sessions", "habits",
    }  # fmt: skip
    assert set(stats["summary"]) == {
        "total_plays", "total_ms_played", "total_skips", "distinct_tracks", "distinct_artists",
    }  # fmt: skip
    assert set(stats["top_tracks"][0]) == {
        "rank", "track", "artist", "plays", "ms_played", "skips", "skip_rate", "first_played",
    }  # fmt: skip
    assert set(stats["most_skipped"][0]) == {
        "rank", "track", "artist", "skips", "plays", "skip_rate",
    }  # fmt: skip
    assert set(stats["top_artists"][0]) == {
        "rank", "artist", "plays", "ms_played", "skips", "skip_rate", "first_played",
    }  # fmt: skip
    assert set(stats["top_albums"][0]) == {"rank", "album", "artist", "plays", "ms_played"}
    assert set(stats["timeline"]) == {"months", "years"}
    assert set(stats["clock"]) == {"hours", "weekdays"}
    assert set(stats["obsessions"]) == {"days", "weeks"}
    assert set(stats["sessions"]) == {"count", "average_ms", "longest"}
    assert set(stats["habits"]) == {"reason_start", "reason_end", "platforms", "shuffle", "offline"}


def test_skip_rate_is_the_share_of_skips_among_all_listens():
    stats = compute_listening_stats(
        [track_entry(), track_entry(), track_entry(), track_entry(ms_played=1_000)]
    )

    assert stats.top_tracks[0].skip_rate == 0.25
    assert stats.top_artists[0].skip_rate == 0.25
    assert stats.most_skipped[0].skip_rate == 0.25


def test_top_artists_are_ranked_by_plays_across_their_tracks():
    stats = compute_listening_stats(
        [
            track_entry(track="A1", artist="One Hit"),
            track_entry(track="B1", artist="Many Songs"),
            track_entry(track="B2", artist="Many Songs"),
            track_entry(track="B2", artist="Many Songs", ms_played=1_000),
        ]
    )

    assert [(a.rank, a.artist, a.plays, a.skips) for a in stats.top_artists] == [
        (1, "Many Songs", 2, 1),
        (2, "One Hit", 1, 0),
    ]
    assert stats.summary.distinct_artists == 2


def test_top_albums_group_by_album_and_artist_and_ignore_entries_without_album():
    stats = compute_listening_stats(
        [
            track_entry(track="A", artist="X", album="Greatest Hits"),
            track_entry(track="B", artist="X", album="Greatest Hits"),
            track_entry(track="C", artist="Y", album="Greatest Hits"),
            track_entry(track="D", artist="Y", album=""),
        ]
    )

    assert [(a.album, a.artist, a.plays) for a in stats.top_albums] == [
        ("Greatest Hits", "X", 2),
        ("Greatest Hits", "Y", 1),
    ]


def test_first_played_is_the_earliest_play_whatever_the_order_of_the_entries():
    stats = compute_listening_stats(
        [
            track_entry(ended_at="2022-05-01T10:00:00"),
            track_entry(ended_at="2021-12-31T10:00:00"),
            track_entry(ended_at="2021-11-30T10:00:00", ms_played=1_000),  # a skip, not a play
        ]
    )

    assert stats.top_tracks[0].first_played == "2021-12-31"
    assert stats.top_artists[0].first_played == "2021-12-31"


def test_merge_duplicates_groups_tracks_with_the_same_name_and_artist():
    entries = [
        track_entry(track="Let Down", uri="spotify:track:album"),
        track_entry(track="let down", uri="spotify:track:single"),
        track_entry(track="Let Down", artist="Someone Else", uri="spotify:track:cover"),
    ]

    separate = compute_listening_stats(entries)
    merged = compute_listening_stats(entries, StatsOptions(merge_duplicates=True))

    assert [t.plays for t in separate.top_tracks] == [1, 1, 1]
    assert [(t.artist, t.plays) for t in merged.top_tracks] == [
        ("Radiohead", 2),
        ("Someone Else", 1),
    ]


def test_min_play_ms_changes_what_counts_as_a_play():
    entries = [track_entry(ms_played=10_000), track_entry(ms_played=40_000)]

    default = compute_listening_stats(entries)
    strict = compute_listening_stats(entries, StatsOptions(min_play_ms=60_000))
    lenient = compute_listening_stats(entries, StatsOptions(min_play_ms=5_000))

    assert (default.summary.total_plays, default.summary.total_skips) == (1, 1)
    assert (strict.summary.total_plays, strict.summary.total_skips) == (0, 2)
    assert (lenient.summary.total_plays, lenient.summary.total_skips) == (2, 0)


def test_min_skips_hides_tracks_skipped_less_often():
    entries = [track_entry(track="Once", ms_played=1), track_entry(track="Twice", ms_played=1)] * 2
    entries.append(track_entry(track="Once", ms_played=1))

    stats = compute_listening_stats(entries, StatsOptions(min_skips=3))

    assert [(t.track, t.skips) for t in stats.most_skipped] == [("Once", 3)]


def test_date_range_filters_every_statistic_but_not_the_overview():
    entries = [
        track_entry(track="March", ended_at="2022-03-05T10:00:00"),
        track_entry(track="April", ended_at="2022-04-10T10:00:00"),
        track_entry(track="May", ended_at="2022-05-15T10:00:00"),
    ]
    options = StatsOptions(date_from=date(2022, 4, 1), date_to=date(2022, 4, 30))

    stats = compute_listening_stats(entries, options, history_files=2)

    assert [t.track for t in stats.top_tracks] == ["April"]
    assert [m.month for m in stats.timeline.months] == ["2022-04"]
    assert stats.options.date_from == "2022-04-01"
    assert stats.overview.history_files == 2
    assert stats.overview.track_entries == 3
    assert (stats.overview.first_entry, stats.overview.last_entry) == ("2022-03-05", "2022-05-15")


def test_the_date_range_follows_the_requested_timezone():
    entry = track_entry(ended_at="2022-03-05T23:30:00")  # already March 6th in Tunisia (UTC+1)
    options = parse_options({"timezone": "Africa/Tunis", "date_from": "2022-03-06"})

    in_tunisia = compute_listening_stats([entry], options)
    in_utc = compute_listening_stats([entry], parse_options({"date_from": "2022-03-06"}))

    assert in_tunisia.summary.total_plays == 1
    assert in_utc.summary.total_plays == 0
