from spotify_stats.constants import MIN_PLAY_MS


def test_play_threshold_is_30_seconds():
    assert MIN_PLAY_MS == 30_000
