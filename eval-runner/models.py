"""Pydantic schemas for eval-runner."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Eval case definitions (loaded from YAML)
# ---------------------------------------------------------------------------

class ToolParameter(BaseModel):
    type: str
    description: Optional[str] = None
    enum: Optional[list[str]] = None
    default: Optional[Any] = None


class ToolSchema(BaseModel):
    type: str = "object"
    properties: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)


class Tool(BaseModel):
    name: str
    description: str
    parameters: ToolSchema


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class ToolResponse(BaseModel):
    """Simulated tool response for multi-turn chains."""
    tool_name: str
    simulated_response: str


# Scorer configs — one per scorer type

class ContainsScorerConfig(BaseModel):
    type: Literal["contains"]
    text: str
    case_sensitive: bool = False


class ExactScorerConfig(BaseModel):
    type: Literal["exact"]
    expected: str
    strip_whitespace: bool = True
    case_sensitive: bool = False


class RegexScorerConfig(BaseModel):
    type: Literal["regex"]
    pattern: str
    negate: bool = False


class WordCountScorerConfig(BaseModel):
    type: Literal["word_count"]
    min_words: Optional[int] = None
    max_words: Optional[int] = None


class JsonSchemaScorerConfig(BaseModel):
    type: Literal["json_schema"]
    schema_: dict = Field(alias="schema")

    model_config = {"populate_by_name": True}


class ToolCallScorerConfig(BaseModel):
    type: Literal["tool_call"]
    tool_name: str
    required_args: dict[str, str] = Field(default_factory=dict)  # arg → substring


class NoToolCallScorerConfig(BaseModel):
    type: Literal["no_tool_call"]


class ToolCallSequenceScorerConfig(BaseModel):
    type: Literal["tool_call_sequence"]
    expected_sequence: list[str]


class NoThinkTagsScorerConfig(BaseModel):
    type: Literal["no_think_tags"]


class LlmJudgeScorerConfig(BaseModel):
    type: Literal["llm_judge"]
    rubric: str
    threshold: float = 0.6


class LatencyScorerConfig(BaseModel):
    type: Literal["latency"]
    max_ms: int


ScorerConfig = (
    ContainsScorerConfig
    | ExactScorerConfig
    | RegexScorerConfig
    | WordCountScorerConfig
    | JsonSchemaScorerConfig
    | ToolCallScorerConfig
    | NoToolCallScorerConfig
    | ToolCallSequenceScorerConfig
    | NoThinkTagsScorerConfig
    | LlmJudgeScorerConfig
    | LatencyScorerConfig
)


class EvalCase(BaseModel):
    id: str
    description: str
    category: str
    tags: list[str] = Field(default_factory=list)
    messages: list[Message]
    tools: list[Tool] = Field(default_factory=list)
    tool_responses: list[ToolResponse] = Field(default_factory=list)
    scorers: list[Any]  # parsed ScorerConfigs
    timeout_seconds: int = 30
    temperature: float = 0.0  # determinism by default

    @model_validator(mode="after")
    def must_have_scorers(self) -> "EvalCase":
        if not self.scorers:
            raise ValueError(f"Case {self.id!r} must have at least one scorer")
        return self


# ---------------------------------------------------------------------------
# Run request / result schemas
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    model: str
    suite: Optional[str] = None
    case_ids: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    router_url: Optional[str] = None
    concurrency: int = Field(default=1, ge=1, le=10)
    timeout_seconds: int = Field(default=30, ge=5, le=300)

    @model_validator(mode="after")
    def must_specify_cases(self) -> "RunRequest":
        if not any([self.suite, self.case_ids, self.tags]):
            raise ValueError("Specify suite, case_ids, or tags")
        return self


class ScorerResult(BaseModel):
    scorer_type: str
    passed: bool
    score: float
    detail: str


class ModelResponse(BaseModel):
    """Parsed response from the LLM."""
    text: Optional[str]
    tool_calls: list[dict] = Field(default_factory=list)
    finish_reason: Optional[str]
    latency_ms: float
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]


class CaseResult(BaseModel):
    result_id: str = Field(default_factory=_uid)
    run_id: str
    case_id: str
    category: str
    tags: list[str]
    model: str
    status: Literal["pass", "fail", "error"]
    scorer_results: list[ScorerResult]
    messages: list[dict]
    response_text: Optional[str]
    tool_calls: list[dict] = Field(default_factory=list)
    latency_ms: Optional[float]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    error: Optional[str]
    created_at: str = Field(default_factory=_now)


class RunSummary(BaseModel):
    run_id: str
    suite_name: Optional[str]
    model: str
    router_url: str
    started_at: str
    finished_at: Optional[str] = None
    status: Literal["running", "done", "failed"]
    total_cases: int = 0
    passed: int = 0
    failed: int = 0
    errored: int = 0
    pass_rate: Optional[float] = None
    p50_latency_ms: Optional[float] = None
    p95_latency_ms: Optional[float] = None


class CategoryBreakdown(BaseModel):
    category: str
    a_total: int
    a_passed: int
    a_pass_rate: float
    b_total: int
    b_passed: int
    b_pass_rate: float
    delta: float
    winner: Literal["a", "b", "tie"]


class ComparisonReport(BaseModel):
    run_a: RunSummary
    run_b: RunSummary
    by_category: list[CategoryBreakdown]
    cases_a_wins: list[str]  # a passes, b fails
    cases_b_wins: list[str]  # b passes, a fails
    latency_delta_p50_ms: Optional[float]
