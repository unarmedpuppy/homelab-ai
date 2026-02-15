"""Service feed polling for Frigate, Immich, and Mealie."""
import os
import time
import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

FRIGATE_URL = os.getenv("FRIGATE_URL", "http://frigate:5000")
IMMICH_URL = os.getenv("IMMICH_URL", "http://immich-server:2283")
IMMICH_API_KEY = os.getenv("IMMICH_API_KEY", "")
MEALIE_URL = os.getenv("MEALIE_URL", "http://mealie:9000")

# Simple TTL cache: key -> (expires_at, data)
_cache: dict[str, tuple[float, list[dict]]] = {}


def _get_cached(key: str) -> list[dict] | None:
    entry = _cache.get(key)
    if entry and time.time() < entry[0]:
        return entry[1]
    return None


def _set_cached(key: str, data: list[dict], ttl: int):
    _cache[key] = (time.time() + ttl, data)


def _relative_time(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            m = seconds // 60
            return f"{m}m ago"
        elif seconds < 86400:
            h = seconds // 3600
            return f"{h}h ago"
        else:
            d = seconds // 86400
            return f"{d}d ago"
    except Exception:
        return ""


async def fetch_frigate_events(limit: int = 10, after_epoch: float | None = None) -> list[dict]:
    cached = _get_cached("frigate_events")
    if cached is not None:
        return cached

    items: list[dict] = []
    try:
        params: dict = {"limit": limit}
        if after_epoch:
            params["after"] = int(after_epoch)

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{FRIGATE_URL}/api/events", params=params)
            resp.raise_for_status()
            events = resp.json()

        for ev in events:
            label = (ev.get("label") or "object").replace("_", " ").title()
            camera = (ev.get("camera") or "unknown").replace("_", " ").title()
            ts = ev.get("start_time", 0)
            iso_ts = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            rel = _relative_time(iso_ts)

            items.append({
                "id": f"frigate-{ev.get('id', ts)}",
                "service": "frigate",
                "icon": "video.fill",
                "title": f"{label} detected",
                "description": f"{camera} — {rel}" if rel else camera,
                "timestamp": iso_ts,
                "deepLink": "jenquisthome://service/frigate",
                "status": "completed",
            })

    except Exception as e:
        logger.debug(f"Frigate fetch failed (expected if offline): {e}")

    _set_cached("frigate_events", items, ttl=60)
    return items


async def fetch_immich_recent(limit: int = 10) -> list[dict]:
    cached = _get_cached("immich_recent")
    if cached is not None:
        return cached

    items: list[dict] = []
    if not IMMICH_API_KEY:
        _set_cached("immich_recent", items, ttl=120)
        return items

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{IMMICH_URL}/api/search/metadata",
                json={"order": "desc", "take": limit},
                headers={"x-api-key": IMMICH_API_KEY},
            )
            resp.raise_for_status()
            data = resp.json()

        assets = data.get("assets", {}).get("items", [])
        for asset in assets:
            is_video = asset.get("type") == "VIDEO"
            filename = asset.get("originalFileName", "Unknown")
            ts = asset.get("createdAt", "")

            items.append({
                "id": f"immich-{asset.get('id', '')}",
                "service": "immich",
                "icon": "video.fill" if is_video else "photo.fill",
                "title": "Video added" if is_video else "Photo added",
                "description": filename,
                "timestamp": ts,
                "deepLink": "jenquisthome://service/immich",
                "status": "completed",
            })

    except Exception as e:
        logger.debug(f"Immich fetch failed (expected if offline): {e}")

    _set_cached("immich_recent", items, ttl=120)
    return items


async def fetch_mealie_today() -> list[dict]:
    """Returns structured meal plan data (not feed items)."""
    cached = _get_cached("mealie_today")
    if cached is not None:
        return cached

    meals: list[dict] = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{MEALIE_URL}/api/groups/mealplans/today")
            resp.raise_for_status()
            data = resp.json()

        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            recipe = entry.get("recipe") or {}
            name = recipe.get("name") or entry.get("title") or entry.get("name")
            if name:
                meals.append({
                    "name": name,
                    "recipe_id": recipe.get("id") or entry.get("recipeId"),
                })

    except Exception as e:
        logger.debug(f"Mealie fetch failed (expected if offline): {e}")

    _set_cached("mealie_today", meals, ttl=300)
    return meals
