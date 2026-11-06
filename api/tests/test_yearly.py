from spotify_stats.yearly import YearlyTopTracksCollector
from tests.entries import listen_of


def collect(*listens) -> YearlyTopTracksCollector:
    collector = YearlyTopTracksCollector()
    for listen in listens:
        collector.add(listen)
    return collector


def test_gives_the_most_played_track_of_each_year_in_year_order():
    collector = collect(
        listen_of(track="A", ended_at="2022-01-01T10:00:00"),
        listen_of(track="B", ended_at="2022-01-02T10:00:00"),
        listen_of(track="B", ended_at="2022-01-03T10:00:00"),
        listen_of(track="A", ended_at="2021-06-01T10:00:00"),
    )

    assert [(top.year, top.track, top.plays) for top in collector.result()] == [
        (2021, "A", 1),
        (2022, "B", 2),
    ]


def test_ties_go_to_the_longer_listening_time():
    collector = collect(
        listen_of(track="Short", ms_played=100_000),
        listen_of(track="Long", ms_played=300_000),
    )

    assert collector.result()[0].track == "Long"


def test_skips_do_not_count():
    assert collect(listen_of(ms_played=1_000)).result() == []
