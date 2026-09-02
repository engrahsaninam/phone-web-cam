from __future__ import annotations

import platform
import re
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

_TUNNEL_URL_RE = re.compile(r"https://([a-z0-9-]+)\.trycloudflare\.com", re.IGNORECASE)
_RELEASE_BASE = "https://github.com/cloudflare/cloudflared/releases/latest/download"
_MIN_CLOUDFLARED_BYTES = 1_000_000


def extract_tunnel_url(line: str) -> str | None:
    match = _TUNNEL_URL_RE.search(line)
    if not match:
        return None
    # cloudflared logs the Quick Tunnel API endpoint before the actual
    # randomly-generated public hostname. Never treat that API URL as usable.
    if match.group(1).lower() == "api":
        return None
    return match.group(0)


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


def build_curl_download_command(
    url: str,
    target: Path,
    curl_executable: str = "curl.exe",
) -> list[str]:
    return [
        curl_executable,
        "--location",
        "--fail",
        "--progress-bar",
        "--connect-timeout",
        "15",
        "--max-time",
        "180",
        "--retry",
        "2",
        "--retry-delay",
        "2",
        "--output",
        str(target),
        url,
    ]


def _download_with_urllib(url: str, target: Path) -> None:
    print("Windows curl.exe was not found; using Python downloader...")
    with urllib.request.urlopen(url, timeout=30) as response, target.open("wb") as output:
        total_header = response.headers.get("Content-Length")
        total = int(total_header) if total_header and total_header.isdigit() else 0
        downloaded = 0
        last_percent = -1

        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)
            downloaded += len(chunk)

            if total:
                percent = min(100, int(downloaded * 100 / total))
                if percent >= last_percent + 5 or percent == 100:
                    print(f"  Downloaded {percent}% ({downloaded / 1_048_576:.1f} MB)")
                    last_percent = percent
            else:
                print(f"  Downloaded {downloaded / 1_048_576:.1f} MB", end="\r", flush=True)


def _download_cloudflared(url: str, target: Path) -> None:
    curl = shutil.which("curl.exe") or shutil.which("curl")
    if curl:
        print("Downloading Cloudflare Tunnel helper (first run only)...")
        print("You should see download progress below. This is normally about a minute or less.")
        result = subprocess.run(build_curl_download_command(url, target, curl), check=False)
        if result.returncode != 0:
            raise RuntimeError(
                "Cloudflare Tunnel helper download failed. "
                f"curl exited with code {result.returncode}.\n"
                f"You can also download it manually from:\n{url}"
            )
    else:
        print("Downloading Cloudflare Tunnel helper (first run only)...")
        _download_with_urllib(url, target)

    if not target.exists() or target.stat().st_size < _MIN_CLOUDFLARED_BYTES:
        raise RuntimeError(
            "Cloudflare Tunnel helper download was incomplete. "
            "Delete the partial file and run start.bat again.\n"
            f"Manual download URL:\n{url}"
        )


def ensure_cloudflared(tools_dir: Path) -> Path:
    existing = shutil.which("cloudflared")
    if existing:
        return Path(existing)

    tools_dir.mkdir(parents=True, exist_ok=True)
    target = tools_dir / "cloudflared.exe"
    if target.exists() and target.stat().st_size >= _MIN_CLOUDFLARED_BYTES:
        return target
    if target.exists():
        target.unlink(missing_ok=True)

    url = cloudflared_download_url()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".exe", dir=tools_dir) as tmp:
        temp_path = Path(tmp.name)
    try:
        _download_cloudflared(url, temp_path)
        temp_path.replace(target)
    finally:
        temp_path.unlink(missing_ok=True)
    return target
