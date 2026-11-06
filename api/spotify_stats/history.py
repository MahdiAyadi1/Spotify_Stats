"""Reads track entries from the export ZIP, one history file at a time.

Only `Streaming_History_Audio_*.json` files are read. Podcast and audiobook
entries are skipped. Every track entry is yielded, whether it counts as a play
or as a skip: that decision belongs to the aggregation.

Only the fields the statistics need are kept. `ip_addr` and `conn_country`
are never read into a `TrackEntry`, never logged, never returned.
"""

import json
import zipfile
import zlib
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from fnmatch import fnmatchcase
from pathlib import PurePosixPath
from typing import IO

from spotify_stats.constants import (
    HISTORY_FILE_PATTERN,
    MAX_HISTORY_FILE_BYTES,
    MAX_TOTAL_HISTORY_BYTES,
)
from spotify_stats.platforms import platform_family


class InvalidExportError(ValueError):
    """The upload is not a usable Spotify extended streaming history export."""


class ExportTooLargeError(InvalidExportError):
    """The history files are larger than the limits protecting the function's memory."""


@dataclass(frozen=True, slots=True)
class TrackEntry:
    track_uri: str
    track_name: str
    artist_name: str
    ms_played: int
    ended_at: datetime  # timezone-aware UTC: when the track stopped playing
    album_name: str = ""
    reason_start: str = "unknown"
    reason_end: str = "unknown"
    shuffle: bool = False
    platform: str = "Other"  # family such as "iOS" or "Windows", see platforms.py
    offline: bool = False


def iter_track_entries(export_zip: IO[bytes]) -> Iterator[TrackEntry]:
    """Yield the track entries of every audio history file in the export.

    Raises InvalidExportError or ExportTooLargeError while iterating.
    """
    with _open_archive(export_zip) as archive:
        history_files = _audio_history_files(archive)
        if not history_files:
            raise InvalidExportError(f"No {HISTORY_FILE_PATTERN} file found in the ZIP.")

        total_bytes_read = 0
        for history_file in history_files:
            raw_history = _read_history_file(archive, history_file)
            total_bytes_read += len(raw_history)
            if total_bytes_read > MAX_TOTAL_HISTORY_BYTES:
                raise ExportTooLargeError(
                    f"The history files exceed {MAX_TOTAL_HISTORY_BYTES} bytes once unzipped."
                )
            yield from _parse_track_entries(raw_history, history_file.filename)


def count_audio_history_files(export_zip: IO[bytes]) -> int:
    """Number of audio history files in the export. Reads the ZIP's file list only."""
    with _open_archive(export_zip) as archive:
        return len(_audio_history_files(archive))


def _open_archive(export_zip: IO[bytes]) -> zipfile.ZipFile:
    try:
        return zipfile.ZipFile(export_zip)
    except zipfile.BadZipFile:
        raise InvalidExportError("The upload is not a ZIP file.") from None


def _audio_history_files(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    """Audio history files, matched on the file name so a parent folder does not matter."""
    return sorted(
        (
            member
            for member in archive.infolist()
            if not member.is_dir()
            and fnmatchcase(PurePosixPath(member.filename).name, HISTORY_FILE_PATTERN)
        ),
        key=lambda member: member.filename,
    )


def _read_history_file(archive: zipfile.ZipFile, history_file: zipfile.ZipInfo) -> bytes:
    """Read one history file, never more than MAX_HISTORY_FILE_BYTES once unzipped."""
    try:
        with archive.open(history_file) as stream:
            raw_history = stream.read(MAX_HISTORY_FILE_BYTES + 1)
    except (zipfile.BadZipFile, zlib.error):
        raise InvalidExportError(f"{history_file.filename} is corrupted.") from None
    if len(raw_history) > MAX_HISTORY_FILE_BYTES:
        raise ExportTooLargeError(
            f"{history_file.filename} exceeds {MAX_HISTORY_FILE_BYTES} bytes once unzipped."
        )
    return raw_history


def _parse_track_entries(raw_history: bytes, file_name: str) -> Iterator[TrackEntry]:
    try:
        entries = json.loads(raw_history)
    except ValueError:
        raise InvalidExportError(f"{file_name} is not valid JSON.") from None
    if not isinstance(entries, list):
        raise InvalidExportError(f"{file_name} is not a list of history entries.")

    for entry in entries:
        if not isinstance(entry, dict):
            raise InvalidExportError(f"{file_name} contains an entry that is not an object.")

        track_uri = entry.get("spotify_track_uri")
        track_name = entry.get("master_metadata_track_name")
        if track_uri is None or track_name is None:
            continue  # podcast episode or audiobook chapter

        ms_played = entry.get("ms_played")
        if not isinstance(ms_played, int):
            raise InvalidExportError(f"{file_name} contains a track entry without ms_played.")

        yield TrackEntry(
            track_uri=track_uri,
            track_name=track_name,
            artist_name=entry.get("master_metadata_album_artist_name") or "",
            ms_played=ms_played,
            ended_at=_parse_timestamp(entry.get("ts"), file_name),
            album_name=entry.get("master_metadata_album_album_name") or "",
            reason_start=entry.get("reason_start") or "unknown",
            reason_end=entry.get("reason_end") or "unknown",
            shuffle=entry.get("shuffle") is True,
            platform=platform_family(entry.get("platform")),
            offline=entry.get("offline") is True,
        )


def _parse_timestamp(timestamp: object, file_name: str) -> datetime:
    """Parse `ts` such as "2026-02-05T08:34:23Z" into an aware UTC datetime."""
    try:
        ended_at = datetime.fromisoformat(timestamp)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise InvalidExportError(
            f"{file_name} contains a track entry without a valid ts."
        ) from None
    return ended_at.replace(tzinfo=UTC) if ended_at.tzinfo is None else ended_at.astimezone(UTC)
