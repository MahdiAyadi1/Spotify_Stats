import pytest

from spotify_stats.platforms import platform_family


@pytest.mark.parametrize(
    ("platform", "family"),
    [
        ("ios", "iOS"),
        ("iOS 14.4 (iPhone12,1)", "iOS"),
        ("Android OS 11 API 30 (samsung, SM-G991B)", "Android"),
        ("Windows 10 (10.0.19044; x64)", "Windows"),
        ("OS X 12.4.0 [arm 2]", "macOS"),
        ("osx", "macOS"),
        ("Linux", "Linux"),
        ("web_player windows 10;chrome 101;desktop", "Web player"),
        ("cast_tv", "Other"),
        ("", "Other"),
        (None, "Other"),
    ],
)
def test_platform_family(platform, family):
    assert platform_family(platform) == family
