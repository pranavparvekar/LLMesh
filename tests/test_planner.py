"""Tests for task planner."""

import pytest
from llmesh.planner import TaskPlanner, Subtask


def test_parse_subtasks_basic():
    """Test parsing subtasks from plan text."""
    plan_text = """
Here's the plan:

---
SUBTASK: Create main application file
DIFFICULTY: EASY
FILES: app.py, config.py
REASON: Simple boilerplate
---

---
SUBTASK: Implement authentication
DIFFICULTY: HARD
FILES: auth.py
REASON: Security-critical code
---
    """

    subtasks = TaskPlanner.parse_subtasks(plan_text)

    assert len(subtasks) == 2

    assert subtasks[0].description == "Create main application file"
    assert subtasks[0].difficulty == "EASY"
    assert subtasks[0].files == ["app.py", "config.py"]

    assert subtasks[1].description == "Implement authentication"
    assert subtasks[1].difficulty == "HARD"
    assert subtasks[1].files == ["auth.py"]


def test_parse_subtasks_empty():
    """Test parsing empty or invalid plan."""
    subtasks = TaskPlanner.parse_subtasks("")
    assert len(subtasks) == 0

    subtasks = TaskPlanner.parse_subtasks("Just some text without subtask markers")
    assert len(subtasks) == 0


def test_parse_subtasks_normalize_difficulty():
    """Test difficulty normalization."""
    plan_text = """
---
SUBTASK: Task 1
DIFFICULTY: easy
FILES: file1.py
REASON: Test
---

---
SUBTASK: Task 2
DIFFICULTY: INVALID
FILES: file2.py
REASON: Test
---
    """

    subtasks = TaskPlanner.parse_subtasks(plan_text)

    assert subtasks[0].difficulty == "EASY"  # Normalized to uppercase
    assert subtasks[1].difficulty == "MEDIUM"  # Invalid normalized to MEDIUM


def test_create_planning_prompt():
    """Test planning prompt generation."""
    prompt = TaskPlanner.create_planning_prompt("Build a web app")

    assert "Build a web app" in prompt
    assert "SUBTASK" in prompt
    assert "DIFFICULTY" in prompt
    assert "FILES" in prompt


def test_create_review_prompt():
    """Test review prompt generation."""
    prompt = TaskPlanner.create_review_prompt("Task", "Plan content")

    assert "Task" in prompt
    assert "Plan content" in prompt
    assert "review" in prompt.lower()


def test_create_revision_prompt():
    """Test revision prompt generation."""
    prompt = TaskPlanner.create_revision_prompt("Task", "Plan", "Feedback")

    assert "Task" in prompt
    assert "Plan" in prompt
    assert "Feedback" in prompt
