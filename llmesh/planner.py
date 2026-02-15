"""
Task planner — breaks a high-level task into subtasks.

Uses the cheap agent (Gemini) to create a plan, then parses
the plan into structured subtasks with difficulty ratings.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


# Prefix added to all prompts to prevent agent-mode CLIs from trying
# to use tools/read files instead of just responding with text.
_RESPONSE_ONLY_PREFIX = """IMPORTANT: You are being used as a text-generation backend.
DO NOT use any tools. DO NOT read, write, or search for files.
DO NOT investigate the current directory or codebase.
Just respond directly with text based on the instructions below.
Ignore any existing files or project context — work ONLY from what is provided here.

"""


@dataclass
class Subtask:
    """A single subtask extracted from a plan."""
    description: str
    difficulty: str          # "EASY" | "MEDIUM" | "HARD"
    assigned_agent: str = "" # "gemini" | "claude" — set by router
    files: List[str] = field(default_factory=list)
    dependencies: List[int] = field(default_factory=list)
    status: str = "pending"  # "pending" | "in_progress" | "done"
    result: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.difficulty}: {self.description[:60]}..."


class TaskPlanner:
    """Breaks tasks into subtasks using structured prompts."""

    @staticmethod
    def parse_subtasks(plan_text: str) -> List[Subtask]:
        """
        Parse subtasks from a plan text.

        Expects format:
        ---
        SUBTASK: description
        DIFFICULTY: EASY | MEDIUM | HARD
        FILES: file1.py, file2.py
        REASON: why this difficulty
        ---
        """
        subtasks = []

        # Split by --- markers
        sections = re.split(r'\n---+\n', plan_text)

        for section in sections:
            section = section.strip()
            if not section or len(section) < 10:
                continue

            # Extract fields
            description = TaskPlanner._extract_field(section, "SUBTASK")
            difficulty = TaskPlanner._extract_field(section, "DIFFICULTY")
            files_str = TaskPlanner._extract_field(section, "FILES")

            if not description:
                continue

            # Normalize difficulty
            difficulty = difficulty.upper() if difficulty else "MEDIUM"
            if difficulty not in ["EASY", "MEDIUM", "HARD"]:
                difficulty = "MEDIUM"

            # Parse files
            files = []
            if files_str:
                files = [f.strip() for f in files_str.split(",") if f.strip()]

            subtask = Subtask(
                description=description,
                difficulty=difficulty,
                files=files
            )
            subtasks.append(subtask)

        return subtasks

    @staticmethod
    def _extract_field(text: str, field_name: str) -> str:
        """Extract a field value from text."""
        pattern = rf'{field_name}:\s*(.+?)(?:\n[A-Z]+:|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    @staticmethod
    def create_planning_prompt(task: str) -> str:
        """Generate the planning prompt for an agent."""
        return _RESPONSE_ONLY_PREFIX + f"""You are a senior software developer planning a project.

TASK: {task}

Create a detailed implementation plan:

1. PROJECT STRUCTURE: List all files and directories to create
2. DESIGN DECISIONS: Key technical choices and why
3. SUBTASKS: Break the work into discrete subtasks

For each subtask, use this EXACT format:
---
SUBTASK: [clear description of what to implement]
DIFFICULTY: [EASY or HARD]
FILES: [comma-separated list of files]
REASON: [why this difficulty level]
---

EASY = boilerplate, config, simple CRUD, docs, tests
HARD = security-critical, complex algorithms, architecture, tricky logic

Be thorough but practical. Focus on working code, not perfection."""

    @staticmethod
    def create_review_prompt(task: str, plan: str) -> str:
        """Generate the review prompt for an agent."""
        return _RESPONSE_ONLY_PREFIX + f"""You are a senior architect reviewing a project plan.

TASK: {task}

PROPOSED PLAN:
{plan}

Review this plan and provide BRIEF, ACTIONABLE feedback:
1. What's WRONG or MISSING? (security issues, bad patterns, missing edge cases)
2. What should change? (specific improvements, not vague suggestions)
3. Any subtask difficulty ratings you disagree with?

Be CONCISE. Only flag real issues. Don't rewrite the plan.
Max 10 bullet points."""

    @staticmethod
    def create_revision_prompt(task: str, plan: str, feedback: str) -> str:
        """Generate the revision prompt for an agent."""
        return _RESPONSE_ONLY_PREFIX + f"""Update this project plan based on review feedback.

TASK: {task}

ORIGINAL PLAN:
{plan}

REVIEW FEEDBACK:
{feedback}

Provide the REVISED plan using the same format as before:
---
SUBTASK: ...
DIFFICULTY: ...
FILES: ...
REASON: ...
---"""
