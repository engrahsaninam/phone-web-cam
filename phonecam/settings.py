from __future__ import annotations

_RESOLUTIONS = {
    "480p": (854, 480),
    "720p": (1280, 720),
    "1080p": (1920, 1080),
}
_VALID_FACING_MODES = {"user", "environment"}


def get_video_constraints(resolution: str, facing_mode: str) -> dict[str, object]:
    if resolution not in _RESOLUTIONS:
        raise ValueError(f"Unsupported resolution: {resolution}")
    if facing_mode not in _VALID_FACING_MODES:
        raise ValueError(f"Unsupported facing mode: {facing_mode}")

    width, height = _RESOLUTIONS[resolution]
    return {
        "width": {"ideal": width},
        "height": {"ideal": height},
        "frameRate": {"ideal": 30, "max": 30},
        "facingMode": {"ideal": facing_mode},
    }
