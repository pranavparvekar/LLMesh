"""
Task router — decides which agent handles which subtask.

Simple rules:
    EASY tasks → cheap agent (Gemini)
    MEDIUM tasks → depends on strategy and budget
    HARD tasks → expensive agent (Claude)

Categories that are always HARD (route to Claude):
    - Security-critical code (auth, encryption, input validation)
    - Complex algorithms
    - Architecture decisions
    - Code review for correctness

Categories that are always EASY (route to Gemini):
    - Boilerplate code
    - Config files
    - Documentation
    - Test scaffolding
    - Simple CRUD operations
    - File structure setup
"""

from typing import List, Dict
from llmesh.planner import Subtask
from llmesh.agents.base import BaseAgent


class TaskRouter:
    """Routes subtasks to appropriate agents based on difficulty."""

    def __init__(self, agents: List[BaseAgent]):
        """
        Initialize router with available agents.

        Args:
            agents: List of available agents
        """
        self.agents = {agent.name: agent for agent in agents}

        # Categorize agents by cost tier
        self.cheap_agents = [a for a in agents if a.cost_tier in ["free", "cheap"]]
        self.expensive_agents = [a for a in agents if a.cost_tier == "expensive"]

    def route_subtasks(self, subtasks: List[Subtask]) -> List[Subtask]:
        """
        Assign agents to subtasks based on difficulty.

        Modifies subtasks in place by setting assigned_agent.
        """
        for subtask in subtasks:
            subtask.assigned_agent = self.select_agent(subtask)
        return subtasks

    def select_agent(self, subtask: Subtask) -> str:
        """
        Select the best agent for a subtask.

        Returns:
            Agent name (e.g., "claude", "gemini")
        """
        difficulty = subtask.difficulty.upper()

        # EASY → cheap agent
        if difficulty == "EASY":
            if self.cheap_agents:
                return self.cheap_agents[0].name
            # Fallback to expensive if no cheap agents
            if self.expensive_agents:
                return self.expensive_agents[0].name

        # HARD → expensive agent
        elif difficulty == "HARD":
            if self.expensive_agents:
                return self.expensive_agents[0].name
            # Fallback to cheap if no expensive agents
            if self.cheap_agents:
                return self.cheap_agents[0].name

        # MEDIUM → prefer cheap, use expensive if critical keywords detected
        else:
            # Check for security/critical keywords
            critical_keywords = [
                "auth", "security", "encryption", "password", "token",
                "permission", "validation", "sanitize", "exploit"
            ]

            desc_lower = subtask.description.lower()
            is_critical = any(kw in desc_lower for kw in critical_keywords)

            if is_critical and self.expensive_agents:
                return self.expensive_agents[0].name
            elif self.cheap_agents:
                return self.cheap_agents[0].name
            elif self.expensive_agents:
                return self.expensive_agents[0].name

        # Ultimate fallback: use first available agent
        if self.agents:
            return list(self.agents.keys())[0]

        raise ValueError("No agents available")

    def get_agent(self, agent_name: str) -> BaseAgent:
        """Get agent instance by name."""
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found")
        return self.agents[agent_name]

    def get_cheap_agent(self) -> BaseAgent:
        """Get the first cheap/free agent."""
        if self.cheap_agents:
            return self.cheap_agents[0]
        if self.expensive_agents:
            return self.expensive_agents[0]
        raise ValueError("No agents available")

    def get_expensive_agent(self) -> BaseAgent:
        """Get the first expensive agent."""
        if self.expensive_agents:
            return self.expensive_agents[0]
        if self.cheap_agents:
            return self.cheap_agents[0]
        raise ValueError("No agents available")
