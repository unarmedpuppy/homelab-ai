"""Eval Runner — FastAPI application for homelab model evaluation."""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import db
import loader
import runner as eval_runner
from models import RunRequest

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "/app/data/evals.db")
CASES_DIR = os.getenv("CASES_DIR", "/app/cases")
SUITES_DIR = os.getenv("SUITES_DIR", "/app/suites")
ROUTER_URL = os.getenv("ROUTER_URL", "http://llm-router:8000")
ROUTER_API_KEY = os.getenv("ROUTER_API_KEY", os.getenv("LLM_ROUTER_API_KEY", ""))
EVAL_API_KEY = os.getenv("EVAL_API_KEY", "")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "qwen3-32b-awq")

_run_queue: asyncio.Queue = asyncio.Queue()


async def _run_worker() -> None:
    while True:
        run_id, request = await _run_queue.get()
        try:
            await eval_runner.execute_run(
                request=request,
                run_id=run_id,
                db_path=DB_PATH,
                router_url=ROUTER_URL,
                api_key=ROUTER_API_KEY,
                judge_model=JUDGE_MODEL,
            )
        except Exception as e:
            logger.error(f"Run {run_id} worker error: {e}", exc_info=True)
            try:
                await db.finish_run(DB_PATH, run_id, status="failed")
            except Exception:
                pass
        finally:
            _run_queue.task_done()


@asynccontextmanager
async def lifespan(app: FastAPI):
    import pathlib
    pathlib.Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    await db.init_db(DB_PATH)
    loader.load_all_cases(CASES_DIR)
    loader.load_all_suites(SUITES_DIR)
    worker_task = asyncio.create_task(_run_worker())
    yield
    worker_task.cancel()


