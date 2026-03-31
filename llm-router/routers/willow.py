"""Willow proxy router — job-based API for containerized Claude Code.

Willow is a containerized Claude Code subscription running on the home server.
It exposes a job-based API (not OpenAI-compatible chat completions).

- Submit jobs: POST /v1/jobs
- Poll status:  GET /v1/jobs/{id}
- Health:       GET /health

Willow is NOT in the auto-routing chain. It is only accessible via explicit
X-Provider: willow header or these proxy endpoints.
"""

import logging
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from auth import ApiKey, validate_api_key_header

logger = logging.getLogger(__name__)

router = APIRouter(tags=["willow"])

WILLOW_URL = os.environ.get("WILLOW_URL", "http://willow:8013")


@router.post("/v1/willow/jobs")
async def submit_job(
    request: Request,
    api_key: ApiKey = Depends(validate_api_key_header),
):
    """Submit a job to Willow.

    Accepts JSON body with:
      - prompt (str, required)
      - session_id (str, optional)
      - working_directory (str, optional)
      - timeout (int, optional)
    """
    body = await request.json()

    prompt = body.get("prompt")
    if not prompt or not isinstance(prompt, str):
        raise HTTPException(status_code=422, detail="'prompt' is required and must be a string")

    logger.info(
        f"[Willow] Job submitted by key={api_key.name}, "
        f"prompt={prompt[:80]}{'...' if len(prompt) > 80 else ''}"
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{WILLOW_URL}/v1/jobs",
                json=body,
            )
    except (httpx.ConnectError, httpx.ConnectTimeout) as e:
        logger.error(f"[Willow] Unreachable: {e}")
        raise HTTPException(status_code=503, detail="Willow is unreachable")

    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get("/v1/willow/jobs/{job_id}")
async def get_job(
    job_id: str,
    api_key: ApiKey = Depends(validate_api_key_header),
):
    """Get job status and result from Willow."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{WILLOW_URL}/v1/jobs/{job_id}")
    except (httpx.ConnectError, httpx.ConnectTimeout) as e:
        logger.error(f"[Willow] Unreachable: {e}")
        raise HTTPException(status_code=503, detail="Willow is unreachable")

    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.get("/v1/willow/health")
async def health():
    """Health check — proxies to Willow's /health endpoint."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{WILLOW_URL}/health")
    except (httpx.ConnectError, httpx.ConnectTimeout) as e:
        logger.error(f"[Willow] Unreachable: {e}")
        raise HTTPException(status_code=503, detail="Willow is unreachable")

    return JSONResponse(content=response.json(), status_code=response.status_code)
