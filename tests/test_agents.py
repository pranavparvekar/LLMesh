"""Tests for agent implementations."""

import pytest
from llmesh.agents.mock import MockAgent
from llmesh.agents.base import AgentResponse


def test_mock_agent_send():
    """Test mock agent basic send."""
    agent = MockAgent(
        name="test_agent",
        cost_tier="free",
        responses={"test": "Test response"}
    )

    response = agent.send("This is a test prompt")

    assert isinstance(response, AgentResponse)
    assert response.success
    assert response.agent_name == "test_agent"
    assert "test" in response.content.lower()


def test_mock_agent_with_default():
    """Test mock agent with default response."""
    agent = MockAgent(
        name="test",
        responses={"default": "Default: {prompt}"}
    )

    response = agent.send("Any prompt")

    assert response.success
    assert "Any prompt" in response.content


def test_mock_agent_stream():
    """Test mock agent streaming."""
    agent = MockAgent(name="test", delay=0.01)

    chunks = []

    def collect_chunk(chunk):
        chunks.append(chunk)

    response = agent.stream("Test prompt", collect_chunk)

    assert response.success
    assert len(chunks) > 0
    assert ''.join(chunks) == response.content


def test_mock_agent_is_available():
    """Test mock agent availability check."""
    agent = MockAgent(name="test")
    assert agent.is_available() is True


def test_mock_agent_properties():
    """Test mock agent properties."""
    agent = MockAgent(name="custom_name", cost_tier="expensive")

    assert agent.name == "custom_name"
    assert agent.cost_tier == "expensive"