app = FastAPI(title="Eval Runner", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _check_auth(authorization: Optional[str]) -> None:
    if not EVAL_API_KEY:
        return  # No key configured — open access (dev mode)
    if not authorization or authorization != f"Bearer {EVAL_API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    cases = loader.get_cases()
    suites = loader.get_suites()
    return {
        "status": "healthy",
        "cases_loaded": len(cases),
        "suites_loaded": len(suites),
        "router_url": ROUTER_URL,
        "judge_model": JUDGE_MODEL,
        "queue_depth": _run_queue.qsize(),
    }


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------

@app.get("/cases")
async def list_cases(
    category: Optional[str] = Query(None),
    tag: Optional[list[str]] = Query(None),
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    cases = list(loader.get_cases().values())
    if category:
        cases = [c for c in cases if c.category == category]
    if tag:
        cases = [c for c in cases if any(t in c.tags for t in tag)]
    return {
        "cases": [
            {"id": c.id, "category": c.category, "description": c.description, "tags": c.tags}
            for c in cases
        ],
        "total": len(cases),
    }


@app.get("/cases/{case_id}")
async def get_case(case_id: str, authorization: Optional[str] = Header(None)):
    _check_auth(authorization)
    case = loader.get_cases().get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id!r} not found")
    return case.model_dump()


# ---------------------------------------------------------------------------
# Suites
# ---------------------------------------------------------------------------

@app.get("/suites")
async def list_suites(authorization: Optional[str] = Header(None)):
    _check_auth(authorization)
    suites = loader.get_suites()
    result = []
    for name, s in suites.items():
        tags = s.get("tags", [])
        cases = loader.resolve_cases(suite=name) if name else []
        result.append({
            "name": name,
            "description": s.get("description", ""),
            "case_count": len(cases),
            "tags": tags,
            "pass_threshold": s.get("pass_threshold"),
        })
    return {"suites": result}


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------

@app.post("/runs", status_code=202)
async def create_run(request: RunRequest, authorization: Optional[str] = Header(None)):
    _check_auth(authorization)

    # Validate cases exist before queuing
    try:
        cases = loader.resolve_cases(
            suite=request.suite,
            case_ids=request.case_ids,
            tags=request.tags,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not cases:
        raise HTTPException(status_code=400, detail="No matching cases found")

    run_id = str(uuid.uuid4())
    router_url = request.router_url or ROUTER_URL

    await db.create_run(
        db_path=DB_PATH,
        run_id=run_id,
        suite_name=request.suite,
        model=request.model,
        router_url=router_url,
        total_cases=len(cases),
    )

    await _run_queue.put((run_id, request))
    logger.info(f"Queued run {run_id}: model={request.model} cases={len(cases)}")

    return {"run_id": run_id, "status": "running", "total_cases": len(cases)}


@app.get("/runs")
async def list_runs(
    model: Optional[str] = Query(None),
    suite: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    runs = await db.list_runs(
        DB_PATH, model=model, suite=suite, status=status, limit=limit, offset=offset
    )
    return {"runs": runs, "total": len(runs)}


@app.get("/runs/compare")
async def compare_runs(
    a: str = Query(...),
    b: str = Query(...),
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    run_a = await db.get_run(DB_PATH, a)
    run_b = await db.get_run(DB_PATH, b)
    if not run_a:
        raise HTTPException(status_code=404, detail=f"Run {a!r} not found")
    if not run_b:
        raise HTTPException(status_code=404, detail=f"Run {b!r} not found")

    results_a = await db.query_results(DB_PATH, a, limit=1000)
    results_b = await db.query_results(DB_PATH, b, limit=1000)

    # Build per-category breakdown
    cats_a: dict[str, list] = {}
    cats_b: dict[str, list] = {}
    for r in results_a:
        cats_a.setdefault(r["category"], []).append(r)
    for r in results_b:
        cats_b.setdefault(r["category"], []).append(r)

    all_cats = sorted(set(list(cats_a.keys()) + list(cats_b.keys())))
    breakdown = []
    for cat in all_cats:
        ra = cats_a.get(cat, [])
        rb = cats_b.get(cat, [])
        a_rate = sum(1 for r in ra if r["status"] == "pass") / len(ra) if ra else 0
        b_rate = sum(1 for r in rb if r["status"] == "pass") / len(rb) if rb else 0
        delta = b_rate - a_rate
        winner = "b" if delta > 0.01 else "a" if delta < -0.01 else "tie"
        breakdown.append({
            "category": cat,
            "a_total": len(ra), "a_passed": sum(1 for r in ra if r["status"] == "pass"), "a_pass_rate": round(a_rate, 4),
            "b_total": len(rb), "b_passed": sum(1 for r in rb if r["status"] == "pass"), "b_pass_rate": round(b_rate, 4),
            "delta": round(delta, 4),
            "winner": winner,
        })

    # Cases where one wins but the other fails
    ids_a = {r["case_id"]: r["status"] for r in results_a}
    ids_b = {r["case_id"]: r["status"] for r in results_b}
    a_wins = [cid for cid in ids_a if ids_a[cid] == "pass" and ids_b.get(cid) != "pass"]
    b_wins = [cid for cid in ids_b if ids_b[cid] == "pass" and ids_a.get(cid) != "pass"]

    lat_a = run_a.get("p50_latency_ms")
    lat_b = run_b.get("p50_latency_ms")
    lat_delta = round(lat_b - lat_a, 1) if lat_a is not None and lat_b is not None else None

    return {
        "run_a": run_a,
        "run_b": run_b,
        "by_category": breakdown,
        "cases_a_wins": a_wins,
        "cases_b_wins": b_wins,
        "latency_delta_p50_ms": lat_delta,
    }


@app.get("/runs/{run_id}")
async def get_run(run_id: str, authorization: Optional[str] = Header(None)):
    _check_auth(authorization)
    run = await db.get_run(DB_PATH, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id!r} not found")
    return run


@app.delete("/runs/{run_id}")
async def delete_run(run_id: str, authorization: Optional[str] = Header(None)):
    _check_auth(authorization)
    run = await db.get_run(DB_PATH, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Not found")
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db_conn:
        await db_conn.execute("DELETE FROM eval_results WHERE run_id = ?", (run_id,))
        await db_conn.execute("DELETE FROM eval_runs WHERE run_id = ?", (run_id,))
        await db_conn.commit()
    return {"deleted": True}


@app.get("/runs/{run_id}/results")
async def get_run_results(
    run_id: str,
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    run = await db.get_run(DB_PATH, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    results = await db.query_results(
        DB_PATH, run_id, status=status, category=category, limit=limit, offset=offset
    )
    return {"results": results, "total": len(results)}


@app.get("/runs/{run_id}/results/{result_id}")
async def get_result(run_id: str, result_id: str, authorization: Optional[str] = Header(None)):
    _check_auth(authorization)
    result = await db.get_result(DB_PATH, result_id)
    if not result or result["run_id"] != run_id:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


# ---------------------------------------------------------------------------
# Stats + Models
# ---------------------------------------------------------------------------

@app.get("/stats")
async def get_stats(authorization: Optional[str] = Header(None)):
    _check_auth(authorization)
    return await db.get_stats(DB_PATH)


@app.get("/models")
async def list_models(authorization: Optional[str] = Header(None)):
    _check_auth(authorization)
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{ROUTER_URL}/v1/models",
                headers={"Authorization": f"Bearer {ROUTER_API_KEY}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return {"models": [m["id"] for m in data.get("data", [])]}
    except Exception as e:
        return {"models": [], "error": str(e)}


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@app.post("/admin/reload")
async def reload_cases(authorization: Optional[str] = Header(None)):
    _check_auth(authorization)
    loader.load_all_cases(CASES_DIR)
    loader.load_all_suites(SUITES_DIR)
    return {"cases": len(loader.get_cases()), "suites": len(loader.get_suites())}


@app.get("/")
async def root():
    return {
        "service": "Eval Runner",
        "version": "0.1.0",
        "cases": len(loader.get_cases()),
        "suites": len(loader.get_suites()),
        "docs": "/docs",
    }
