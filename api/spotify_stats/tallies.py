"""Counts plays, listening time and skips per group (track, artist, album)."""

from collections.abc import Callable, Hashable
from dataclasses import dataclass
from datetime import date
from typing import Generic, TypeVar

from spotify_stats.listen import Listen

Label = TypeVar("Label")


@dataclass(slots=True)
class ListeningTally:
    plays: int = 0
    ms_played: int = 0
    skips: int = 0
    first_played: date | None = None  # local date of the earliest play

    @property
    def skip_rate(self) -> float:
        listens = self.plays + self.skips
        return round(self.skips / listens, 4) if listens else 0.0

    def add(self, listen: Listen) -> None:
        if not listen.is_play:
            self.skips += 1
            return
        self.plays += 1
        self.ms_played += listen.entry.ms_played
        played_on = listen.local_ended_at.date()
        if self.first_played is None or played_on < self.first_played:
            self.first_played = played_on


class GroupedTallies(Generic[Label]):
    """One tally per group. `key_of` returns None for listens that belong to no group."""

    def __init__(
        self,
        key_of: Callable[[Listen], Hashable | None],
        label_of: Callable[[Listen], Label],
    ) -> None:
        self._key_of = key_of
        self._label_of = label_of  # called once per group, on its first listen
        self._groups: dict[Hashable, tuple[Label, ListeningTally]] = {}

    def add(self, listen: Listen) -> None:
        key = self._key_of(listen)
        if key is None:
            return
        group = self._groups.get(key)
        if group is None:
            group = self._groups[key] = (self._label_of(listen), ListeningTally())
        group[1].add(listen)

    def groups(self) -> list[tuple[Label, ListeningTally]]:
        return list(self._groups.values())


def track_tallies() -> GroupedTallies[tuple[str, str]]:
    """Label: (track, artist). The name and artist of a track are those of its first listen."""
    return GroupedTallies(
        key_of=lambda listen: listen.track_key,
        label_of=lambda listen: (listen.entry.track_name, listen.entry.artist_name),
    )


def artist_tallies() -> GroupedTallies[str]:
    return GroupedTallies(
        key_of=lambda listen: listen.entry.artist_name or None,
        label_of=lambda listen: listen.entry.artist_name,
    )


def album_tallies() -> GroupedTallies[tuple[str, str]]:
    """Label: (album, artist). Albums are grouped with their artist: names repeat across artists."""
    return GroupedTallies(
        key_of=lambda listen: (
            (listen.entry.album_name, listen.entry.artist_name) if listen.entry.album_name else None
        ),
        label_of=lambda listen: (listen.entry.album_name, listen.entry.artist_name),
    )
