"""
Request complexity classification for smart auto-routing.

Analyzes request content, headers, and caller signals to determine
which tier of model should handle the request. Pure functions, no I/O.
"""
import logging
import re
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional

logger = logging.getLogger(__name__)


class ComplexityTier(IntEnum):
    ROUTINE = 1   # Simple Q&A, short chat, lookups → 3070
    MODERATE = 2  # Coding, multi-turn, tools, analysis → 3090
    COMPLEX = 3   # Heavy reasoning, long context, architecture → 3090 (cloud fallback preferred)


TIER_MODEL_MAP = {
    ComplexityTier.ROUTINE: "qwen2.5-7b-awq",
    ComplexityTier.MODERATE: "qwen2.5-14b-awq",
    ComplexityTier.COMPLEX: "qwen2.5-14b-awq",
}


@dataclass
class ClassificationResult:
    tier: ComplexityTier
    score: float  # 0.0-1.0 heuristic score
    signals: list[str] = field(default_factory=list)
    caller_tier: Optional[ComplexityTier] = None
    heuristic_tier: ComplexityTier = ComplexityTier.ROUTINE


# Keywords that suggest coding/development tasks
_CODING_KEYWORDS = re.compile(
    r'\b(code|coding|programming|developer|engineer|software|implement|debug|refactor)\b',
    re.IGNORECASE,
)

# Keywords that suggest reasoning/analysis tasks
_REASONING_KEYWORDS = re.compile(
    r'\b(reason|think|step.by.step|analyze|explain.why|chain.of.thought|logic)\b',
    re.IGNORECASE,
)

# Keywords in the last user message that suggest complexity
_COMPLEXITY_KEYWORDS = re.compile(
    r'\b(debug|refactor|analyze|implement|architecture|design|optimize|migrate|'
    r'distributed|concurrent|async|threading|security|vulnerability|performance)\b',
    re.IGNORECASE,
)

# Source headers that default to MODERATE (agent-like callers)
_AGENT_SOURCES = {"n8n", "agent", "agent-harness", "ralph"}


def classify_request(request, body: dict, api_key=None) -> ClassificationResult:
    """
    Classify a request's complexity by combining heuristics (Option A)
    and caller-declared signals (Option B).

    final_tier = max(caller_tier, heuristic_tier)
    Heuristics can only escalate, never downgrade.
    """
    score, signals = _score_heuristics(body)
    heuristic_tier = _score_to_tier(score)

    caller_tier = _get_caller_tier(request, body, api_key)

    if caller_tier is not None:
        final_tier = max(caller_tier, heuristic_tier)
    else:
        final_tier = heuristic_tier

    return ClassificationResult(
        tier=final_tier,
        score=score,
        signals=signals,
        caller_tier=caller_tier,
        heuristic_tier=heuristic_tier,
    )


def _score_to_tier(score: float) -> ComplexityTier:
    if score < 0.25:
        return ComplexityTier.ROUTINE
    elif score <= 0.6:
        return ComplexityTier.MODERATE
    else:
        return ComplexityTier.COMPLEX


