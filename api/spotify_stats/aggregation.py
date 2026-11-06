"""Turns track entries into statistics, in a single pass.

Pure functions only: no Azure imports, no I/O.

A play is an entry listened to for at least `options.min_play_ms`; shorter entries
are skips. Skips are not plays and add nothing to the listening time.
Each statistic is its own small collector (tallies, timeline, sessions, ...) and
every listen is handed to all of them, so memory depends on the number of distinct
tracks, months and days, not on the number of entries.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from spotify_stats.discovery import MonthlyDiscovery, discoveries_per_month
from spotify_stats.habits import HabitsCollector, ListeningHabits
from spotify_stats.history import TrackEntry
from spotify_stats.listen import Listen, make_listen
from spotify_stats.obsessions import Obsessions, ObsessionsCollector
from spotify_stats.options import StatsOptions
from spotify_stats.rankings import (
    RankedAlbum,
    RankedArtist,
    RankedTrack,
    SkippedTrack,
    rank_most_skipped,
    rank_top_albums,
    rank_top_artists,
    rank_top_tracks,
)
from spotify_stats.sessions import ListeningSessions, SessionsCollector
from spotify_stats.tallies import album_tallies, artist_tallies, track_tallies
from spotify_stats.timeline import Clock, Timeline, TimelineCollector
from spotify_stats.yearly import YearlyTopTrack, YearlyTopTracksCollector


@dataclass(frozen=True, slots=True)
class AppliedOptions:
    min_play_ms: int
    min_skips: int
    timezone: str
    date_from: str | None
    date_to: str | None
    merge_duplicates: bool


@dataclass(frozen=True, slots=True)
class ExportOverview:
    """About the whole export, before the date filter."""

    history_files: int
    track_entries: int
    first_entry: str | None  # local date, YYYY-MM-DD
    last_entry: str | None


@dataclass(frozen=True, slots=True)
class ListeningSummary:
    total_plays: int
    total_ms_played: int
    total_skips: int
    distinct_tracks: int
    distinct_artists: int


@dataclass(frozen=True, slots=True)
class ListeningStats:
    """Field names match the JSON contract of POST /api/stats (see `dataclasses.asdict`)."""

    options: AppliedOptions
    overview: ExportOverview
    summary: ListeningSummary
    top_tracks: list[RankedTrack]
    top_artists: list[RankedArtist]
    top_albums: list[RankedAlbum]
    most_skipped: list[SkippedTrack]
    yearly_top_tracks: list[YearlyTopTrack]
    discovery: list[MonthlyDiscovery]
    timeline: Timeline
    clock: Clock
    obsessions: Obsessions
    sessions: ListeningSessions
    habits: ListeningHabits


class _ListenCollector(Protocol):
    def add(self, listen: Listen) -> None: ...


def compute_listening_stats(
    entries: Iterable[TrackEntry],
    options: StatsOptions | None = None,
    history_files: int = 0,
) -> ListeningStats:
    options = options or StatsOptions()
    tracks = track_tallies()
    artists = artist_tallies()
    albums = album_tallies()
    timeline = TimelineCollector()
    yearly_top_tracks = YearlyTopTracksCollector()
    obsessions = ObsessionsCollector()
    sessions = SessionsCollector(options.timezone)
    habits = HabitsCollector()
    collectors: tuple[_ListenCollector, ...] = (
        tracks, artists, albums, timeline, yearly_top_tracks, obsessions, sessions, habits,
    )  # fmt: skip

    track_entries = 0
    first_ended_at = last_ended_at = None
    for entry in entries:
        track_entries += 1
        if first_ended_at is None or entry.ended_at < first_ended_at:
            first_ended_at = entry.ended_at
        if last_ended_at is None or entry.ended_at > last_ended_at:
            last_ended_at = entry.ended_at

        listen = make_listen(entry, options)
        if not options.includes(listen.local_ended_at.date()):
            continue
        for collector in collectors:
            collector.add(listen)

    track_groups = tracks.groups()
    top_tracks = rank_top_tracks(track_groups)
    top_artists = rank_top_artists(artists.groups())
    return ListeningStats(
        options=AppliedOptions(
            min_play_ms=options.min_play_ms,
            min_skips=options.min_skips,
            timezone=options.timezone_name,
            date_from=options.date_from.isoformat() if options.date_from else None,
            date_to=options.date_to.isoformat() if options.date_to else None,
            merge_duplicates=options.merge_duplicates,
        ),
        overview=ExportOverview(
            history_files=history_files,
            track_entries=track_entries,
            first_entry=_local_date(first_ended_at, options),
            last_entry=_local_date(last_ended_at, options),
        ),
        summary=ListeningSummary(
            total_plays=sum(tally.plays for _, tally in track_groups),
            total_ms_played=sum(tally.ms_played for _, tally in track_groups),
            total_skips=sum(tally.skips for _, tally in track_groups),
            distinct_tracks=len(top_tracks),
            distinct_artists=len(top_artists),
        ),
        top_tracks=top_tracks,
        top_artists=top_artists,
        top_albums=rank_top_albums(albums.groups()),
        most_skipped=rank_most_skipped(track_groups, options.min_skips),
        yearly_top_tracks=yearly_top_tracks.result(),
        discovery=discoveries_per_month(top_tracks, top_artists),
        timeline=timeline.timeline(),
        clock=timeline.clock(),
        obsessions=obsessions.result(),
        sessions=sessions.result(),
        habits=habits.result(),
    )


def _local_date(ended_at, options: StatsOptions) -> str | None:
    return ended_at.astimezone(options.timezone).date().isoformat() if ended_at else None
