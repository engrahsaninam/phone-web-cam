from __future__ import annotations

import asyncio
from typing import Any

from .runtime import RuntimeStatus
from .virtualcam import VirtualCameraSink


class PeerManager:
    """Owns the current WebRTC peer and forwards incoming video to the sink."""

    def __init__(self, runtime_status: RuntimeStatus, sink: VirtualCameraSink | None = None) -> None:
        self.runtime_status = runtime_status
        self.sink = sink or VirtualCameraSink(runtime_status)
        self._pcs: set[Any] = set()
        self._tasks: set[asyncio.Task[Any]] = set()
        self._lock = asyncio.Lock()

    async def handle_offer(self, sdp: str, offer_type: str) -> dict[str, str]:
        from aiortc import RTCPeerConnection, RTCSessionDescription

        async with self._lock:
            await self._close_peers_only()
            self.sink.reset()

            pc = RTCPeerConnection()
            self._pcs.add(pc)

            @pc.on("connectionstatechange")
            async def on_connectionstatechange() -> None:
                state = pc.connectionState
                self.runtime_status.set_stream(state == "connected")
                if state in {"failed", "closed", "disconnected"}:
                    await pc.close()
                    self._pcs.discard(pc)

            @pc.on("track")
            def on_track(track: Any) -> None:
                if track.kind != "video":
                    return
                task = asyncio.create_task(self._consume_video(track))
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)

            offer = RTCSessionDescription(sdp=sdp, type=offer_type)
            await pc.setRemoteDescription(offer)
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            return {
                "sdp": pc.localDescription.sdp,
                "type": pc.localDescription.type,
            }

    async def _consume_video(self, track: Any) -> None:
        try:
            while True:
                frame = await track.recv()
                image = frame.to_ndarray(format="bgr24")
                self.sink.send_bgr(image)
        except Exception as exc:
            try:
                from aiortc.mediastreams import MediaStreamError
            except Exception:
                MediaStreamError = ()  # type: ignore[assignment]
            if MediaStreamError and not isinstance(exc, MediaStreamError):
                raise
        finally:
            self.runtime_status.set_stream(False)

    async def close(self) -> None:
        async with self._lock:
            await self._close_peers_only()
            for task in list(self._tasks):
                task.cancel()
            if self._tasks:
                await asyncio.gather(*self._tasks, return_exceptions=True)
            self._tasks.clear()
            self.sink.close()
            self.runtime_status.set_stream(False)

    async def _close_peers_only(self) -> None:
        if self._pcs:
            await asyncio.gather(*(pc.close() for pc in list(self._pcs)), return_exceptions=True)
        self._pcs.clear()
        self.runtime_status.set_stream(False)
