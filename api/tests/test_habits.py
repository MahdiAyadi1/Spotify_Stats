from spotify_stats.habits import HabitsCollector
from tests.entries import listen_of


def collect(*listens) -> HabitsCollector:
    collector = HabitsCollector()
    for listen in listens:
        collector.add(listen)
    return collector


def test_reasons_count_plays_and_skips_most_frequent_first():
    habits = collect(
        listen_of(reason_start="clickrow", reason_end="trackdone"),
        listen_of(reason_start="clickrow", reason_end="fwdbtn", ms_played=1_000),
        listen_of(reason_start="trackdone", reason_end="trackdone"),
    ).result()

    assert [(r.reason, r.plays, r.skips) for r in habits.reason_start] == [
        ("clickrow", 1, 1),
        ("trackdone", 1, 0),
    ]
    assert [(r.reason, r.plays, r.skips) for r in habits.reason_end] == [
        ("trackdone", 2, 0),
        ("fwdbtn", 0, 1),
    ]


def test_platform_shuffle_and_offline_count_plays_only():
    habits = collect(
        listen_of(platform="iOS", shuffle=True, offline=True, ms_played=60_000),
        listen_of(platform="iOS", ms_played=40_000),
        listen_of(platform="Windows", ms_played=1_000, shuffle=True, offline=True),  # a skip
    ).result()

    assert [(p.platform, p.plays, p.ms_played) for p in habits.platforms] == [("iOS", 2, 100_000)]
    assert (habits.shuffle.shuffled_plays, habits.shuffle.other_plays) == (1, 1)
    assert (habits.offline.offline_plays, habits.offline.online_plays) == (1, 1)


def test_no_listens_gives_empty_habits():
    habits = collect().result()

    assert habits.reason_start == habits.reason_end == habits.platforms == []
    assert habits.shuffle.shuffled_plays == habits.offline.offline_plays == 0
