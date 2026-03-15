"""Core eval execution engine."""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Callable, Optional

import httpx

import db
import judge as judge_module
from loader import resolve_cases
from models import (
    CaseResult,
    EvalCase,
    LlmJudgeScorerConfig,
    ModelResponse,
    RunRequest,
    ScorerResult,
)
from scorers import build_scorer

logger = logging.getLogger(__name__)


async def _call_model(
    messages: list[dict],
    tools: list[dict],
    model: str,
    temperature: float,
    router_url: str,
    api_key: str,
    timeout: int,
) -> tuple[ModelResponse, list[dict]]:
    """Single API call → (ModelResponse, updated_messages)."""
    body: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    t0 = time.monotonic()

    async with httpx.AsyncClient(timeout=timeout + 5) as client:
        resp = await client.post(
            f"{router_url.rstrip('/')}/v1/chat/completions",
            json=body,
            headers=headers,
        )
        resp.raise_for_status()

    latency_ms = (time.monotonic() - t0) * 1000
    data = resp.json()
    choice = data["choices"][0]
    msg = choice.get("message", {})
    usage = data.get("usage", {})

    tool_calls_raw = msg.get("tool_calls") or []
    response = ModelResponse(
        text=msg.get("content"),
        tool_calls=tool_calls_raw,
        finish_reason=choice.get("finish_reason"),
        latency_ms=latency_ms,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
    )

    # Append assistant turn to messages
    assistant_msg: dict = {"role": "assistant"}
    if msg.get("content"):
        assistant_msg["content"] = msg["content"]
    if tool_calls_raw:
        assistant_msg["tool_calls"] = tool_calls_raw
    updated = messages + [assistant_msg]
    return response, updated


async def execute_case(
    case: EvalCase,
    model: str,
    router_url: str,
    api_key: str,
    judge_model: str,
    run_id: str,
    temperature_override: Optional[float] = None,
) -> CaseResult:
    effective_temp = temperature_override if temperature_override is not None else case.temperature
    messages = [m.model_dump() for m in case.messages]
    tools = [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters.model_dump(),
            },
        }
        for t in case.tools
    ]
    # Index simulated tool responses by tool name for multi-turn chains
    sim_responses = {tr.tool_name: tr.simulated_response for tr in case.tool_responses}

    all_tool_calls: list[dict] = []
    final_response: Optional[ModelResponse] = None
    total_latency = 0.0

    try:
        # Drive the conversation — up to 5 turns to handle multi-tool chains
        for _turn in range(5):
            response, messages = await _call_model(
                messages=messages,
                tools=tools,
                model=model,
                temperature=effective_temp,
                router_url=router_url,
                api_key=api_key,
                timeout=case.timeout_seconds,
            )
            total_latency += response.latency_ms
            all_tool_calls.extend(response.tool_calls)
            final_response = response

            if not response.tool_calls:
                break  # Model is done — no more tool calls

            # Inject simulated tool results for each tool call
            for tc in response.tool_calls:
                fn_name = tc.get("function", {}).get("name", "")
                sim_result = sim_responses.get(fn_name, json.dumps({"result": "simulated"}))
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", str(uuid.uuid4())),
                    "content": sim_result,
                })

    except Exception as e:
        logger.error(f"Case {case.id} error: {e}")
        return CaseResult(
            run_id=run_id,
            case_id=case.id,
            category=case.category,
            tags=case.tags,
            model=model,
            temperature=effective_temp,
            status="error",
            scorer_results=[],
            messages=[m.model_dump() for m in case.messages],
            response_text=None,
            latency_ms=None,
            prompt_tokens=None,
            completion_tokens=None,
            error=str(e),
        )

    if final_response is None:
        return CaseResult(
            run_id=run_id,
            case_id=case.id,
            category=case.category,
            tags=case.tags,
            model=model,
            temperature=effective_temp,
            status="error",
            scorer_results=[],
            messages=[m.model_dump() for m in case.messages],
            response_text=None,
            latency_ms=None,
            prompt_tokens=None,
            completion_tokens=None,
            error="No response received",
        )

    # Override latency with total accumulated time across turns
    final_response = final_response.model_copy(update={"latency_ms": total_latency})

    # Run scorers
    scorer_results: list[ScorerResult] = []
    user_message = next(
        (m.content for m in reversed(case.messages) if m.role == "user"), ""
    )

    for scorer_cfg in case.scorers:
        if scorer_cfg.type == "llm_judge":
            judge_result = await judge_module.judge(
                rubric=scorer_cfg.rubric,
                question=user_message,
                response_text=final_response.text or "",
                judge_model=judge_model,
                router_url=router_url,
                api_key=api_key,
            )
            passed = judge_result.score >= scorer_cfg.threshold
            scorer_results.append(ScorerResult(
                scorer_type="llm_judge",
                passed=passed,
                score=judge_result.score,
                detail=judge_result.reasoning,
            ))
        else:
            scorer = build_scorer(scorer_cfg)
            sr = scorer.score(final_response, all_tool_calls=all_tool_calls)
            scorer_results.append(sr)

    # Overall status: pass if ALL scorers pass
    all_passed = all(sr.passed for sr in scorer_results)
    status = "pass" if all_passed else "fail"

    return CaseResult(
        run_id=run_id,
        case_id=case.id,
        category=case.category,
        tags=case.tags,
        model=model,
        temperature=effective_temp,
        status=status,
        scorer_results=scorer_results,
        messages=[m.model_dump() for m in case.messages],
        response_text=final_response.text,
        tool_calls=all_tool_calls,
        latency_ms=total_latency,
        prompt_tokens=final_response.prompt_tokens,
        completion_tokens=final_response.completion_tokens,
        error=None,
    )


async def execute_run(
    request: RunRequest,
    run_id: str,
    db_path: str,
    router_url: str,
    api_key: str,
    judge_model: str,
    progress_callback: Optional[Callable[[CaseResult], None]] = None,
) -> None:
    """Execute a full eval run, persisting results incrementally."""
    try:
        cases = resolve_cases(
            suite=request.suite,
            case_ids=request.case_ids,
            tags=request.tags,
        )
    except ValueError as e:
        await db.finish_run(db_path, run_id, status="failed")
        logger.error(f"Run {run_id} failed to resolve cases: {e}")
        return

    effective_url = request.router_url or router_url
    sem = asyncio.Semaphore(request.concurrency)

    async def run_one(case: EvalCase) -> CaseResult:
        async with sem:
            result = await execute_case(
                case=case,
                model=request.model,
                router_url=effective_url,
                api_key=api_key,
                judge_model=judge_model,
                run_id=run_id,
                temperature_override=request.temperature_override,
            )
            await db.insert_result(db_path, result)
            if progress_callback:
                progress_callback(result)
            return result

    tasks = [run_one(c) for c in cases]
    await asyncio.gather(*tasks, return_exceptions=True)
    await db.finish_run(db_path, run_id)
    logger.info(f"Run {run_id} complete ({len(cases)} cases, model={request.model})")
