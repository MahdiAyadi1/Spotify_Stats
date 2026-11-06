from datetime import date

import pytest

from spotify_stats.options import InvalidOptionsError, StatsOptions, parse_options


def test_no_parameters_give_the_defaults():
    assert parse_options({}) == StatsOptions()


def test_every_parameter_can_be_set():
    options = parse_options(
        {
            "min_play_ms": "45000",
            "min_skips": "3",
            "timezone": "Africa/Tunis",
            "date_from": "2022-01-01",
            "date_to": "2022-12-31",
            "merge_duplicates": "TRUE",
        }
    )

    assert options.min_play_ms == 45_000
    assert options.min_skips == 3
    assert options.timezone_name == "Africa/Tunis"
    assert (options.date_from, options.date_to) == (date(2022, 1, 1), date(2022, 12, 31))
    assert options.merge_duplicates is True


def test_empty_values_count_as_not_given():
    assert parse_options({"timezone": "", "date_from": "", "min_skips": ""}) == StatsOptions()


def test_the_date_range_includes_both_ends():
    options = parse_options({"date_from": "2022-01-01", "date_to": "2022-01-31"})

    assert options.includes(date(2022, 1, 1))
    assert options.includes(date(2022, 1, 31))
    assert not options.includes(date(2021, 12, 31))
    assert not options.includes(date(2022, 2, 1))


@pytest.mark.parametrize(
    "query",
    [
        {"timezon": "Africa/Tunis"},
        {"min_play_ms": "abc"},
        {"min_play_ms": "-1"},
        {"min_play_ms": "600001"},
        {"min_skips": "0"},
        {"timezone": "Mars/Base"},
        {"timezone": "../etc/passwd"},
        {"date_from": "2022-13-01"},
        {"date_from": "2022-02-01", "date_to": "2022-01-01"},
        {"merge_duplicates": "maybe"},
    ],
)
def test_invalid_parameters_are_rejected(query):
    with pytest.raises(InvalidOptionsError):
        parse_options(query)
