"""Tests for orchestrator."""

import pytest
from llmesh.orchestrator import Orchestrator, OrchestratorConfig
from llmesh.agents.mock import MockAgent
from llmesh.discussion import DiscussionResult


@pytest.fixture
def mock_agents():
    """Create mock agents for testing."""
    return [
        MockAgent(
            name="mock_gemini",
            cost_tier="free",
            delay=0.01,
            responses={
                "plan": """
PROJECT STRUCTURE:
- app.py

---
SUBTASK: Create main file
DIFFICULTY: EASY
FILES: app.py
REASON: Simple boilerplate
---
                """,
                "revision": """
REVISED PLAN:

---
SUBTASK: Create main file
DIFFICULTY: EASY
FILES: app.py
REASON: Simple boilerplate
---
                """,
                "integration": "=== FILE: app.py ===\nprint('hello')\n=== END FILE ===",
                "default": "Mock response"
            }
        ),
        MockAgent(
            name="mock_claude",
            cost_tier="expensive",
            delay=0.01,
            responses={
                "review": "Looks good overall. Minor suggestion: add error handling.",
                "final": "LGTM. Code is clean.",
                "default": "Mock response"
            }
        ),
    ]


def test_orchestrator_init(mock_agents):
    """Test orchestrator initialization."""
    config = OrchestratorConfig(strategy="simple")
    orch = Orchestrator(agents=mock_agents, config=config)

    assert orch.config.strategy == "simple"
    assert len(orch.agents) == 2


def test_orchestrator_simple_strategy(mock_agents):
    """Test simple strategy execution."""
    config = OrchestratorConfig(strategy="simple")
    orch = Orchestrator(agents=mock_agents, config=config)

    result = orch.run("Build a hello world app")

    assert isinstance(result, DiscussionResult)
    assert result.success
    assert result.task == "Build a hello world app"
    assert len(result.messages) > 0
    assert result.final_output != ""


def test_orchestrator_quality_strategy(mock_agents):
    """Test quality strategy execution."""
    config = OrchestratorConfig(strategy="quality")
    orch = Orchestrator(agents=mock_agents, config=config)

    result = orch.run("Build a hello world app")

    assert result.success
    assert len(result.messages) > 0


def test_orchestrator_plan_review_execute(mock_agents):
    """Test plan-review-execute strategy."""
    config = OrchestratorConfig(strategy="plan-review-execute", dry_run=True)
    orch = Orchestrator(agents=mock_agents, config=config)

    result = orch.run("Build a hello world app")

    assert result.success
    # In dry run, should have messages for plan, review, revision
    assert len(result.messages) >= 3


def test_orchestrator_event_callbacks(mock_agents):
    """Test event callbacks."""
    events = []

    def event_handler(event_type, data):
        events.append((event_type, data))

    config = OrchestratorConfig(strategy="simple")
    orch = Orchestrator(agents=mock_agents, config=config, on_event=event_handler)

    result = orch.run("Test task")

    assert len(events) > 0
    # Should have at least phase_start, agent_start, agent_done, task_complete
    event_types = [e[0] for e in events]
    assert "phase_start" in event_types
    assert "task_complete" in event_types


def test_orchestrator_token_tracking(mock_agents):
    """Test token usage tracking."""
    config = OrchestratorConfig(strategy="simple")
    orch = Orchestrator(agents=mock_agents, config=config)

    result = orch.run("Test task")

    assert result.stats.tokens_by_agent is not None
    assert len(result.stats.tokens_by_agent) > 0
    assert result.stats.duration_seconds > 0
