"""Groups the free-text `platform` field of the export into a few device families."""

_FAMILY_PREFIXES = (
    # "web_player windows 10;chrome ..." must be tested before the operating systems.
    (("web_player",), "Web player"),
    (("ios",), "iOS"),
    (("android",), "Android"),
    (("windows",), "Windows"),
    (("os x", "osx", "macos"), "macOS"),
    (("linux",), "Linux"),
)


def platform_family(platform: str | None) -> str:
    name = (platform or "").strip().casefold()
    for prefixes, family in _FAMILY_PREFIXES:
        if name.startswith(prefixes):
            return family
    return "Other"