def _score_heuristics(body: dict) -> tuple[float, list[str]]:
    """Score request complexity from body content. Returns (score, signals)."""
    score = 0.0
    signals: list[str] = []
    messages = body.get("messages", [])

    # --- Tools present: +0.1 per tool, max 0.4 ---
    tools = body.get("tools", [])
    if tools:
        tool_score = min(0.4, len(tools) * 0.1)
        score += tool_score
        signals.append(f"tools={len(tools)}")

    # --- System prompt analysis ---
    system_text = _get_system_text(messages)
    if system_text:
        if _CODING_KEYWORDS.search(system_text):
            score += 0.2
            signals.append("coding_system_prompt")
        if _REASONING_KEYWORDS.search(system_text):
            score += 0.15
            signals.append("reasoning_system_prompt")

    # --- Multi-turn conversation: +0.05 per turn past 3, max 0.2 ---
    user_turns = sum(1 for m in messages if isinstance(m, dict) and m.get("role") == "user")
    if user_turns > 3:
        turn_score = min(0.2, (user_turns - 3) * 0.05)
        score += turn_score
        signals.append(f"multi_turn={user_turns}")

    # --- Token estimate > 2000: scaled 0.0-0.3 ---
    token_estimate = _estimate_tokens(messages)
    if token_estimate > 2000:
        # Scale linearly from 0.0 at 2000 to 0.3 at 8000
        token_score = min(0.3, (token_estimate - 2000) / 20000)
        score += token_score
        signals.append(f"tokens={token_estimate}")

    # --- max_tokens > 1024: scaled 0.0-0.15 ---
    max_tokens = body.get("max_tokens")
    if max_tokens and max_tokens > 1024:
        mt_score = min(0.15, (max_tokens - 1024) / 10000)
        score += mt_score
        signals.append(f"max_tokens={max_tokens}")

    # --- Complexity keywords in last user message: +0.1-0.2 ---
    last_user_msg = _get_last_user_content(messages)
    if last_user_msg:
        keyword_matches = _COMPLEXITY_KEYWORDS.findall(last_user_msg)
        if keyword_matches:
            kw_score = min(0.2, len(keyword_matches) * 0.1)
            score += kw_score
            signals.append(f"complexity_keywords={len(keyword_matches)}")

    # --- Low temperature (<= 0.3): +0.05 ---
    temperature = body.get("temperature")
    if temperature is not None and temperature <= 0.3:
        score += 0.05
        signals.append("low_temperature")

    score = min(1.0, score)
    return score, signals


def _get_caller_tier(request, body: dict, api_key=None) -> Optional[ComplexityTier]:
    """
    Check caller-declared complexity signals (priority order).
    Returns None if no caller signal present.
    """
    headers = getattr(request, "headers", {})

    # 1. X-Complexity header (explicit tier declaration)
    complexity_header = headers.get("x-complexity", "").lower().strip()
    if complexity_header:
        tier_map = {"routine": ComplexityTier.ROUTINE, "moderate": ComplexityTier.MODERATE, "complex": ComplexityTier.COMPLEX}
        if complexity_header in tier_map:
            return tier_map[complexity_header]

    # 2. X-Force-Big: true → COMPLEX (backwards compat)
    if headers.get("x-force-big", "").lower() == "true":
        return ComplexityTier.COMPLEX

    # 3. #force_big tag in message content (backwards compat)
    messages = body.get("messages", [])
    for msg in messages:
        if isinstance(msg, dict):
            content = msg.get("content", "") or ""
            if "#force_big" in content:
                return ComplexityTier.COMPLEX

    # 4. API key metadata.complexity field
    if api_key and getattr(api_key, "metadata", None):
        metadata = api_key.metadata
        if isinstance(metadata, dict) and "complexity" in metadata:
            tier_map = {"routine": ComplexityTier.ROUTINE, "moderate": ComplexityTier.MODERATE, "complex": ComplexityTier.COMPLEX}
            val = str(metadata["complexity"]).lower()
            if val in tier_map:
                return tier_map[val]

    # 5. Source-based defaults: agent-like sources → MODERATE
    source_header = headers.get("x-source", "").lower().strip()
    if source_header in _AGENT_SOURCES:
        return ComplexityTier.MODERATE

    return None


def _estimate_tokens(messages: list) -> int:
    """Rough token estimation (4 chars per token)."""
    total_chars = sum(
        len(m.get("content", "") or "")
        for m in messages
        if isinstance(m, dict)
    )
    return total_chars // 4


def _get_system_text(messages: list) -> str:
    """Extract combined system message text."""
    parts = []
    for m in messages:
        if isinstance(m, dict) and m.get("role") == "system":
            content = m.get("content", "") or ""
            parts.append(content)
    return " ".join(parts)


def _get_last_user_content(messages: list) -> str:
    """Get the content of the last user message."""
    for m in reversed(messages):
        if isinstance(m, dict) and m.get("role") == "user":
            return m.get("content", "") or ""
    return ""
