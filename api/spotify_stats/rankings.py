"""Ranked lists built from the tallies: top tracks, artists, albums and most skipped."""

from dataclasses import dataclass

from spotify_stats.tallies import ListeningTally


@dataclass(frozen=True, slots=True)
class RankedTrack:
    rank: int
    track: str
    artist: str
    plays: int
    ms_played: int
    skips: int
    skip_rate: float
    first_played: str | None  # local date, YYYY-MM-DD


@dataclass(frozen=True, slots=True)
class SkippedTrack:
    rank: int
    track: str
    artist: str
    skips: int
    plays: int
    skip_rate: float


@dataclass(frozen=True, slots=True)
class RankedArtist:
    rank: int
    artist: str
    plays: int
    ms_played: int
    skips: int
    skip_rate: float
    first_played: str | None


@dataclass(frozen=True, slots=True)
class RankedAlbum:
    rank: int
    album: str
    artist: str
    plays: int
    ms_played: int


def rank_top_tracks(groups: list[tuple[tuple[str, str], ListeningTally]]) -> list[RankedTrack]:
    """Most plays first; ties go to the longer listening time, then to the name."""
    played = sorted(
        (group for group in groups if group[1].plays),
        key=lambda group: _by_plays(group[1], *group[0]),
    )
    return [
        RankedTrack(
            rank, track, artist, tally.plays, tally.ms_played, tally.skips, tally.skip_rate,
            _iso(tally),
        )
        for rank, ((track, artist), tally) in enumerate(played, start=1)
    ]


def rank_most_skipped(
    groups: list[tuple[tuple[str, str], ListeningTally]], min_skips: int
) -> list[SkippedTrack]:
    """Most skips first; ties go to the track with fewer plays, then to the name."""
    skipped = sorted(
        (group for group in groups if group[1].skips >= min_skips),
        key=lambda group: (-group[1].skips, group[1].plays, group[0][0].casefold(), group[0][1]),
    )
    return [
        SkippedTrack(rank, track, artist, tally.skips, tally.plays, tally.skip_rate)
        for rank, ((track, artist), tally) in enumerate(skipped, start=1)
    ]


def rank_top_artists(groups: list[tuple[str, ListeningTally]]) -> list[RankedArtist]:
    """Most plays first; ties go to the longer listening time, then to the name."""
    played = sorted(
        (group for group in groups if group[1].plays),
        key=lambda group: (-group[1].plays, -group[1].ms_played, group[0].casefold(), group[0]),
    )
    return [
        RankedArtist(
            rank, artist, tally.plays, tally.ms_played, tally.skips, tally.skip_rate, _iso(tally)
        )
        for rank, (artist, tally) in enumerate(played, start=1)
    ]


def rank_top_albums(groups: list[tuple[tuple[str, str], ListeningTally]]) -> list[RankedAlbum]:
    """Most plays first; ties go to the longer listening time, then to the name."""
    played = sorted(
        (group for group in groups if group[1].plays),
        key=lambda group: _by_plays(group[1], *group[0]),
    )
    return [
        RankedAlbum(rank, album, artist, tally.plays, tally.ms_played)
        for rank, ((album, artist), tally) in enumerate(played, start=1)
    ]


def _by_plays(tally: ListeningTally, name: str, other_name: str) -> tuple[int, int, str, str]:
    return (-tally.plays, -tally.ms_played, name.casefold(), other_name)


def _iso(tally: ListeningTally) -> str | None:
    return tally.first_played.isoformat() if tally.first_played else None
