"""POST /api/jobs/fetch – manual trigger for the fetch job."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional

from app.config import settings
from app.jobs.fetch_all import run_fetch_all

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _verify_token(x_api_token: Optional[str] = Header(default=None)) -> None:
    if x_api_token != settings.api_token:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Api-Token header")


@router.post("/fetch", dependencies=[Depends(_verify_token)])
async def trigger_fetch() -> dict:
    """Manually trigger a full data fetch for all sources."""
    summary = await run_fetch_all()
    return {"status": "done", "summary": summary}
