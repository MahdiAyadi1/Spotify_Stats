"""Tracks played the most within a single day or a single week (weeks start on Monday)."""

from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta

from spotify_stats.constants import OBSESSION_LIMIT
from spotify_stats.listen import Listen


@dataclass(frozen=True, slots=True)
class Obsession:
    rank: int
    track: str
    artist: str
    period_start: str  # the day, or the Monday of the week, as YYYY-MM-DD
    plays: int


@dataclass(frozen=True, slots=True)
class Obsessions:
    days: list[Obsession]
    weeks: list[Obsession]


class ObsessionsCollector:
    def __init__(self) -> None:
        self._labels: dict[str, tuple[str, str]] = {}  # track_key -> (track, artist)
        self._plays_per_day: Counter[tuple[str, date]] = Counter()
        self._plays_per_week: Counter[tuple[str, date]] = Counter()

    def add(self, listen: Listen) -> None:
        if not listen.is_play:
            return
        self._labels.setdefault(
            listen.track_key, (listen.entry.track_name, listen.entry.artist_name)
        )
        day = listen.local_ended_at.date()
        self._plays_per_day[(listen.track_key, day)] += 1
        self._plays_per_week[(listen.track_key, day - timedelta(days=day.weekday()))] += 1

    def result(self) -> Obsessions:
        return Obsessions(
            days=self._rank(self._plays_per_day), weeks=self._rank(self._plays_per_week)
        )

    def _rank(self, plays_per_period: Counter[tuple[str, date]]) -> list[Obsession]:
        """Each track appears once, with its best period; ties go to the earlier period."""
        best_period: dict[str, tuple[int, date]] = {}
        for (track_key, period_start), plays in plays_per_period.items():
            best = best_period.get(track_key)
            if best is None or (-plays, period_start) < (-best[0], best[1]):
                best_period[track_key] = (plays, period_start)

        ordered = sorted(
            best_period.items(),
            key=lambda item: (-item[1][0], item[1][1], self._labels[item[0]][0].casefold()),
        )[:OBSESSION_LIMIT]
        return [
            Obsession(rank, *self._labels[track_key], period_start.isoformat(), plays)
            for rank, (track_key, (plays, period_start)) in enumerate(ordered, start=1)
        ]
