"""Tests for task router."""

import pytest
from llmesh.router import TaskRouter
from llmesh.planner import Subtask
from llmesh.agents.mock import MockAgent


@pytest.fixture
def mock_agents():
    """Create mock agents for testing."""
    return [
        MockAgent(name="cheap", cost_tier="free"),
        MockAgent(name="expensive", cost_tier="expensive"),
    ]


@pytest.fixture
def router(mock_agents):
    """Create a router with mock agents."""
    return TaskRouter(mock_agents)


def test_router_init(mock_agents):
    """Test router initialization."""
    router = TaskRouter(mock_agents)

    assert len(router.agents) == 2
    assert "cheap" in router.agents
    assert "expensive" in router.agents
    assert len(router.cheap_agents) == 1
    assert len(router.expensive_agents) == 1


def test_select_agent_easy(router):
    """Test routing EASY tasks to cheap agent."""
    subtask = Subtask(description="Simple task", difficulty="EASY")
    agent_name = router.select_agent(subtask)

    assert agent_name == "cheap"


def test_select_agent_hard(router):
    """Test routing HARD tasks to expensive agent."""
    subtask = Subtask(description="Complex task", difficulty="HARD")
    agent_name = router.select_agent(subtask)

    assert agent_name == "expensive"


def test_select_agent_medium_non_critical(router):
    """Test routing MEDIUM non-critical tasks to cheap agent."""
    subtask = Subtask(description="Medium difficulty task", difficulty="MEDIUM")
    agent_name = router.select_agent(subtask)

    assert agent_name == "cheap"


def test_select_agent_medium_critical(router):
    """Test routing MEDIUM security-critical tasks to expensive agent."""
    subtask = Subtask(
        description="Implement auth validation and security",
        difficulty="MEDIUM"
    )
    agent_name = router.select_agent(subtask)

    assert agent_name == "expensive"  # Security keywords detected


def test_route_subtasks(router):
    """Test routing multiple subtasks."""
    subtasks = [
        Subtask(description="Easy task", difficulty="EASY"),
        Subtask(description="Hard task", difficulty="HARD"),
        Subtask(description="Medium task", difficulty="MEDIUM"),
    ]

    routed = router.route_subtasks(subtasks)

    assert routed[0].assigned_agent == "cheap"
    assert routed[1].assigned_agent == "expensive"
    assert routed[2].assigned_agent == "cheap"


def test_get_agent(router):
    """Test getting agent by name."""
    agent = router.get_agent("cheap")
    assert agent.name == "cheap"

    with pytest.raises(ValueError):
        router.get_agent("nonexistent")


def test_get_cheap_agent(router):
    """Test getting cheap agent."""
    agent = router.get_cheap_agent()
    assert agent.cost_tier == "free"


def test_get_expensive_agent(router):
    """Test getting expensive agent."""
    agent = router.get_expensive_agent()
    assert agent.cost_tier == "expensive"
