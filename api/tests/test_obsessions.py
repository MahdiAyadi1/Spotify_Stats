from spotify_stats.constants import OBSESSION_LIMIT
from spotify_stats.obsessions import ObsessionsCollector
from tests.entries import listen_of


def collect(*listens) -> ObsessionsCollector:
    collector = ObsessionsCollector()
    for listen in listens:
        collector.add(listen)
    return collector


def test_ranks_tracks_by_their_best_day_and_best_week_each_track_once():
    collector = collect(
        *[listen_of(track="A", ended_at="2022-03-07T10:00:00") for _ in range(3)],  # a Monday
        listen_of(track="A", ended_at="2022-03-09T10:00:00"),
        *[listen_of(track="B", ended_at="2022-03-01T10:00:00") for _ in range(2)],
    )

    obsessions = collector.result()

    assert [(o.rank, o.track, o.period_start, o.plays) for o in obsessions.days] == [
        (1, "A", "2022-03-07", 3),
        (2, "B", "2022-03-01", 2),
    ]
    assert [(o.rank, o.track, o.period_start, o.plays) for o in obsessions.weeks] == [
        (1, "A", "2022-03-07", 4),
        (2, "B", "2022-02-28", 2),  # weeks start on Monday
    ]


def test_skips_do_not_count():
    result = collect(listen_of(ms_played=1_000)).result()

    assert result.days == []
    assert result.weeks == []


def test_lists_are_limited():
    collector = collect(
        *[
            listen_of(track=f"Track {number}", ended_at=f"2022-03-{number + 1:02d}T10:00:00")
            for number in range(OBSESSION_LIMIT + 2)
        ]
    )

    assert len(collector.result().days) == OBSESSION_LIMIT
