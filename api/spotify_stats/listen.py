"""One track entry, classified and placed in the requested timezone."""

from dataclasses import dataclass
from datetime import datetime

from spotify_stats.history import TrackEntry
from spotify_stats.options import StatsOptions


@dataclass(frozen=True, slots=True)
class Listen:
    entry: TrackEntry
    is_play: bool  # False: a skip, shorter than options.min_play_ms
    local_ended_at: datetime
    track_key: str  # the Spotify URI, or "name + artist" when duplicates are merged


def make_listen(entry: TrackEntry, options: StatsOptions) -> Listen:
    if options.merge_duplicates:
        track_key = f"{entry.track_name.casefold()}\x1f{entry.artist_name.casefold()}"
    else:
        track_key = entry.track_uri
    return Listen(
        entry=entry,
        is_play=entry.ms_played >= options.min_play_ms,
        local_ended_at=entry.ended_at.astimezone(options.timezone),
        track_key=track_key,
    )
