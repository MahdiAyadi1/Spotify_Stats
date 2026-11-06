"""How music is started and stopped, on which device, shuffled or not, online or offline."""

from dataclasses import dataclass

from spotify_stats.listen import Listen


@dataclass(frozen=True, slots=True)
class ReasonCount:
    reason: str  # as written by Spotify, e.g. "trackdone", "fwdbtn", "clickrow"
    plays: int
    skips: int


@dataclass(frozen=True, slots=True)
class PlatformUsage:
    platform: str
    plays: int
    ms_played: int


@dataclass(frozen=True, slots=True)
class ShuffleUsage:
    shuffled_plays: int
    other_plays: int


@dataclass(frozen=True, slots=True)
class OfflineUsage:
    offline_plays: int
    online_plays: int


@dataclass(frozen=True, slots=True)
class ListeningHabits:
    reason_start: list[ReasonCount]
    reason_end: list[ReasonCount]
    platforms: list[PlatformUsage]
    shuffle: ShuffleUsage
    offline: OfflineUsage


class HabitsCollector:
    def __init__(self) -> None:
        self._reason_start: dict[str, list[int]] = {}  # reason -> [plays, skips]
        self._reason_end: dict[str, list[int]] = {}
        self._platforms: dict[str, list[int]] = {}  # platform -> [plays, ms_played]
        self._shuffled_plays = 0
        self._offline_plays = 0
        self._plays = 0

    def add(self, listen: Listen) -> None:
        entry = listen.entry
        outcome = 0 if listen.is_play else 1  # index into [plays, skips]
        self._reason_start.setdefault(entry.reason_start, [0, 0])[outcome] += 1
        self._reason_end.setdefault(entry.reason_end, [0, 0])[outcome] += 1
        if not listen.is_play:
            return
        self._plays += 1
        self._shuffled_plays += entry.shuffle
        self._offline_plays += entry.offline
        platform = self._platforms.setdefault(entry.platform, [0, 0])
        platform[0] += 1
        platform[1] += entry.ms_played

    def result(self) -> ListeningHabits:
        return ListeningHabits(
            reason_start=_reason_counts(self._reason_start),
            reason_end=_reason_counts(self._reason_end),
            platforms=[
                PlatformUsage(platform, *counts)
                for platform, counts in sorted(
                    self._platforms.items(), key=lambda item: (-item[1][0], item[0])
                )
            ],
            shuffle=ShuffleUsage(self._shuffled_plays, self._plays - self._shuffled_plays),
            offline=OfflineUsage(self._offline_plays, self._plays - self._offline_plays),
        )


def _reason_counts(counts_by_reason: dict[str, list[int]]) -> list[ReasonCount]:
    """Most frequent reason first."""
    return [
        ReasonCount(reason, *counts)
        for reason, counts in sorted(
            counts_by_reason.items(), key=lambda item: (-sum(item[1]), item[0])
        )
    ]
