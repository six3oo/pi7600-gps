"""Minimal GPS-only API for Waveshare SIM7600.

This module is intentionally stripped down to only query and return GNSS/GPS
information from the SIM7600 via AT commands.

Endpoints:
- GET /gps : Query SIM7600 GNSS info and return a parsed fix payload.
- GET /health : Basic liveness check.

Environment:
- SIM7600_PORT: optional serial device path (default auto-detect /dev/ttyUSB*).
- SIM7600_BAUD: optional baudrate (default 115200).
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Query

from pi7600 import SIM7600GPS


app = FastAPI(title="pi7600-gps", description="GPS-only API for SIM7600", version="1.0.0")

gps = SIM7600GPS(
    port=(os.getenv("SIM7600_PORT") or None),
    baudrate=int(os.getenv("SIM7600_BAUD", "115200")),
)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/gps")
def get_gps(
    timeout: float = Query(default=5.0, ge=0.5, le=30.0),
    enable_gnss: bool = Query(default=True),
):
    try:
        fix = gps.get_fix(timeout=timeout, enable_gnss=enable_gnss)
        return fix.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
