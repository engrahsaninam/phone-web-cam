# Phone Web Cam

Turn your phone camera into a Windows webcam **without installing any app on the phone**.

Your phone opens a temporary HTTPS page in its normal browser, grants camera permission, and sends video to the PC over WebRTC. The PC forwards incoming frames to an installed virtual-camera device such as **OBS Virtual Camera**.

## What you need

- Windows 10/11 PC
- Python 3.10 or newer
- Internet access while starting the app (for the temporary HTTPS tunnel)
- OBS Studio installed on the PC if you want the feed to appear as a camera in Zoom / Teams / Meet / Discord
- Phone and PC on the same Wi-Fi/LAN is strongly recommended for V1

**Nothing needs to be installed on the phone.**

## Quick start

1. Install Python 3.10+ on the PC and enable **Add Python to PATH**.
2. Install OBS Studio on the PC. OBS includes `OBS Virtual Camera` on Windows.
3. Download or clone this repository.
4. Double-click **`start.bat`**.
5. On first run, the launcher creates a local `.venv`, installs dependencies, and downloads Cloudflare's `cloudflared` helper into `.tools/`.
6. A QR code and temporary HTTPS URL appear in the terminal.
7. Scan the QR code with your phone camera and open the link.
8. Tap **Start Camera** and allow camera access.
9. In Zoom, Teams, Google Meet, Discord, etc., choose **OBS Virtual Camera** as the camera.

Keep the `start.bat` window open while using the camera. Press `Ctrl+C` to stop.

## Phone controls

- **Start Camera** — grants permission and starts streaming.
- **Switch Camera** — switches between rear and front cameras.
- **Quality** — 480p, 720p (recommended), or 1080p.
- **Stop** — stops camera capture and closes the WebRTC connection.

## How it works

```text
Phone browser
  getUserMedia(camera)
       |
       | WebRTC video
       v
Python / aiortc receiver on PC
       |
       | BGR frames
       v
pyvirtualcam
       |
       v
OBS Virtual Camera
       |
       v
Zoom / Teams / Meet / Discord / etc.

Signaling + phone webpage:
Phone <-> temporary HTTPS trycloudflare.com URL <-> localhost FastAPI server
```

## Privacy and security

- No recording code; incoming video frames are not saved.
- A fresh cryptographically random pairing token is generated every time the launcher starts.
- Offer and status APIs reject requests without that exact token.
- The temporary HTTPS URL changes each run.
- The phone requests camera only; microphone permission is disabled.
- HTTP responses are sent with `no-store`, `no-referrer`, and camera-only permission headers.

## Current V1 limitations

- Windows-focused launcher.
- One active phone stream at a time.
- Best on the same local network.
- No audio forwarding.
- Depends on an existing virtual camera on the PC (OBS Virtual Camera recommended).
