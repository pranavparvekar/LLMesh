"""
Base agent interface.

All CLI agents (Claude, Gemini, etc.) implement this interface.
The key method is `send(prompt) -> response` which:
1. Spawns the CLI as a subprocess
2. Passes the prompt
3. Captures and returns the output
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Callable


@dataclass
class AgentResponse:
    """Response from an agent."""
    content: str              # The response text
    token_estimate: int       # Estimated tokens used
    duration_seconds: float   # How long the call took
    agent_name: str
    success: bool
    error: Optional[str] = None


class BaseAgent(ABC):
    """Base interface for all AI agent adapters."""

    @abstractmethod
    def send(self, prompt: str, timeout: int = 120) -> AgentResponse:
        """Send a prompt to the CLI and return the response."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this CLI tool is installed and accessible."""
        pass

    @abstractmethod
    def stream(self, prompt: str, on_chunk: Callable[[str], None]) -> AgentResponse:
        """Send a prompt and stream the response chunk by chunk."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name identifier."""
        pass

    @property
    @abstractmethod
    def cost_tier(self) -> str:
        """Cost tier: 'free', 'cheap', or 'expensive'."""
        pass


class AgentError(Exception):
    """Base exception for agent errors."""
    pass


class AgentNotFound(AgentError):
    """Agent CLI is not installed or not found in PATH."""
    pass


class AgentTimeout(AgentError):
    """Agent took too long to respond."""
    pass
