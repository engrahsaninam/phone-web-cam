from __future__ import annotations

import platform
import re
import shutil
import tempfile
import urllib.request
from pathlib import Path

_TUNNEL_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com", re.IGNORECASE)
_RELEASE_BASE = "https://github.com/cloudflare/cloudflared/releases/latest/download"


def extract_tunnel_url(line: str) -> str | None:
    match = _TUNNEL_URL_RE.search(line)
    return match.group(0) if match else None


def cloudflared_download_url(system: str | None = None, machine: str | None = None) -> str:
    system = system or platform.system()
    machine = (machine or platform.machine()).lower()

    if system != "Windows":
        raise RuntimeError("Phone Web Cam V1 currently auto-installs cloudflared on Windows only.")

    if machine in {"arm64", "aarch64"}:
        asset = "cloudflared-windows-arm64.exe"
    else:
        asset = "cloudflared-windows-amd64.exe"
    return f"{_RELEASE_BASE}/{asset}"


def ensure_cloudflared(tools_dir: Path) -> Path:
    existing = shutil.which("cloudflared")
    if existing:
        return Path(existing)

    tools_dir.mkdir(parents=True, exist_ok=True)
    target = tools_dir / "cloudflared.exe"
    if target.exists():
        return target

    url = cloudflared_download_url()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".exe", dir=tools_dir) as tmp:
        temp_path = Path(tmp.name)
    try:
        print("Downloading Cloudflare Tunnel helper (first run only)...")
        urllib.request.urlretrieve(url, temp_path)
        temp_path.replace(target)
    finally:
        temp_path.unlink(missing_ok=True)
    return target
