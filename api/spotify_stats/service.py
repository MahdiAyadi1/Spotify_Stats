"""The whole job of POST /api/stats, without any Azure types.

Takes the uploaded bytes and returns the HTTP status and the JSON body.
Messages in error bodies mention file names and limits only, never listening data.
"""

import io
from dataclasses import asdict, dataclass
from http import HTTPStatus
from typing import Any

from spotify_stats.aggregation import compute_listening_stats
from spotify_stats.history import ExportTooLargeError, InvalidExportError, iter_track_entries


@dataclass(frozen=True, slots=True)
class StatsResult:
    status: HTTPStatus
    body: dict[str, Any]


def build_stats_result(export_zip: bytes) -> StatsResult:
    try:
        listening_stats = compute_listening_stats(iter_track_entries(io.BytesIO(export_zip)))
    except ExportTooLargeError as error:
        return StatsResult(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": str(error)})
    except InvalidExportError as error:
        return StatsResult(HTTPStatus.BAD_REQUEST, {"error": str(error)})
    return StatsResult(HTTPStatus.OK, asdict(listening_stats))
