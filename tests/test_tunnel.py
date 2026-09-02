from pathlib import Path

import pytest

from phonecam.tunnel import (
    build_curl_download_command,
    cloudflared_download_url,
    extract_tunnel_url,
)


def test_extract_tunnel_url_from_cloudflared_output():
    line = '2026-09-02 INF |  https://silver-river.trycloudflare.com  |'
    assert extract_tunnel_url(line) == 'https://silver-river.trycloudflare.com'


def test_extract_tunnel_url_ignores_unrelated_lines():
    assert extract_tunnel_url('2026-09-02 INF Starting metrics server') is None


def test_cloudflared_windows_amd64_download_url():
    assert cloudflared_download_url('Windows', 'AMD64').endswith('/cloudflared-windows-amd64.exe')


def test_cloudflared_windows_arm64_download_url():
    assert cloudflared_download_url('Windows', 'ARM64').endswith('/cloudflared-windows-arm64.exe')


def test_cloudflared_download_rejects_non_windows_v1():
    with pytest.raises(RuntimeError):
        cloudflared_download_url('Linux', 'x86_64')


def test_extract_tunnel_url_ignores_quick_tunnel_api_endpoint():
    line = '2026-09-02 INF Requesting new quick Tunnel on https://api.trycloudflare.com'
    assert extract_tunnel_url(line) is None


def test_cloudflared_curl_command_has_progress_timeout_and_retries(tmp_path: Path):
    target = tmp_path / "cloudflared.exe"
    command = build_curl_download_command("https://example.com/cloudflared.exe", target)

    assert command[0] == "curl.exe"
    assert "--progress-bar" in command
    assert "--connect-timeout" in command
    assert "--max-time" in command
    assert "--retry" in command
    assert "--location" in command
    assert str(target) in command


def test_cloudflared_curl_command_allows_slow_download_and_resumes(tmp_path: Path):
    target = tmp_path / "cloudflared.exe"
    command = build_curl_download_command("https://example.com/cloudflared.exe", target)

    max_time_index = command.index("--max-time")
    connect_timeout_index = command.index("--connect-timeout")
    continue_index = command.index("--continue-at")

    assert command[max_time_index + 1] == "600"
    assert command[connect_timeout_index + 1] == "30"
    assert command[continue_index + 1] == "-"
