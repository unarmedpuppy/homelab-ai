"""Unit tests for complexity classification module."""
import pytest
from dataclasses import dataclass
from typing import Optional

from complexity import (
    classify_request,
    ComplexityTier,
    TIER_MODEL_MAP,
    _score_heuristics,
    _get_caller_tier,
    _score_to_tier,
)


class FakeRequest:
    def __init__(self, headers=None):
        self.headers = headers or {}


@dataclass
class FakeApiKey:
    metadata: Optional[dict] = None


# ============================================================================
# Tier-to-model mapping
# ============================================================================

def test_tier_model_map():
    assert TIER_MODEL_MAP[ComplexityTier.ROUTINE] == "qwen2.5-7b-awq"
    assert TIER_MODEL_MAP[ComplexityTier.MODERATE] == "qwen2.5-14b-awq"
    assert TIER_MODEL_MAP[ComplexityTier.COMPLEX] == "qwen2.5-14b-awq"


# ============================================================================
# Score-to-tier mapping
# ============================================================================

def test_score_to_tier_routine():
    assert _score_to_tier(0.0) == ComplexityTier.ROUTINE
    assert _score_to_tier(0.24) == ComplexityTier.ROUTINE


def test_score_to_tier_moderate():
    assert _score_to_tier(0.25) == ComplexityTier.MODERATE
    assert _score_to_tier(0.6) == ComplexityTier.MODERATE


def test_score_to_tier_complex():
    assert _score_to_tier(0.61) == ComplexityTier.COMPLEX
    assert _score_to_tier(1.0) == ComplexityTier.COMPLEX


# ============================================================================
# Simple messages → ROUTINE
# ============================================================================

def test_simple_message_routes_routine():
    body = {"messages": [{"role": "user", "content": "What is 2+2?"}]}
    result = classify_request(FakeRequest(), body)
    assert result.tier == ComplexityTier.ROUTINE
    assert result.score < 0.25


def test_empty_messages_routes_routine():
    body = {"messages": []}
    result = classify_request(FakeRequest(), body)
    assert result.tier == ComplexityTier.ROUTINE
    assert result.score == 0.0


def test_short_chat_routes_routine():
    body = {"messages": [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
    ]}
    result = classify_request(FakeRequest(), body)
    assert result.tier == ComplexityTier.ROUTINE


# ============================================================================
# Tools present → MODERATE+
# ============================================================================

def test_single_tool_adds_score():
    body = {
        "messages": [{"role": "user", "content": "Run the function"}],
        "tools": [{"type": "function", "function": {"name": "get_weather"}}],
    }
    score, signals = _score_heuristics(body)
    assert score >= 0.1
    assert "tools=1" in signals


def test_multiple_tools_escalate_to_moderate():
    body = {
        "messages": [{"role": "user", "content": "Help me"}],
        "tools": [{"type": "function"} for _ in range(4)],
    }
    result = classify_request(FakeRequest(), body)
    assert result.tier >= ComplexityTier.MODERATE
    assert result.score >= 0.25


def test_tools_score_caps_at_04():
    body = {
        "messages": [{"role": "user", "content": "Help"}],
        "tools": [{"type": "function"} for _ in range(10)],
    }
    score, signals = _score_heuristics(body)
    # Tools contribution capped at 0.4, total should not blow up
    assert score <= 1.0
    assert "tools=10" in signals


# ============================================================================
# Coding system prompt → MODERATE+
# ============================================================================

def test_coding_system_prompt():
    body = {"messages": [
        {"role": "system", "content": "You are a software developer who writes code."},
        {"role": "user", "content": "Hello"},
    ]}
    score, signals = _score_heuristics(body)
    assert "coding_system_prompt" in signals
    assert score >= 0.2


def test_reasoning_system_prompt():
    body = {"messages": [
        {"role": "system", "content": "Think step by step and analyze carefully."},
        {"role": "user", "content": "Solve this"},
    ]}
    score, signals = _score_heuristics(body)
    assert "reasoning_system_prompt" in signals
    assert score >= 0.15


def test_coding_and_reasoning_system_prompt_stack():
    body = {"messages": [
        {"role": "system", "content": "You are a developer. Think step by step."},
        {"role": "user", "content": "Hello"},
    ]}
    score, signals = _score_heuristics(body)
    assert "coding_system_prompt" in signals
    assert "reasoning_system_prompt" in signals
    assert score >= 0.35


# ============================================================================
# Multi-turn conversations
# ============================================================================

def test_multi_turn_past_3_adds_score():
    messages = []
    for i in range(6):
        messages.append({"role": "user", "content": f"Message {i}"})
        messages.append({"role": "assistant", "content": f"Reply {i}"})
    body = {"messages": messages}
    score, signals = _score_heuristics(body)
    assert any("multi_turn" in s for s in signals)


