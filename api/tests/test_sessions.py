from datetime import UTC

from spotify_stats.options import parse_options
from spotify_stats.sessions import SessionsCollector
from tests.entries import listen_of

THREE_MINUTES = 180_000


def collect(*listens, timezone=UTC) -> SessionsCollector:
    collector = SessionsCollector(timezone)
    for listen in listens:
        collector.add(listen)
    return collector


def test_plays_close_together_form_one_session_and_a_long_gap_starts_another():
    collector = collect(
        listen_of(ended_at="2022-03-05T10:00:00", ms_played=THREE_MINUTES),
        listen_of(ended_at="2022-03-05T10:10:00", ms_played=THREE_MINUTES),
        listen_of(ended_at="2022-03-05T12:00:00", ms_played=THREE_MINUTES),
    )

    sessions = collector.result()

    assert sessions.count == 2
    assert sessions.average_ms == 480_000  # (09:57 to 10:10 = 13 min, and 3 min) / 2
    assert sessions.longest.started_at == "2022-03-05T09:57:00+00:00"
    assert sessions.longest.duration_ms == 780_000
    assert sessions.longest.plays == 2


def test_a_gap_of_exactly_the_limit_does_not_split_the_session():
    collector = collect(
        listen_of(ended_at="2022-03-05T10:00:00", ms_played=THREE_MINUTES),
        listen_of(ended_at="2022-03-05T10:33:00", ms_played=THREE_MINUTES),  # starts 30 min later
    )

    assert collector.result().count == 1


def test_the_order_of_the_entries_does_not_matter():
    listens = [
        listen_of(ended_at="2022-03-05T12:00:00", ms_played=THREE_MINUTES),
        listen_of(ended_at="2022-03-05T10:00:00", ms_played=THREE_MINUTES),
        listen_of(ended_at="2022-03-05T10:10:00", ms_played=THREE_MINUTES),
    ]

    assert collect(*listens).result() == collect(*reversed(listens)).result()


def test_started_at_is_in_the_requested_timezone():
    options = parse_options({"timezone": "Africa/Tunis"})
    collector = collect(
        listen_of(options, ended_at="2022-03-05T10:00:00", ms_played=THREE_MINUTES),
        timezone=options.timezone,
    )

    assert collector.result().longest.started_at == "2022-03-05T10:57:00+01:00"


def test_skips_do_not_count_and_no_plays_means_no_sessions():
    sessions = collect(listen_of(ms_played=1_000)).result()

    assert (sessions.count, sessions.average_ms, sessions.longest) == (0, 0, None)
