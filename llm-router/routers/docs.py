"""Docs API - Aggregates ADRs from Gitea repos."""
import os
import time
import base64
import logging
import re
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()

GITEA_URL = os.getenv("GITEA_URL", "https://gitea.server.unarmedpuppy.com")
GITEA_TOKEN = os.getenv("GITEA_TOKEN", "")
GITEA_ORG = "homelab"
CACHE_TTL = 300  # 5 minutes
CONTENT_CACHE_TTL = 60  # 1 minute

# In-memory caches
_repos_cache: dict = {"data": None, "expires": 0}
_content_cache: dict[str, dict] = {}


def _gitea_headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if GITEA_TOKEN:
        headers["Authorization"] = f"token {GITEA_TOKEN}"
    return headers


def _parse_adr_frontmatter(content: str) -> dict[str, str]:
    """Extract Date and Status from ADR markdown frontmatter/header lines."""
    result: dict[str, str] = {}
    for line in content.split("\n")[:20]:
        line = line.strip()
        if line.startswith("# "):
            result["title"] = line[2:].strip()
        match = re.match(r"^[-*]\s*\**(Date|Status)\**\s*:\s*(.+)", line, re.IGNORECASE)
        if match:
            result[match.group(1).lower()] = match.group(2).strip()
    return result


def _title_from_filename(name: str) -> str:
    """Derive a readable title from an ADR filename like 001-use-fastapi.md."""
    stem = name.rsplit(".", 1)[0]
    # Strip leading number prefix
    stem = re.sub(r"^\d+[-_]?", "", stem)
    return stem.replace("-", " ").replace("_", " ").title()


async def _fetch_repos_with_adrs() -> list[dict]:
    """Fetch all repos in the org and their ADR file listings from Gitea."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        # List all repos in the org
        repos_resp = await client.get(
            f"{GITEA_URL}/api/v1/orgs/{GITEA_ORG}/repos",
            headers=_gitea_headers(),
            params={"limit": 50},
        )
        if repos_resp.status_code != 200:
            logger.error(f"Gitea repos list failed: {repos_resp.status_code}")
            raise HTTPException(status_code=502, detail="Failed to fetch repos from Gitea")

        repos = repos_resp.json()
        results = []

        for repo in repos:
            repo_name = repo["name"]
            # Try to list docs/adrs directory
            adrs_resp = await client.get(
                f"{GITEA_URL}/api/v1/repos/{GITEA_ORG}/{repo_name}/contents/docs/adrs",
                headers=_gitea_headers(),
                params={"ref": "main"},
            )

            if adrs_resp.status_code != 200:
                continue

            adr_files = adrs_resp.json()
            if not isinstance(adr_files, list):
                continue

            adrs = []
            for f in adr_files:
                if not f.get("name", "").endswith(".md"):
                    continue

                # Fetch first ~30 lines for frontmatter parsing
                file_resp = await client.get(
                    f"{GITEA_URL}/api/v1/repos/{GITEA_ORG}/{repo_name}/contents/{f['path']}",
                    headers=_gitea_headers(),
                    params={"ref": "main"},
                )

                meta: dict[str, str] = {}
                if file_resp.status_code == 200:
                    file_data = file_resp.json()
                    raw = base64.b64decode(file_data.get("content", "")).decode("utf-8", errors="replace")
                    # Only parse first 30 lines for speed
                    preview = "\n".join(raw.split("\n")[:30])
                    meta = _parse_adr_frontmatter(preview)

                adrs.append({
                    "name": f["name"],
                    "path": f["path"],
                    "title": meta.get("title", _title_from_filename(f["name"])),
                    "date": meta.get("date", ""),
                    "status": meta.get("status", ""),
                })

            if adrs:
                results.append({
                    "repo": repo_name,
                    "description": repo.get("description", ""),
                    "adrs": sorted(adrs, key=lambda a: a["name"]),
                })

        results.sort(key=lambda r: r["repo"])
        return results


@router.get("/repos")
async def get_docs_repos():
    """List all repos with their ADRs."""
    now = time.time()
    if _repos_cache["data"] is not None and now < _repos_cache["expires"]:
        return _repos_cache["data"]

    data = await _fetch_repos_with_adrs()
    _repos_cache["data"] = data
    _repos_cache["expires"] = now + CACHE_TTL
    return data


@router.get("/content/{repo}/{path:path}")
async def get_doc_content(repo: str, path: str):
    """Return raw markdown content for a single ADR."""
    cache_key = f"{repo}/{path}"
    now = time.time()

    cached = _content_cache.get(cache_key)
    if cached and now < cached["expires"]:
        return {"content": cached["content"], "repo": repo, "path": path}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{GITEA_URL}/api/v1/repos/{GITEA_ORG}/{repo}/contents/{path}",
            headers=_gitea_headers(),
            params={"ref": "main"},
        )

        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail=f"File not found: {repo}/{path}")
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Gitea error: {resp.status_code}")

        data = resp.json()
        content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")

    _content_cache[cache_key] = {"content": content, "expires": now + CONTENT_CACHE_TTL}
    return {"content": content, "repo": repo, "path": path}
