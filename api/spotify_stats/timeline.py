"""Plays and listening time per month, per year, per hour of the day and per weekday.

Only plays count. Everything follows the requested timezone and the time the track stopped.
"""

from collections.abc import Iterator
from dataclasses import dataclass

from spotify_stats.listen import Listen


@dataclass(frozen=True, slots=True)
class MonthlyListening:
    month: str  # YYYY-MM
    plays: int
    ms_played: int


@dataclass(frozen=True, slots=True)
class YearlyListening:
    year: int
    plays: int
    ms_played: int


@dataclass(frozen=True, slots=True)
class HourlyListening:
    hour: int  # 0-23
    plays: int
    ms_played: int


@dataclass(frozen=True, slots=True)
class WeekdayListening:
    weekday: int  # 0 = Monday ... 6 = Sunday
    plays: int
    ms_played: int


@dataclass(frozen=True, slots=True)
class Timeline:
    months: list[MonthlyListening]  # every month from the first to the last, empty ones included
    years: list[YearlyListening]


@dataclass(frozen=True, slots=True)
class Clock:
    hours: list[HourlyListening]  # always 24 entries
    weekdays: list[WeekdayListening]  # always 7 entries


def months_between(first_month: str, last_month: str) -> Iterator[str]:
    """Every month from first_month to last_month, both as YYYY-MM and included."""
    year, month = int(first_month[:4]), int(first_month[5:7])
    last_year, last = int(last_month[:4]), int(last_month[5:7])
    while (year, month) <= (last_year, last):
        yield f"{year:04d}-{month:02d}"
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)


class TimelineCollector:
    def __init__(self) -> None:
        self._months: dict[str, list[int]] = {}  # month -> [plays, ms_played]
        self._hours = [[0, 0] for _ in range(24)]
        self._weekdays = [[0, 0] for _ in range(7)]

    def add(self, listen: Listen) -> None:
        if not listen.is_play:
            return
        ended_at = listen.local_ended_at
        ms_played = listen.entry.ms_played
        month = self._months.setdefault(f"{ended_at.year:04d}-{ended_at.month:02d}", [0, 0])
        for counts in (month, self._hours[ended_at.hour], self._weekdays[ended_at.weekday()]):
            counts[0] += 1
            counts[1] += ms_played

    def timeline(self) -> Timeline:
        if not self._months:
            return Timeline(months=[], years=[])
        month_names = sorted(self._months)
        months = [
            MonthlyListening(month, *self._months.get(month, (0, 0)))
            for month in months_between(month_names[0], month_names[-1])
        ]
        years: dict[int, list[int]] = {}
        for month in months:
            counts = years.setdefault(int(month.month[:4]), [0, 0])
            counts[0] += month.plays
            counts[1] += month.ms_played
        return Timeline(
            months=months,
            years=[YearlyListening(year, *counts) for year, counts in sorted(years.items())],
        )

    def clock(self) -> Clock:
        return Clock(
            hours=[HourlyListening(hour, *counts) for hour, counts in enumerate(self._hours)],
            weekdays=[WeekdayListening(day, *counts) for day, counts in enumerate(self._weekdays)],
        )
