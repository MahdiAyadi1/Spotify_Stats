from spotify_stats.options import parse_options
from spotify_stats.timeline import TimelineCollector, months_between
from tests.entries import listen_of


def collect(*listens) -> TimelineCollector:
    collector = TimelineCollector()
    for listen in listens:
        collector.add(listen)
    return collector


def test_months_are_filled_between_the_first_and_the_last_and_summed_per_year():
    collector = collect(
        listen_of(ended_at="2021-12-20T10:00:00", ms_played=100_000),
        listen_of(ended_at="2022-02-01T10:00:00", ms_played=200_000),
        listen_of(ended_at="2022-02-09T10:00:00", ms_played=300_000),
    )

    timeline = collector.timeline()

    assert [(m.month, m.plays, m.ms_played) for m in timeline.months] == [
        ("2021-12", 1, 100_000),
        ("2022-01", 0, 0),
        ("2022-02", 2, 500_000),
    ]
    assert [(y.year, y.plays, y.ms_played) for y in timeline.years] == [
        (2021, 1, 100_000),
        (2022, 2, 500_000),
    ]


def test_skips_are_not_counted():
    collector = collect(listen_of(ms_played=1_000))

    assert collector.timeline().months == []
    assert sum(hour.plays for hour in collector.clock().hours) == 0


def test_clock_counts_plays_per_hour_and_weekday_with_monday_as_zero():
    collector = collect(listen_of(ended_at="2022-03-05T10:15:00", ms_played=60_000))  # a Saturday

    clock = collector.clock()

    assert len(clock.hours) == 24
    assert len(clock.weekdays) == 7
    assert (clock.hours[10].plays, clock.hours[10].ms_played) == (1, 60_000)
    assert clock.weekdays[5].plays == 1


def test_the_timezone_moves_a_play_to_the_next_day_and_hour():
    options = parse_options({"timezone": "Africa/Tunis"})  # UTC+1
    collector = collect(listen_of(options, ended_at="2022-03-05T23:30:00"))

    clock = collector.clock()

    assert clock.hours[0].plays == 1
    assert clock.weekdays[6].plays == 1  # Sunday March 6th, local time


def test_months_between_crosses_a_year_boundary():
    assert list(months_between("2021-11", "2022-02")) == [
        "2021-11",
        "2021-12",
        "2022-01",
        "2022-02",
    ]
