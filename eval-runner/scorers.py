"""Scorer implementations for eval-runner."""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

from models import (
    ContainsScorerConfig,
    ExactScorerConfig,
    JsonSchemaScorerConfig,
    LatencyScorerConfig,
    LlmJudgeScorerConfig,
    ModelResponse,
    NoThinkTagsScorerConfig,
    NoToolCallScorerConfig,
    RegexScorerConfig,
    ScorerResult,
    ToolCallScorerConfig,
    ToolCallSequenceScorerConfig,
    WordCountScorerConfig,
)

# Pattern that matches thinking tokens — the router should strip these,
# but we verify it actually does.
_THINK_PATTERN = re.compile(r"</?think>", re.IGNORECASE)


class BaseScorer(ABC):
    @abstractmethod
    def score(self, response: ModelResponse, all_tool_calls: list[dict] | None = None) -> ScorerResult:
        ...


class ContainsScorer(BaseScorer):
    def __init__(self, cfg: ContainsScorerConfig):
        self.text = cfg.text
        self.case_sensitive = cfg.case_sensitive

    def score(self, response: ModelResponse, **_) -> ScorerResult:
        text = response.text or ""
        hay = text if self.case_sensitive else text.lower()
        needle = self.text if self.case_sensitive else self.text.lower()
        passed = needle in hay
        return ScorerResult(
            scorer_type="contains",
            passed=passed,
            score=1.0 if passed else 0.0,
            detail=f"{'Found' if passed else 'Missing'}: {self.text!r}",
        )


class ExactScorer(BaseScorer):
    def __init__(self, cfg: ExactScorerConfig):
        self.expected = cfg.expected
        self.strip = cfg.strip_whitespace
        self.case_sensitive = cfg.case_sensitive

    def score(self, response: ModelResponse, **_) -> ScorerResult:
        text = response.text or ""
        a = (text.strip() if self.strip else text)
        b = self.expected.strip() if self.strip else self.expected
        if not self.case_sensitive:
            a, b = a.lower(), b.lower()
        passed = a == b
        return ScorerResult(
            scorer_type="exact",
            passed=passed,
            score=1.0 if passed else 0.0,
            detail=f"Expected {self.expected!r}, got {(response.text or '')[:80]!r}",
        )


class RegexScorer(BaseScorer):
    def __init__(self, cfg: RegexScorerConfig):
        self.pattern = re.compile(cfg.pattern)
        self.negate = cfg.negate

    def score(self, response: ModelResponse, **_) -> ScorerResult:
        text = response.text or ""
        match = bool(self.pattern.search(text))
        passed = (not match) if self.negate else match
        return ScorerResult(
            scorer_type="regex",
            passed=passed,
            score=1.0 if passed else 0.0,
            detail=(
                f"Pattern {self.pattern.pattern!r}: {'matched (negated=fail)' if match and self.negate else 'matched' if match else 'no match'}"
            ),
        )


class WordCountScorer(BaseScorer):
    def __init__(self, cfg: WordCountScorerConfig):
        self.min_words = cfg.min_words
        self.max_words = cfg.max_words

    def score(self, response: ModelResponse, **_) -> ScorerResult:
        text = response.text or ""
        count = len(text.split())
        ok_min = (count >= self.min_words) if self.min_words else True
        ok_max = (count <= self.max_words) if self.max_words else True
        passed = ok_min and ok_max
        parts = []
        if self.min_words:
            parts.append(f"min={self.min_words}")
        if self.max_words:
            parts.append(f"max={self.max_words}")
        return ScorerResult(
            scorer_type="word_count",
            passed=passed,
            score=1.0 if passed else 0.0,
            detail=f"{count} words ({', '.join(parts)})",
        )


class JsonSchemaScorer(BaseScorer):
    def __init__(self, cfg: JsonSchemaScorerConfig):
        self.schema = cfg.schema_

    def score(self, response: ModelResponse, **_) -> ScorerResult:
        text = response.text or ""
        # Strip markdown fences
        stripped = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("```").strip()
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError as e:
            return ScorerResult(
                scorer_type="json_schema",
                passed=False,
                score=0.0,
                detail=f"JSON parse error: {e}",
            )
        try:
            import jsonschema
            jsonschema.validate(parsed, self.schema)
            return ScorerResult(
                scorer_type="json_schema",
                passed=True,
                score=1.0,
                detail="Valid JSON matching schema",
            )
        except Exception as e:
            return ScorerResult(
                scorer_type="json_schema",
                passed=False,
                score=0.0,
                detail=f"Schema validation failed: {e}",
            )


