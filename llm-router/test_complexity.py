"""Unit tests for request source classification module."""
import pytest
from dataclasses import dataclass
from typing import Optional

from complexity import is_agent_request, _AGENT_SOURCES


class FakeRequest:
    def __init__(self, headers=None):
        self.headers = headers or {}


@dataclass
class FakeApiKey:
    name: str = "test-key"
    metadata: Optional[dict] = None


# ============================================================================
# Agent source detection
# ============================================================================

def test_agent_sources_contains_willow():
    assert "willow" in _AGENT_SOURCES
    assert "ralph" not in _AGENT_SOURCES


def test_x_source_header_agent():
    req = FakeRequest(headers={"x-source": "n8n"})
    assert is_agent_request(req) is True


def test_x_source_header_willow():
    req = FakeRequest(headers={"x-source": "willow"})
    assert is_agent_request(req) is True


def test_x_source_header_interactive():
    req = FakeRequest(headers={"x-source": "dashboard"})
    assert is_agent_request(req) is False


def test_no_headers_not_agent():
    req = FakeRequest()
    assert is_agent_request(req) is False


def test_api_key_agent_prefix():
    req = FakeRequest()
    key = FakeApiKey(name="agent-n8n")
    assert is_agent_request(req, key) is True


def test_api_key_critical_prefix():
    req = FakeRequest()
    key = FakeApiKey(name="critical-monitoring")
    assert is_agent_request(req, key) is True


def test_api_key_normal_not_agent():
    req = FakeRequest()
    key = FakeApiKey(name="josh-dashboard")
    assert is_agent_request(req, key) is False


def test_api_key_priority_metadata():
    req = FakeRequest()
    key = FakeApiKey(name="test", metadata={"priority": 0})
    assert is_agent_request(req, key) is True


def test_api_key_priority_1_not_agent():
    req = FakeRequest()
    key = FakeApiKey(name="test", metadata={"priority": 1})
    assert is_agent_request(req, key) is False