def test_3_turns_or_less_no_multi_turn_signal():
    messages = [
        {"role": "user", "content": "Q1"},
        {"role": "assistant", "content": "A1"},
        {"role": "user", "content": "Q2"},
        {"role": "assistant", "content": "A2"},
        {"role": "user", "content": "Q3"},
    ]
    body = {"messages": messages}
    score, signals = _score_heuristics(body)
    assert not any("multi_turn" in s for s in signals)


# ============================================================================
# Token estimate
# ============================================================================

def test_long_context_adds_token_signal():
    long_content = "x" * 12000  # ~3000 tokens
    body = {"messages": [{"role": "user", "content": long_content}]}
    score, signals = _score_heuristics(body)
    assert any("tokens=" in s for s in signals)
    assert score > 0


def test_short_content_no_token_signal():
    body = {"messages": [{"role": "user", "content": "Short question"}]}
    score, signals = _score_heuristics(body)
    assert not any("tokens=" in s for s in signals)


# ============================================================================
# max_tokens parameter
# ============================================================================

def test_high_max_tokens_adds_signal():
    body = {
        "messages": [{"role": "user", "content": "Generate"}],
        "max_tokens": 4096,
    }
    score, signals = _score_heuristics(body)
    assert any("max_tokens=" in s for s in signals)


def test_low_max_tokens_no_signal():
    body = {
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 512,
    }
    score, signals = _score_heuristics(body)
    assert not any("max_tokens=" in s for s in signals)


# ============================================================================
# Complexity keywords in last user message
# ============================================================================

def test_complexity_keywords_in_message():
    body = {"messages": [{"role": "user", "content": "Debug this distributed systems race condition"}]}
    score, signals = _score_heuristics(body)
    assert any("complexity_keywords" in s for s in signals)
    assert score >= 0.1


def test_no_complexity_keywords():
    body = {"messages": [{"role": "user", "content": "What time is it?"}]}
    score, signals = _score_heuristics(body)
    assert not any("complexity_keywords" in s for s in signals)


# ============================================================================
# Low temperature
# ============================================================================

def test_low_temperature_adds_signal():
    body = {
        "messages": [{"role": "user", "content": "Generate precisely"}],
        "temperature": 0.1,
    }
    score, signals = _score_heuristics(body)
    assert "low_temperature" in signals
    assert score >= 0.05


def test_normal_temperature_no_signal():
    body = {
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.7,
    }
    score, signals = _score_heuristics(body)
    assert "low_temperature" not in signals


# ============================================================================
# Score bounded 0-1
# ============================================================================

def test_score_capped_at_1():
    """Stack all signals to verify score never exceeds 1.0."""
    body = {
        "messages": [
            {"role": "system", "content": "You are a developer who thinks step by step."},
        ] + [
            {"role": "user" if i % 2 == 0 else "assistant", "content": "x" * 2000}
            for i in range(10)
        ],
        "tools": [{"type": "function"} for _ in range(10)],
        "max_tokens": 8192,
        "temperature": 0.1,
    }
    # Make last message have complexity keywords
    body["messages"].append({"role": "user", "content": "Debug and refactor this architecture"})
    score, _ = _score_heuristics(body)
    assert score <= 1.0


# ============================================================================
# Caller tier: X-Complexity header
# ============================================================================

def test_x_complexity_routine():
    req = FakeRequest({"x-complexity": "routine"})
    assert _get_caller_tier(req, {}) == ComplexityTier.ROUTINE


def test_x_complexity_moderate():
    req = FakeRequest({"x-complexity": "moderate"})
    assert _get_caller_tier(req, {}) == ComplexityTier.MODERATE


def test_x_complexity_complex():
    req = FakeRequest({"x-complexity": "complex"})
    assert _get_caller_tier(req, {}) == ComplexityTier.COMPLEX


def test_x_complexity_case_insensitive():
    req = FakeRequest({"x-complexity": "COMPLEX"})
    assert _get_caller_tier(req, {}) == ComplexityTier.COMPLEX


def test_x_complexity_invalid_ignored():
    req = FakeRequest({"x-complexity": "mega"})
    assert _get_caller_tier(req, {}) is None


# ============================================================================
# Caller tier: X-Force-Big backward compat
# ============================================================================

def test_x_force_big_maps_to_complex():
    req = FakeRequest({"x-force-big": "true"})
    assert _get_caller_tier(req, {}) == ComplexityTier.COMPLEX


def test_x_force_big_false_ignored():
    req = FakeRequest({"x-force-big": "false"})
    assert _get_caller_tier(req, {}) is None