class ToolCallScorer(BaseScorer):
    def __init__(self, cfg: ToolCallScorerConfig):
        self.tool_name = cfg.tool_name
        self.required_args = cfg.required_args

    def score(self, response: ModelResponse, **_) -> ScorerResult:
        matching = [tc for tc in response.tool_calls if tc.get("function", {}).get("name") == self.tool_name]
        if not matching:
            return ScorerResult(
                scorer_type="tool_call",
                passed=False,
                score=0.0,
                detail=f"Tool {self.tool_name!r} not called. Got: {[tc.get('function',{}).get('name') for tc in response.tool_calls]}",
            )
        # Check required args on the first matching call
        call = matching[0]
        try:
            args = json.loads(call.get("function", {}).get("arguments", "{}"))
        except json.JSONDecodeError:
            args = {}

        failures = []
        for key, expected_substr in self.required_args.items():
            actual = str(args.get(key, ""))
            if expected_substr.lower() not in actual.lower():
                failures.append(f"{key}={actual!r} (wanted {expected_substr!r})")

        if failures:
            return ScorerResult(
                scorer_type="tool_call",
                passed=False,
                score=0.5,
                detail=f"Tool called but arg mismatch: {', '.join(failures)}",
            )
        return ScorerResult(
            scorer_type="tool_call",
            passed=True,
            score=1.0,
            detail=f"{self.tool_name!r} called with correct args",
        )


class NoToolCallScorer(BaseScorer):
    def score(self, response: ModelResponse, **_) -> ScorerResult:
        if response.tool_calls:
            names = [tc.get("function", {}).get("name") for tc in response.tool_calls]
            return ScorerResult(
                scorer_type="no_tool_call",
                passed=False,
                score=0.0,
                detail=f"Unexpected tool calls: {names}",
            )
        return ScorerResult(
            scorer_type="no_tool_call",
            passed=True,
            score=1.0,
            detail="No tool calls (correct)",
        )


class ToolCallSequenceScorer(BaseScorer):
    def __init__(self, cfg: ToolCallSequenceScorerConfig):
        self.expected = cfg.expected_sequence

    def score(self, response: ModelResponse, all_tool_calls: list[dict] | None = None, **_) -> ScorerResult:
        calls = all_tool_calls or response.tool_calls
        names = [tc.get("function", {}).get("name") for tc in calls]
        passed = names == self.expected
        return ScorerResult(
            scorer_type="tool_call_sequence",
            passed=passed,
            score=1.0 if passed else 0.0,
            detail=f"Expected {self.expected}, got {names}",
        )


class NoThinkTagsScorer(BaseScorer):
    def score(self, response: ModelResponse, **_) -> ScorerResult:
        text = response.text or ""
        match = _THINK_PATTERN.search(text)
        if match:
            return ScorerResult(
                scorer_type="no_think_tags",
                passed=False,
                score=0.0,
                detail=f"Found thinking tag at position {match.start()}: {text[max(0,match.start()-20):match.end()+20]!r}",
            )
        return ScorerResult(
            scorer_type="no_think_tags",
            passed=True,
            score=1.0,
            detail="No thinking tags in response",
        )


class LlmJudgeScorer(BaseScorer):
    """Scoring deferred to judge.py — this is a placeholder that gets replaced at runtime."""

    def __init__(self, cfg: LlmJudgeScorerConfig):
        self.rubric = cfg.rubric
        self.threshold = cfg.threshold

    def score(self, response: ModelResponse, **_) -> ScorerResult:
        # Actual scoring happens in runner.py via judge.py (async)
        raise NotImplementedError("LlmJudgeScorer must be called via runner.py")


class LatencyScorer(BaseScorer):
    def __init__(self, cfg: LatencyScorerConfig):
        self.max_ms = cfg.max_ms

    def score(self, response: ModelResponse, **_) -> ScorerResult:
        ms = response.latency_ms
        passed = ms <= self.max_ms
        return ScorerResult(
            scorer_type="latency",
            passed=passed,
            score=1.0 if passed else 0.0,
            detail=f"{ms:.0f}ms (max {self.max_ms}ms)",
        )


# ---------------------------------------------------------------------------
# Registry + factory
# ---------------------------------------------------------------------------

def build_scorer(cfg: Any) -> BaseScorer:
    t = cfg.type
    return {
        "contains": lambda: ContainsScorer(cfg),
        "exact": lambda: ExactScorer(cfg),
        "regex": lambda: RegexScorer(cfg),
        "word_count": lambda: WordCountScorer(cfg),
        "json_schema": lambda: JsonSchemaScorer(cfg),
        "tool_call": lambda: ToolCallScorer(cfg),
        "no_tool_call": lambda: NoToolCallScorer(cfg),
        "tool_call_sequence": lambda: ToolCallSequenceScorer(cfg),
        "no_think_tags": lambda: NoThinkTagsScorer(cfg),
        "llm_judge": lambda: LlmJudgeScorer(cfg),
        "latency": lambda: LatencyScorer(cfg),
    }[t]()
