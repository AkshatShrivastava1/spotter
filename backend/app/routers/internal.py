"""Endpoints for infrastructure, not the app."""

import hmac

from fastapi import APIRouter, Header, HTTPException

from ..config import get_settings
from ..scheduler import run_nudges_once

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/run-nudges")
def run_nudges(x_cron_secret: str = Header("")):
    """Run one pass of the nudge engine. Called by an external cron (see .github/workflows/nudges.yml)
    so nudges still fire on hosts that put idle servers to sleep."""
    secret = get_settings().cron_secret
    if not secret:
        raise HTTPException(404, "not found")
    if not hmac.compare_digest(x_cron_secret, secret):
        raise HTTPException(401, "bad secret")
    return {"sent": run_nudges_once()}
