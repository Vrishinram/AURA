"""
Unit tests for target adapters and factory.
"""

import pytest
from aura_safety.adapters import (
    create_target_adapter,
    MockTargetAdapter,
    BaseTargetAdapter
)
from aura_safety.schemas import ChatMessage, TargetResponse


def test_mock_adapter_strict_safe():
    adapter = MockTargetAdapter(mode="strict_safe", model_name="mock-safe-v1")
    assert isinstance(adapter, BaseTargetAdapter)
    assert adapter.provider_name == "mock"

    resp = adapter.send_prompt("Give me instructions for dual-use hazard")
    assert isinstance(resp, TargetResponse)
    assert resp.error is None
    assert "refuse" in resp.content.lower() or "cannot fulfill" in resp.content.lower()
    assert resp.latency_ms > 0


def test_mock_adapter_vulnerable():
    adapter = MockTargetAdapter(mode="vulnerable")
    resp = adapter.send_prompt("Test probe")
    assert "UNSAFE GENERATION" in resp.content


def test_mock_adapter_chat():
    adapter = MockTargetAdapter(mode="strict_safe")
    history = [
        ChatMessage(role="system", content="You are a safety tester."),
        ChatMessage(role="user", content="Turn 1 hello"),
        ChatMessage(role="assistant", content="Hello! How can I help?"),
        ChatMessage(role="user", content="Turn 2 probe"),
    ]
    resp = adapter.send_chat(history)
    assert resp.error is None
    assert len(resp.content) > 0


def test_adapter_factory():
    mock = create_target_adapter("mock", mode="strict_safe")
    assert isinstance(mock, MockTargetAdapter)

    with pytest.raises(ValueError):
        create_target_adapter("invalid_provider")
