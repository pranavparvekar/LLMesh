"""
Discussion state management.

Tracks the full conversation between agents:
- All messages exchanged
- Which agent said what
- Token estimates per agent
- Current phase
- Discussion summary
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional


@dataclass
class DiscussionMessage:
    """A single message in the agent discussion."""
    agent_name: str       # "claude" | "gemini" | "orchestrator" | "user"
    phase: str            # "planning" | "review" | "execution" | "integration"
    content: str
    timestamp: datetime
    token_estimate: int

    def __str__(self) -> str:
        return f"[{self.agent_name}] {self.content[:100]}..."


@dataclass
class DiscussionStats:
    """Statistics about a completed discussion."""
    total_rounds: int = 0
    tokens_by_agent: Dict[str, int] = field(default_factory=dict)
    duration_seconds: float = 0.0
    tokens_saved_estimate: int = 0
    savings_percent: float = 0.0
    phases_completed: List[str] = field(default_factory=list)

    def calculate_savings(self):
        """
        Calculate estimated token savings vs doing everything with expensive agent.

        Assumes all work could have been done by the expensive agent.
        Savings = tokens used by cheap agents (since expensive agent would have done it all)
        """
        cheap_tokens = sum(
            tokens for agent, tokens in self.tokens_by_agent.items()
            if agent.lower() in ["gemini", "mock_gemini", "mock"]
        )

        expensive_tokens = sum(
            tokens for agent, tokens in self.tokens_by_agent.items()
            if agent.lower() in ["claude", "mock_claude"]
        )

        total_tokens = sum(self.tokens_by_agent.values())

        # Savings: if expensive agent did everything, it would be total_tokens
        # But we only spent expensive_tokens on expensive agent
        # So we saved (total_tokens - expensive_tokens) expensive tokens
        self.tokens_saved_estimate = cheap_tokens

        # Savings percent: what % of total work was done by cheap agents
        if total_tokens > 0:
            self.savings_percent = (cheap_tokens / total_tokens) * 100
        else:
            self.savings_percent = 0.0


@dataclass
class DiscussionResult:
    """Complete result of a multi-agent discussion."""
    task: str
    messages: List[DiscussionMessage] = field(default_factory=list)
    final_output: str = ""
    stats: DiscussionStats = field(default_factory=DiscussionStats)
    success: bool = True
    error: Optional[str] = None

    def add_message(self, message: DiscussionMessage):
        """Add a message to the discussion."""
        self.messages.append(message)

        # Update token stats
        agent = message.agent_name
        if agent not in self.stats.tokens_by_agent:
            self.stats.tokens_by_agent[agent] = 0
        self.stats.tokens_by_agent[agent] += message.token_estimate

    def get_conversation_history(self, max_messages: int = None) -> str:
        """Get formatted conversation history for context."""
        messages = self.messages
        if max_messages:
            messages = messages[-max_messages:]

        lines = []
        for msg in messages:
            lines.append(f"[{msg.agent_name} - {msg.phase}]")
            lines.append(msg.content)
            lines.append("")

        return "\n".join(lines)
