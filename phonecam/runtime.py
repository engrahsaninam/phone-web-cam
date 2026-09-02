from __future__ import annotations

from threading import Lock


class RuntimeStatus:
    def __init__(self) -> None:
        self._lock = Lock()
        self._stream_connected = False
        self._virtual_camera_device: str | None = None
        self._virtual_camera_error: str | None = None

    def set_stream(self, connected: bool) -> None:
        with self._lock:
            self._stream_connected = connected

    def set_virtual_camera(self, device: str | None, error: str | None) -> None:
        with self._lock:
            self._virtual_camera_device = device
            self._virtual_camera_error = error

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "stream_connected": self._stream_connected,
                "virtual_camera_active": self._virtual_camera_device is not None and self._virtual_camera_error is None,
                "virtual_camera_device": self._virtual_camera_device,
                "virtual_camera_error": self._virtual_camera_error,
            }
