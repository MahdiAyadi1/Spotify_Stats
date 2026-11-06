"""Listening sessions: consecutive plays with no gap longer than SESSION_GAP_MS between them.

Only plays count. A play starts at `ts` minus `ms_played`, since `ts` is when it stopped.
"""

from array import array
from dataclasses import dataclass
from datetime import datetime, tzinfo

from spotify_stats.constants import SESSION_GAP_MS
from spotify_stats.listen import Listen


@dataclass(frozen=True, slots=True)
class LongestSession:
    started_at: str  # ISO 8601 in the requested timezone
    duration_ms: int  # from the start of the first play to the end of the last
    plays: int


@dataclass(frozen=True, slots=True)
class ListeningSessions:
    count: int
    average_ms: int
    longest: LongestSession | None


class SessionsCollector:
    def __init__(self, timezone: tzinfo) -> None:
        self._timezone = timezone
        self._started_ms = array("q")
        self._ended_ms = array("q")

    def add(self, listen: Listen) -> None:
        if not listen.is_play:
            return
        ended_ms = round(listen.entry.ended_at.timestamp() * 1000)
        self._started_ms.append(ended_ms - listen.entry.ms_played)
        self._ended_ms.append(ended_ms)

    def result(self) -> ListeningSessions:
        order = sorted(range(len(self._started_ms)), key=self._started_ms.__getitem__)
        sessions: list[tuple[int, int, int]] = []  # (started_ms, ended_ms, plays)
        for index in order:
            started_ms, ended_ms = self._started_ms[index], self._ended_ms[index]
            if sessions and started_ms - sessions[-1][1] <= SESSION_GAP_MS:
                first_started_ms, last_ended_ms, plays = sessions[-1]
                sessions[-1] = (first_started_ms, max(last_ended_ms, ended_ms), plays + 1)
            else:
                sessions.append((started_ms, ended_ms, 1))

        if not sessions:
            return ListeningSessions(count=0, average_ms=0, longest=None)

        durations = [ended_ms - started_ms for started_ms, ended_ms, _ in sessions]
        longest_index = max(range(len(sessions)), key=lambda i: (durations[i], -sessions[i][0]))
        longest_started_ms, _, longest_plays = sessions[longest_index]
        return ListeningSessions(
            count=len(sessions),
            average_ms=round(sum(durations) / len(sessions)),
            longest=LongestSession(
                started_at=datetime.fromtimestamp(
                    longest_started_ms / 1000, tz=self._timezone
                ).isoformat(timespec="seconds"),
                duration_ms=durations[longest_index],
                plays=longest_plays,
            ),
        )