def test_force_big_full_backward_compat():
    """X-Force-Big should result in COMPLEX tier in classify_request."""
    body = {"messages": [{"role": "user", "content": "What is 2+2?"}]}
    req = FakeRequest({"x-force-big": "true"})
    result = classify_request(req, body)
    assert result.tier == ComplexityTier.COMPLEX
    assert result.caller_tier == ComplexityTier.COMPLEX


# ============================================================================
# Caller tier: #force_big tag backward compat
# ============================================================================

def test_force_big_tag_in_message():
    body = {"messages": [{"role": "user", "content": "Hello #force_big"}]}
    assert _get_caller_tier(FakeRequest(), body) == ComplexityTier.COMPLEX


def test_force_big_tag_not_present():
    body = {"messages": [{"role": "user", "content": "Hello"}]}
    assert _get_caller_tier(FakeRequest(), body) is None


# ============================================================================
# Caller tier: API key metadata
# ============================================================================

def test_api_key_complexity_metadata():
    key = FakeApiKey(metadata={"complexity": "moderate"})
    assert _get_caller_tier(FakeRequest(), {}, key) == ComplexityTier.MODERATE


def test_api_key_no_metadata():
    key = FakeApiKey(metadata=None)
    assert _get_caller_tier(FakeRequest(), {}, key) is None


def test_api_key_no_complexity_field():
    key = FakeApiKey(metadata={"priority": 0})
    assert _get_caller_tier(FakeRequest(), {}, key) is None


# ============================================================================
# Caller tier: Source-based defaults
# ============================================================================

def test_n8n_source_defaults_moderate():
    req = FakeRequest({"x-source": "n8n"})
    assert _get_caller_tier(req, {}) == ComplexityTier.MODERATE


def test_agent_source_defaults_moderate():
    req = FakeRequest({"x-source": "agent"})
    assert _get_caller_tier(req, {}) == ComplexityTier.MODERATE


def test_agent_harness_source_defaults_moderate():
    req = FakeRequest({"x-source": "agent-harness"})
    assert _get_caller_tier(req, {}) == ComplexityTier.MODERATE


def test_unknown_source_no_default():
    req = FakeRequest({"x-source": "web-ui"})
    assert _get_caller_tier(req, {}) is None


# ============================================================================
# Conflict resolution: max(caller, heuristic)
# ============================================================================

def test_heuristic_cannot_downgrade_caller():
    """Even if heuristics say ROUTINE, caller COMPLEX wins."""
    body = {"messages": [{"role": "user", "content": "Hi"}]}
    req = FakeRequest({"x-complexity": "complex"})
    result = classify_request(req, body)
    assert result.tier == ComplexityTier.COMPLEX
    assert result.heuristic_tier == ComplexityTier.ROUTINE
    assert result.caller_tier == ComplexityTier.COMPLEX


def test_heuristic_escalates_over_caller():
    """If heuristics score higher than caller declaration, heuristic wins."""
    body = {
        "messages": [
            {"role": "system", "content": "You are a developer."},
            {"role": "user", "content": "Debug this architecture problem"},
        ],
        "tools": [{"type": "function"} for _ in range(4)],
    }
    req = FakeRequest({"x-complexity": "routine"})
    result = classify_request(req, body)
    # Heuristics should push past ROUTINE
    assert result.tier >= ComplexityTier.MODERATE
    assert result.caller_tier == ComplexityTier.ROUTINE


def test_no_caller_signal_heuristic_only():
    body = {
        "messages": [
            {"role": "system", "content": "You write code."},
            {"role": "user", "content": "Implement a cache"},
        ],
        "tools": [{"type": "function"}],
    }
    result = classify_request(FakeRequest(), body)
    assert result.caller_tier is None
    assert result.tier == result.heuristic_tier


# ============================================================================
# Integration-style: realistic scenarios
# ============================================================================

def test_simple_qa_routes_to_3070():
    body = {"messages": [{"role": "user", "content": "What's the capital of France?"}]}
    result = classify_request(FakeRequest(), body)
    assert TIER_MODEL_MAP[result.tier] == "qwen2.5-7b-awq"


def test_coding_with_tools_routes_to_3090():
    body = {
        "messages": [
            {"role": "system", "content": "You are a software engineer."},
            {"role": "user", "content": "Refactor this function to use async/await"},
        ],
        "tools": [{"type": "function", "function": {"name": "read_file"}}],
    }
    result = classify_request(FakeRequest(), body)
    assert TIER_MODEL_MAP[result.tier] == "qwen2.5-14b-awq"


def test_agent_harness_source_routes_to_3090():
    body = {"messages": [{"role": "user", "content": "Quick task"}]}
    req = FakeRequest({"x-source": "agent-harness"})
    result = classify_request(req, body)
    assert TIER_MODEL_MAP[result.tier] == "qwen2.5-14b-awq"
