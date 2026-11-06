"""The most played track of each year."""

from dataclasses import dataclass

from spotify_stats.listen import Listen


@dataclass(frozen=True, slots=True)
class YearlyTopTrack:
    year: int
    track: str
    artist: str
    plays: int
    ms_played: int


class YearlyTopTracksCollector:
    def __init__(self) -> None:
        self._labels: dict[str, tuple[str, str]] = {}  # track_key -> (track, artist)
        self._counts: dict[tuple[int, str], list[int]] = {}  # (year, track_key) -> [plays, ms]

    def add(self, listen: Listen) -> None:
        if not listen.is_play:
            return
        self._labels.setdefault(
            listen.track_key, (listen.entry.track_name, listen.entry.artist_name)
        )
        counts = self._counts.setdefault((listen.local_ended_at.year, listen.track_key), [0, 0])
        counts[0] += 1
        counts[1] += listen.entry.ms_played

    def result(self) -> list[YearlyTopTrack]:
        """Ties go to the longer listening time, then to the name."""
        best_by_year: dict[int, YearlyTopTrack] = {}
        for (year, track_key), (plays, ms_played) in self._counts.items():
            track, artist = self._labels[track_key]
            candidate = YearlyTopTrack(year, track, artist, plays, ms_played)
            best = best_by_year.get(year)
            if best is None or _order(candidate) < _order(best):
                best_by_year[year] = candidate
        return [best_by_year[year] for year in sorted(best_by_year)]


def _order(top_track: YearlyTopTrack) -> tuple[int, int, str, str]:
    return (-top_track.plays, -top_track.ms_played, top_track.track.casefold(), top_track.artist)
