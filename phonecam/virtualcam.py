from __future__ import annotations

from threading import Lock
from typing import Any

from .runtime import RuntimeStatus


class VirtualCameraSink:
    """Lazily opens a system virtual camera and sends BGR frames to it."""

    def __init__(self, runtime_status: RuntimeStatus, fps: float = 30.0) -> None:
        self.runtime_status = runtime_status
        self.fps = fps
        self._lock = Lock()
        self._camera: Any | None = None
        self._shape: tuple[int, int] | None = None
        self._failed_for_session = False

    def reset(self) -> None:
        with self._lock:
            self._close_unlocked()
            self._failed_for_session = False
            self.runtime_status.set_virtual_camera(device=None, error=None)

    def send_bgr(self, frame: Any) -> None:
        if self._failed_for_session:
            return

        height, width = int(frame.shape[0]), int(frame.shape[1])
        with self._lock:
            try:
                if self._camera is None or self._shape != (height, width):
                    self._close_unlocked()
                    import pyvirtualcam

                    self._camera = pyvirtualcam.Camera(
                        width=width,
                        height=height,
                        fps=self.fps,
                        fmt=pyvirtualcam.PixelFormat.BGR,
                    )
                    self._shape = (height, width)
                    self.runtime_status.set_virtual_camera(device=self._camera.device, error=None)
                self._camera.send(frame)
            except Exception as exc:  # backend availability differs by machine
                self._close_unlocked()
                self._failed_for_session = True
                self.runtime_status.set_virtual_camera(
                    device=None,
                    error=f"Virtual camera unavailable: {exc}",
                )

    def close(self) -> None:
        with self._lock:
            self._close_unlocked()

    def _close_unlocked(self) -> None:
        if self._camera is not None:
            try:
                self._camera.close()
            finally:
                self._camera = None
                self._shape = None
