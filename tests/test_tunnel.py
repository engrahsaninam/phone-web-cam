from phonecam.tunnel import extract_tunnel_url


def test_extract_tunnel_url_from_cloudflared_output():
    line = '2026-09-02 INF |  https://silver-river.trycloudflare.com  |'
    assert extract_tunnel_url(line) == 'https://silver-river.trycloudflare.com'


def test_extract_tunnel_url_ignores_unrelated_lines():
    assert extract_tunnel_url('2026-09-02 INF Starting metrics server') is None

import pytest

from phonecam.tunnel import cloudflared_download_url


def test_cloudflared_windows_amd64_download_url():
    assert cloudflared_download_url('Windows', 'AMD64').endswith('/cloudflared-windows-amd64.exe')


def test_cloudflared_windows_arm64_download_url():
    assert cloudflared_download_url('Windows', 'ARM64').endswith('/cloudflared-windows-arm64.exe')


def test_cloudflared_download_rejects_non_windows_v1():
    with pytest.raises(RuntimeError):
        cloudflared_download_url('Linux', 'x86_64')
