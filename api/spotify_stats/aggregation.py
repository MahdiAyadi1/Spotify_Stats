"""Turns track entries into statistics (top tracks, most skipped).

Pure functions only: no Azure imports, no I/O.

A play is an entry listened to for at least MIN_PLAY_MS; shorter entries are
skips. Skips are not plays and add nothing to the listening time.
Tracks are grouped by `track_uri`, not by name.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from spotify_stats.constants import MIN_PLAY_MS
from spotify_stats.history import TrackEntry


@dataclass(frozen=True, slots=True)
class ListeningSummary:
    total_plays: int
    total_ms_played: int
    distinct_tracks: int


@dataclass(frozen=True, slots=True)
class RankedTrack:
    rank: int
    track: str
    artist: str
    plays: int
    ms_played: int


@dataclass(frozen=True, slots=True)
class SkippedTrack:
    rank: int
    track: str
    artist: str
    skips: int


@dataclass(frozen=True, slots=True)
class ListeningStats:
    """Field names match the JSON contract of POST /api/stats (see `dataclasses.asdict`)."""

    summary: ListeningSummary
    top_tracks: list[RankedTrack]
    most_skipped: list[SkippedTrack]


@dataclass(slots=True)
class _TrackTally:
    track: str
    artist: str
    plays: int = 0
    ms_played: int = 0
    skips: int = 0


def compute_listening_stats(entries: Iterable[TrackEntry]) -> ListeningStats:
    tallies: dict[str, _TrackTally] = {}
    for entry in entries:
        tally = tallies.get(entry.track_uri)
        if tally is None:
            tally = tallies[entry.track_uri] = _TrackTally(entry.track_name, entry.artist_name)
        if entry.ms_played >= MIN_PLAY_MS:
            tally.plays += 1
            tally.ms_played += entry.ms_played
        else:
            tally.skips += 1

    played_tracks = [tally for tally in tallies.values() if tally.plays]
    skipped_tracks = [tally for tally in tallies.values() if tally.skips]

    return ListeningStats(
        summary=ListeningSummary(
            total_plays=sum(tally.plays for tally in played_tracks),
            total_ms_played=sum(tally.ms_played for tally in played_tracks),
            distinct_tracks=len(played_tracks),
        ),
        top_tracks=_rank_by_plays(played_tracks),
        most_skipped=_rank_by_skips(skipped_tracks),
    )


def _rank_by_plays(played_tracks: list[_TrackTally]) -> list[RankedTrack]:
    """Most plays first; ties go to the longer listening time, then to the name."""
    ordered = sorted(
        played_tracks,
        key=lambda tally: (-tally.plays, -tally.ms_played, tally.track.casefold(), tally.artist),
    )
    return [
        RankedTrack(rank, tally.track, tally.artist, tally.plays, tally.ms_played)
        for rank, tally in enumerate(ordered, start=1)
    ]


def _rank_by_skips(skipped_tracks: list[_TrackTally]) -> list[SkippedTrack]:
    """Most skips first; ties go to the track with fewer plays, then to the name."""
    ordered = sorted(
        skipped_tracks,
        key=lambda tally: (-tally.skips, tally.plays, tally.track.casefold(), tally.artist),
    )
    return [
        SkippedTrack(rank, tally.track, tally.artist, tally.skips)
        for rank, tally in enumerate(ordered, start=1)
    ]