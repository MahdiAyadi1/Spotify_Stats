"""New tracks and new artists per month, from the date each was first played."""

from dataclasses import dataclass

from spotify_stats.rankings import RankedArtist, RankedTrack
from spotify_stats.timeline import months_between


@dataclass(frozen=True, slots=True)
class MonthlyDiscovery:
    month: str  # YYYY-MM
    new_tracks: int
    new_artists: int


def discoveries_per_month(
    top_tracks: list[RankedTrack], top_artists: list[RankedArtist]
) -> list[MonthlyDiscovery]:
    """Every month from the first to the last discovery, empty months included.

    "New" means first played within the analysed range, whatever came before it.
    """
    new_tracks = _count_by_month(track.first_played for track in top_tracks)
    new_artists = _count_by_month(artist.first_played for artist in top_artists)
    month_names = sorted(new_tracks | new_artists)
    if not month_names:
        return []
    return [
        MonthlyDiscovery(month, new_tracks.get(month, 0), new_artists.get(month, 0))
        for month in months_between(month_names[0], month_names[-1])
    ]


def _count_by_month(first_played_dates) -> dict[str, int]:
    counts: dict[str, int] = {}
    for first_played in first_played_dates:
        if first_played:
            counts[first_played[:7]] = counts.get(first_played[:7], 0) + 1
    return counts
