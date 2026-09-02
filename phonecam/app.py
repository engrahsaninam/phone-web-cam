from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .pairing import PairingToken
from .runtime import RuntimeStatus
from .webrtc import PeerManager

STATIC_DIR = Path(__file__).resolve().parent / "static"


class OfferPayload(BaseModel):
    sdp: str = Field(min_length=1, max_length=200_000)
    type: str = Field(pattern="^offer$")


def create_app(
    token: PairingToken | None = None,
    peer_manager: object | None = None,
    runtime_status: RuntimeStatus | None = None,
) -> FastAPI:
    runtime_status = runtime_status or RuntimeStatus()
    token = token or PairingToken(os.environ.get("PHONECAM_TOKEN") or PairingToken.create().value)
    manager = peer_manager or PeerManager(runtime_status)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        await manager.close()

    app = FastAPI(title="Phone Web Cam", docs_url=None, redoc_url=None, lifespan=lifespan)
    app.state.pairing_token = token
    app.state.peer_manager = manager
    app.state.runtime_status = runtime_status

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(self), microphone=()"
        response.headers["Cache-Control"] = "no-store"
        return response

    def require_token(candidate: str | None) -> None:
        if not token.matches(candidate):
            raise HTTPException(status_code=403, detail="Invalid pairing token")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.post("/api/offer")
    async def offer(payload: OfferPayload, token_value: str | None = Query(default=None, alias="token")):
        require_token(token_value)
        return await manager.handle_offer(payload.sdp, payload.type)

    @app.get("/api/status")
    async def status(token_value: str | None = Query(default=None, alias="token")):
        require_token(token_value)
        return runtime_status.snapshot()

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


app = create_app()
