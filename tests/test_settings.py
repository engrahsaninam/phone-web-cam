import pytest

from phonecam.settings import get_video_constraints


def test_720p_constraints_default_to_rear_camera():
    constraints = get_video_constraints('720p', 'environment')
    assert constraints['width']['ideal'] == 1280
    assert constraints['height']['ideal'] == 720
    assert constraints['facingMode']['ideal'] == 'environment'


def test_invalid_resolution_is_rejected():
    with pytest.raises(ValueError):
        get_video_constraints('4k', 'environment')
