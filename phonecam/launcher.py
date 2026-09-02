from __future__ import annotations

import os
import queue
from collections import deque
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import quote

from .pairing import PairingToken
from .tunnel import ensure_cloudflared, extract_tunnel_url

ROOT = Path(__file__).resolve().parents[1]
PORT = 8765


def build_pairing_url(base_url: str, token: str) -> str:
    return f"{base_url.rstrip('/')}/?token={quote(token, safe='')}"


def _wait_for_port(host: str, port: int, timeout_seconds: float = 20.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"Local server did not start on {host}:{port}")


def _pump_lines(
    pipe,
    output: queue.Queue[str | None],
    history: deque[str],
) -> None:
    try:
        for line in iter(pipe.readline, ""):
            clean = line.rstrip()
            history.append(clean)
            try:
                output.put_nowait(clean)
            except queue.Full:
                pass
    finally:
        try:
            output.put_nowait(None)
        except queue.Full:
            pass


def _tunnel_error(message: str, history: deque[str]) -> RuntimeError:
    useful = [line for line in history if line.strip()]
    if not useful:
        return RuntimeError(message)
    tail = "\n".join(useful[-12:])
    return RuntimeError(f"{message}\n\ncloudflared log tail:\n{tail}")


def _print_qr(url: str) -> None:
    try:
        import qrcode

        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except Exception:
        print("QR display unavailable; open the URL manually.")


def _terminate(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def main() -> int:
    token = PairingToken.create()
    env = os.environ.copy()
    env["PHONECAM_TOKEN"] = token.value
    env["PYTHONUNBUFFERED"] = "1"

    server_proc: subprocess.Popen | None = None
    tunnel_proc: subprocess.Popen | None = None
    try:
        print("Starting Phone Web Cam...")
        server_proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "phonecam.app:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(PORT),
                "--log-level",
                "warning",
            ],
            cwd=ROOT,
            env=env,
        )
        _wait_for_port("127.0.0.1", PORT)

        cloudflared = ensure_cloudflared(ROOT / ".tools")
        tunnel_proc = subprocess.Popen(
            [
                str(cloudflared),
                "tunnel",
                "--url",
                f"http://127.0.0.1:{PORT}",
                "--no-autoupdate",
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        assert tunnel_proc.stdout is not None
        lines: queue.Queue[str | None] = queue.Queue(maxsize=200)
        tunnel_history: deque[str] = deque(maxlen=40)
        threading.Thread(
            target=_pump_lines,
            args=(tunnel_proc.stdout, lines, tunnel_history),
            daemon=True,
        ).start()

        tunnel_url: str | None = None
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline and tunnel_proc.poll() is None:
            try:
                line = lines.get(timeout=0.5)
            except queue.Empty:
                continue
            if line is None:
                break
            maybe_url = extract_tunnel_url(line)
            if maybe_url:
                tunnel_url = maybe_url
                break

        if not tunnel_url:
            raise _tunnel_error(
                "Could not create the temporary HTTPS tunnel. Check your internet connection and try again.",
                tunnel_history,
            )

        pairing_url = build_pairing_url(tunnel_url, token.value)
        print("\n============================================================")
        print("PHONE WEB CAM IS READY")
        print("1. Keep this window open")
        print("2. Scan the QR code with your phone")
        print("3. Tap Start Camera and allow camera permission")
        print("4. In Zoom/Teams/etc choose 'OBS Virtual Camera'")
        print("============================================================\n")
        _print_qr(pairing_url)
        print(f"\nPhone URL:\n{pairing_url}\n")
        print("Press Ctrl+C to stop. No video is recorded or stored by this app.\n")

        while True:
            if server_proc.poll() is not None:
                raise RuntimeError("The local receiver stopped unexpectedly.")
            if tunnel_proc.poll() is not None:
                raise _tunnel_error("The HTTPS tunnel stopped unexpectedly.", tunnel_history)
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopping Phone Web Cam...")
        return 0
    except Exception as exc:
        print(f"\nERROR: {exc}")
        return 1
    finally:
        _terminate(tunnel_proc)
        _terminate(server_proc)


if __name__ == "__main__":
    raise SystemExit(main())
