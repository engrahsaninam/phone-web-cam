(() => {
  "use strict";

  const preview = document.getElementById("preview");
  const placeholder = document.getElementById("placeholder");
  const liveBadge = document.getElementById("liveBadge");
  const statusEl = document.getElementById("status");
  const virtualCamStatus = document.getElementById("virtualCamStatus");
  const resolutionEl = document.getElementById("resolution");
  const startBtn = document.getElementById("startBtn");
  const switchBtn = document.getElementById("switchBtn");
  const stopBtn = document.getElementById("stopBtn");

  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");

  let pc = null;
  let stream = null;
  let facingMode = "environment";
  let pollTimer = null;
  let starting = false;

  const resolutions = {
    "480p": { width: 854, height: 480 },
    "720p": { width: 1280, height: 720 },
    "1080p": { width: 1920, height: 1080 },
  };

  function setStatus(message, kind = "") {
    statusEl.textContent = message;
    statusEl.className = `status ${kind}`.trim();
  }

  function constraints() {
    const selected = resolutions[resolutionEl.value] || resolutions["720p"];
    return {
      audio: false,
      video: {
        width: { ideal: selected.width },
        height: { ideal: selected.height },
        frameRate: { ideal: 30, max: 30 },
        facingMode: { ideal: facingMode },
      },
    };
  }

  function waitForIceGatheringComplete(peer) {
    if (peer.iceGatheringState === "complete") return Promise.resolve();
    return new Promise((resolve) => {
      const listener = () => {
        if (peer.iceGatheringState === "complete") {
          peer.removeEventListener("icegatheringstatechange", listener);
          resolve();
        }
      };
      peer.addEventListener("icegatheringstatechange", listener);
    });
  }

  async function stopSession(updateStatus = true) {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
    if (pc) {
      pc.close();
      pc = null;
    }
    if (stream) {
      for (const track of stream.getTracks()) track.stop();
      stream = null;
    }
    preview.srcObject = null;
    placeholder.classList.remove("hidden");
    liveBadge.classList.add("hidden");
    startBtn.disabled = false;
    switchBtn.disabled = true;
    stopBtn.disabled = true;
    resolutionEl.disabled = false;
    if (updateStatus) setStatus("Stopped");
  }

  async function pollStatus() {
    if (!token) return;
    try {
      const response = await fetch(`/api/status?token=${encodeURIComponent(token)}`, { cache: "no-store" });
      if (!response.ok) return;
      const data = await response.json();
      if (data.virtual_camera_active) {
        virtualCamStatus.textContent = `PC virtual camera ready: ${data.virtual_camera_device}`;
        virtualCamStatus.className = "good";
      } else if (data.virtual_camera_error) {
        virtualCamStatus.textContent = `${data.virtual_camera_error}. Install OBS Studio on the PC, then stop and start the camera again.`;
        virtualCamStatus.className = "error";
      } else if (data.stream_connected) {
        virtualCamStatus.textContent = "Video reached the PC; opening the virtual camera...";
        virtualCamStatus.className = "muted";
      }
    } catch (_) {
      // Status polling is informative only; it should never interrupt the stream.
    }
  }

  async function startSession() {
    if (starting) return;
    if (!token) {
      setStatus("Invalid pairing link. Scan the QR code shown on the PC.", "error");
      return;
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatus("This browser does not support camera capture.", "error");
      return;
    }

    starting = true;
    startBtn.disabled = true;
    setStatus("Requesting camera permission...");

    try {
      await stopSession(false);
      startBtn.disabled = true;
      stream = await navigator.mediaDevices.getUserMedia(constraints());
      preview.srcObject = stream;
      placeholder.classList.add("hidden");
      liveBadge.classList.remove("hidden");

      pc = new RTCPeerConnection();
      for (const track of stream.getVideoTracks()) pc.addTrack(track, stream);

      pc.addEventListener("connectionstatechange", () => {
        const state = pc ? pc.connectionState : "closed";
        if (state === "connected") setStatus("Connected to PC", "good");
        if (state === "failed" || state === "disconnected") setStatus(`Connection ${state}`, "error");
      });

      const offer = await pc.createOffer({ offerToReceiveAudio: false, offerToReceiveVideo: false });
      await pc.setLocalDescription(offer);
      await waitForIceGatheringComplete(pc);

      setStatus("Connecting to PC...");
      const response = await fetch(`/api/offer?token=${encodeURIComponent(token)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sdp: pc.localDescription.sdp, type: pc.localDescription.type }),
      });
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`PC rejected connection (${response.status}): ${detail}`);
      }

      const answer = await response.json();
      await pc.setRemoteDescription(answer);
      switchBtn.disabled = false;
      stopBtn.disabled = false;
      resolutionEl.disabled = true;
      pollTimer = setInterval(pollStatus, 1000);
      await pollStatus();
    } catch (error) {
      console.error(error);
      await stopSession(false);
      const name = error && error.name ? error.name : "Error";
      if (name === "NotAllowedError") {
        setStatus("Camera permission was denied. Allow camera access and try again.", "error");
      } else if (name === "NotFoundError") {
        setStatus("No phone camera was found.", "error");
      } else {
        setStatus(error && error.message ? error.message : "Could not start camera", "error");
      }
    } finally {
      starting = false;
      if (!stream) startBtn.disabled = false;
    }
  }

  startBtn.addEventListener("click", startSession);
  stopBtn.addEventListener("click", () => stopSession(true));
  switchBtn.addEventListener("click", async () => {
    facingMode = facingMode === "environment" ? "user" : "environment";
    setStatus("Switching camera...");
    await startSession();
  });

  window.addEventListener("pagehide", () => {
    if (pc) pc.close();
    if (stream) for (const track of stream.getTracks()) track.stop();
  });

  if (!token) {
    setStatus("Invalid pairing link. Scan the QR code shown on the PC.", "error");
    startBtn.disabled = true;
  }
})();
