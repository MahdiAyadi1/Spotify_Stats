"""Helpers that build TrackEntry and Listen objects for the tests."""

from datetime import UTC, datetime

from spotify_stats.history import TrackEntry
from spotify_stats.listen import Listen, make_listen
from spotify_stats.options import StatsOptions


def utc(timestamp: str) -> datetime:
    """utc("2022-03-05T10:00:00") -> an aware UTC datetime."""
    return datetime.fromisoformat(timestamp).replace(tzinfo=UTC)


def track_entry(
    track="Let Down",
    artist="Radiohead",
    ms_played=200_000,
    uri=None,
    album="OK Computer",
    ended_at="2022-03-05T10:00:00",
    reason_start="trackdone",
    reason_end="trackdone",
    shuffle=False,
    platform="iOS",
    offline=False,
) -> TrackEntry:
    return TrackEntry(
        track_uri=uri or f"spotify:track:{track}",
        track_name=track,
        artist_name=artist,
        ms_played=ms_played,
        ended_at=utc(ended_at),
        album_name=album,
        reason_start=reason_start,
        reason_end=reason_end,
        shuffle=shuffle,
        platform=platform,
        offline=offline,
    )


def listen_of(options: StatsOptions | None = None, **entry_fields) -> Listen:
    return make_listen(track_entry(**entry_fields), options or StatsOptions())
