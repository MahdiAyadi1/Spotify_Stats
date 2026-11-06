from spotify_stats.aggregation import compute_listening_stats
from spotify_stats.discovery import discoveries_per_month
from tests.entries import track_entry


def test_counts_new_tracks_and_artists_in_the_month_they_were_first_played():
    stats = compute_listening_stats(
        [
            track_entry(track="A", artist="X", ended_at="2022-01-10T10:00:00"),
            track_entry(track="A", artist="X", ended_at="2022-03-10T10:00:00"),  # not new again
            track_entry(track="B", artist="X", ended_at="2022-03-11T10:00:00"),
            track_entry(track="C", artist="Y", ended_at="2022-03-12T10:00:00"),
        ]
    )

    assert [(d.month, d.new_tracks, d.new_artists) for d in stats.discovery] == [
        ("2022-01", 1, 1),
        ("2022-02", 0, 0),
        ("2022-03", 2, 1),
    ]


def test_nothing_played_gives_no_months():
    assert discoveries_per_month([], []) == []
