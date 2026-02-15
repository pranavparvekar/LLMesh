"""
LLMesh - Multi-Agent Orchestrator for Claude Code and Gemini CLI.

A CLI tool that enables Claude Code and Gemini CLI to collaborate on tasks,
optimizing cost by routing easy tasks to Gemini and hard tasks to Claude.
"""

__version__ = "0.1.0"
__author__ = "LLMesh Contributors"

from llmesh.orchestrator import Orchestrator
from llmesh.discussion import DiscussionResult, DiscussionMessage, DiscussionStats

__all__ = [
    "Orchestrator",
    "DiscussionResult",
    "DiscussionMessage",
    "DiscussionStats",
]
