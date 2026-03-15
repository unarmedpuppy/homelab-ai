"""YAML eval case and suite loader."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import yaml

from models import (
    EvalCase,
    JsonSchemaScorerConfig,
    LlmJudgeScorerConfig,
    ContainsScorerConfig,
    ExactScorerConfig,
    RegexScorerConfig,
    WordCountScorerConfig,
    ToolCallScorerConfig,
    NoToolCallScorerConfig,
    ToolCallSequenceScorerConfig,
    NoThinkTagsScorerConfig,
    LatencyScorerConfig,
    Message,
    Tool,
    ToolResponse,
    ToolSchema,
)

logger = logging.getLogger(__name__)

# In-memory case and suite stores
_cases: dict[str, EvalCase] = {}
_suites: dict[str, dict] = {}


def _parse_scorer(raw: dict) -> Any:
    t = raw.get("type")
    if t == "contains":
        return ContainsScorerConfig(**raw)
    if t == "exact":
        return ExactScorerConfig(**raw)
    if t == "regex":
        return RegexScorerConfig(**raw)
    if t == "word_count":
        return WordCountScorerConfig(**raw)
    if t == "json_schema":
        # YAML key is "schema", but Pydantic alias is schema_
        return JsonSchemaScorerConfig.model_validate(raw)
    if t == "tool_call":
        return ToolCallScorerConfig(**raw)
    if t == "no_tool_call":
        return NoToolCallScorerConfig(**raw)
    if t == "tool_call_sequence":
        return ToolCallSequenceScorerConfig(**raw)
    if t == "no_think_tags":
        return NoThinkTagsScorerConfig(**raw)
    if t == "llm_judge":
        return LlmJudgeScorerConfig(**raw)
    if t == "latency":
        return LatencyScorerConfig(**raw)
    raise ValueError(f"Unknown scorer type: {t!r}")


def _parse_case(raw: dict, source_file: str) -> EvalCase:
    case_id = raw.get("id", "")
    try:
        messages = [Message(**m) for m in raw.get("messages", [])]
        tools = []
        for t in raw.get("tools", []):
            params = t.get("parameters", {})
            tools.append(Tool(
                name=t["name"],
                description=t["description"],
                parameters=ToolSchema(**params),
            ))
        tool_responses = [ToolResponse(**tr) for tr in raw.get("tool_responses", [])]
        scorers = [_parse_scorer(s) for s in raw.get("scorers", [])]

        return EvalCase(
            id=case_id,
            description=raw.get("description", ""),
            category=raw.get("category", "uncategorized"),
            tags=raw.get("tags", []),
            messages=messages,
            tools=tools,
            tool_responses=tool_responses,
            scorers=scorers,
            timeout_seconds=raw.get("timeout_seconds", 30),
            temperature=raw.get("temperature", 0.0),
        )
    except Exception as e:
        raise ValueError(f"Error parsing case {case_id!r} in {source_file}: {e}") from e


def load_all_cases(cases_dir: str) -> dict[str, EvalCase]:
    global _cases
    _cases = {}
    path = Path(cases_dir)
    if not path.exists():
        logger.warning(f"Cases directory not found: {cases_dir}")
        return _cases

    for yaml_file in sorted(path.rglob("*.yaml")):
        try:
            with open(yaml_file) as f:
                raw_list = yaml.safe_load(f)
            if not isinstance(raw_list, list):
                logger.warning(f"Skipping {yaml_file}: expected a YAML list")
                continue
            for raw in raw_list:
                case = _parse_case(raw, str(yaml_file))
                if case.id in _cases:
                    logger.warning(f"Duplicate case ID {case.id!r} in {yaml_file}")
                _cases[case.id] = case
        except Exception as e:
            logger.error(f"Failed to load {yaml_file}: {e}")

    logger.info(f"Loaded {len(_cases)} eval cases from {cases_dir}")
    return _cases


def load_all_suites(suites_dir: str) -> dict[str, dict]:
    global _suites
    _suites = {}
    path = Path(suites_dir)
    if not path.exists():
        logger.warning(f"Suites directory not found: {suites_dir}")
        return _suites

    for yaml_file in sorted(path.glob("*.yaml")):
        try:
            with open(yaml_file) as f:
                suite = yaml.safe_load(f)
            name = suite.get("name", yaml_file.stem)
            _suites[name] = suite
        except Exception as e:
            logger.error(f"Failed to load suite {yaml_file}: {e}")

    logger.info(f"Loaded {len(_suites)} suites from {suites_dir}")
    return _suites


def get_cases() -> dict[str, EvalCase]:
    return _cases


def get_suites() -> dict[str, dict]:
    return _suites


def resolve_cases(
    suite: Optional[str] = None,
    case_ids: Optional[list[str]] = None,
    tags: Optional[list[str]] = None,
) -> list[EvalCase]:
    """Resolve a run request to a list of EvalCase objects."""
    if suite:
        suite_def = _suites.get(suite)
        if not suite_def:
            raise ValueError(f"Suite {suite!r} not found. Available: {list(_suites)}")
        filter_tags = suite_def.get("tags", [])
        exclude_tags = suite_def.get("exclude_tags", [])
        candidates = list(_cases.values())
        if filter_tags:
            candidates = [c for c in candidates if any(t in c.tags for t in filter_tags)]
        if exclude_tags:
            candidates = [c for c in candidates if not any(t in c.tags for t in exclude_tags)]
        return candidates

    if case_ids:
        missing = [cid for cid in case_ids if cid not in _cases]
        if missing:
            raise ValueError(f"Unknown case IDs: {missing}")
        return [_cases[cid] for cid in case_ids]

    if tags:
        return [c for c in _cases.values() if any(t in c.tags for t in tags)]

    # No filter: run everything
    return list(_cases.values())
