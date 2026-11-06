"""The whole job of POST /api/stats, without any Azure types.

Takes the uploaded bytes and returns the HTTP status and the JSON body.
Messages in error bodies mention file names and limits only, never listening data.
"""

import io
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from http import HTTPStatus
from typing import Any

from spotify_stats.aggregation import compute_listening_stats
from spotify_stats.history import (
    ExportTooLargeError,
    InvalidExportError,
    count_audio_history_files,
    iter_track_entries,
)
from spotify_stats.options import InvalidOptionsError, parse_options


@dataclass(frozen=True, slots=True)
class StatsResult:
    status: HTTPStatus
    body: dict[str, Any]


def build_stats_result(export_zip: bytes, query: Mapping[str, str] | None = None) -> StatsResult:
    """`query` holds the optional query parameters described in `spotify_stats.options`."""
    try:
        options = parse_options(query or {})
        listening_stats = compute_listening_stats(
            iter_track_entries(io.BytesIO(export_zip)),
            options,
            history_files=count_audio_history_files(io.BytesIO(export_zip)),
        )
    except ExportTooLargeError as error:
        return StatsResult(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": str(error)})
    except (InvalidExportError, InvalidOptionsError) as error:
        return StatsResult(HTTPStatus.BAD_REQUEST, {"error": str(error)})
    return StatsResult(HTTPStatus.OK, asdict(listening_stats))
