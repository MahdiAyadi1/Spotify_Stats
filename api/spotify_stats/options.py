"""Options of POST /api/stats, read from the query string. All are optional.

min_play_ms       listening needed to count as a play (default 30000)
min_skips         skips a track needs to appear in `most_skipped` (default 1)
timezone          IANA name such as Africa/Tunis; months, hours and days follow it (default UTC)
date_from/date_to YYYY-MM-DD, inclusive, in that timezone; filters every statistic
merge_duplicates  true: group tracks by name and artist instead of by Spotify URI
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, tzinfo
from zoneinfo import ZoneInfo

from spotify_stats.constants import MIN_PLAY_MS

MAX_MIN_PLAY_MS = 10 * 60 * 1000

_PARAMETER_NAMES = frozenset(
    {"min_play_ms", "min_skips", "timezone", "date_from", "date_to", "merge_duplicates"}
)


class InvalidOptionsError(ValueError):
    """A query parameter is unknown or has an invalid value."""


@dataclass(frozen=True, slots=True)
class StatsOptions:
    min_play_ms: int = MIN_PLAY_MS
    min_skips: int = 1
    timezone_name: str = "UTC"
    timezone: tzinfo = UTC
    date_from: date | None = None
    date_to: date | None = None
    merge_duplicates: bool = False

    def includes(self, played_on: date) -> bool:
        return (self.date_from is None or played_on >= self.date_from) and (
            self.date_to is None or played_on <= self.date_to
        )


def parse_options(query: Mapping[str, str]) -> StatsOptions:
    unknown_names = sorted(set(query) - _PARAMETER_NAMES)
    if unknown_names:
        raise InvalidOptionsError(f"Unknown parameter: {', '.join(unknown_names)}.")

    timezone_name = query.get("timezone") or "UTC"
    date_from = _parse_date(query, "date_from")
    date_to = _parse_date(query, "date_to")
    if date_from and date_to and date_from > date_to:
        raise InvalidOptionsError("date_from must not be after date_to.")

    return StatsOptions(
        min_play_ms=_parse_int(query, "min_play_ms", MIN_PLAY_MS, 0, MAX_MIN_PLAY_MS),
        min_skips=_parse_int(query, "min_skips", default=1, minimum=1),
        timezone_name=timezone_name,
        timezone=_parse_timezone(timezone_name),
        date_from=date_from,
        date_to=date_to,
        merge_duplicates=_parse_bool(query, "merge_duplicates"),
    )


def _parse_int(
    query: Mapping[str, str], name: str, default: int, minimum: int, maximum: int | None = None
) -> int:
    if not query.get(name):
        return default
    try:
        value = int(query[name])
    except ValueError:
        raise InvalidOptionsError(f"{name} must be an integer.") from None
    if value < minimum or (maximum is not None and value > maximum):
        upper_bound = f" and at most {maximum}" if maximum is not None else ""
        raise InvalidOptionsError(f"{name} must be at least {minimum}{upper_bound}.")
    return value


def _parse_timezone(timezone_name: str) -> tzinfo:
    if timezone_name == "UTC":
        return UTC
    try:
        return ZoneInfo(timezone_name)
    except (KeyError, ValueError, OSError):
        raise InvalidOptionsError(f"Unknown timezone: {timezone_name}.") from None


def _parse_date(query: Mapping[str, str], name: str) -> date | None:
    if not query.get(name):
        return None
    try:
        return date.fromisoformat(query[name])
    except ValueError:
        raise InvalidOptionsError(f"{name} must be a date like 2022-01-31.") from None


def _parse_bool(query: Mapping[str, str], name: str) -> bool:
    value = (query.get(name) or "false").casefold()
    if value not in {"true", "false"}:
        raise InvalidOptionsError(f"{name} must be true or false.")
    return value == "true"
