"""LLM-as-judge client.

Uses the llm-router to score open-ended responses against a rubric.
The judge system prompt is hardcoded — never interpolated from user data —
to prevent prompt injection from eval case content.
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Hardcoded — not configurable from YAML. Rubric content is passed as structured JSON,
# not inline text, which prevents it from being interpreted as instructions.
_JUDGE_SYSTEM_PROMPT = """\
You are an impartial evaluator for AI model outputs.

You will receive a JSON object with three keys:
  - "rubric": a description of what a correct response looks like
  - "question": the original question asked of the model
  - "response": the model's response to evaluate

Score the response from 0.0 to 1.0:
  1.0 = Fully meets the rubric
  0.5 = Partially meets the rubric
  0.0 = Does not meet the rubric

Respond ONLY with valid JSON in this exact format:
{"score": <float 0.0-1.0>, "reasoning": "<one sentence explanation>"}

Do not include any other text outside the JSON object."""


@dataclass
class JudgeResult:
    score: float
    reasoning: str
    raw_response: str


async def judge(
    rubric: str,
    question: str,
    response_text: str,
    judge_model: str,
    router_url: str,
    api_key: str,
) -> JudgeResult:
    """Ask the judge model to score a response against a rubric.

    Retries up to 2 times on transient errors. Returns score=0.0 on
    persistent failure (rather than crashing the eval run).
    """
    payload = json.dumps({
        "rubric": rubric[:500],         # bounded — prevent oversized prompts
        "question": question[:300],      # bounded
        "response": response_text[:2000],  # bounded
    })

    request_body = {
        "model": judge_model,
        "messages": [
            {"role": "user", "content": payload},
        ],
        "temperature": 0.0,
        "max_tokens": 256,
        "response_format": {"type": "json_object"},
    }

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    last_err: Optional[Exception] = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{router_url.rstrip('/')}/v1/chat/completions",
                    json=request_body,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()

            raw = data["choices"][0]["message"]["content"] or ""
            parsed = json.loads(raw)
            score = float(parsed.get("score", 0.0))
            score = max(0.0, min(1.0, score))  # clamp
            reasoning = str(parsed.get("reasoning", ""))
            return JudgeResult(score=score, reasoning=reasoning, raw_response=raw)

        except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError) as e:
            last_err = e
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
            logger.warning(f"Judge attempt {attempt + 1} failed: {e}")

    logger.error(f"Judge failed after 3 attempts: {last_err}")
    return JudgeResult(score=0.0, reasoning=f"Judge error: {last_err}", raw_response="")
