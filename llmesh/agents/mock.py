"""
Mock agent for testing without real CLIs installed.

Returns pre-configured responses or simple echo responses.
Essential for development and testing.
"""

import time
from typing import Dict, Callable
from llmesh.agents.base import BaseAgent, AgentResponse


class MockAgent(BaseAgent):
    """
    Mock agent that returns configurable responses.

    Usage:
        mock = MockAgent(
            name="mock_gemini",
            cost_tier="free",
            responses={
                "plan": "Here's my plan: ...",
                "default": "Mock response for: {prompt}"
            }
        )
    """

    def __init__(
        self,
        name: str = "mock",
        cost_tier: str = "free",
        responses: Dict[str, str] = None,
        delay: float = 0.1
    ):
        self._name = name
        self._cost_tier = cost_tier
        self._responses = responses or {}
        self._delay = delay  # Simulate processing time

    def send(self, prompt: str, timeout: int = 120) -> AgentResponse:
        """Return a mock response based on prompt matching."""
        start_time = time.time()

        # Simulate processing delay
        time.sleep(self._delay)

        # Try to match prompt against configured responses
        response_content = self._get_response(prompt)

        duration = time.time() - start_time
        token_estimate = self._estimate_tokens(response_content)

        return AgentResponse(
            content=response_content,
            token_estimate=token_estimate,
            duration_seconds=duration,
            agent_name=self._name,
            success=True,
            error=None
        )

    def stream(self, prompt: str, on_chunk: Callable[[str], None]) -> AgentResponse:
        """Stream mock response character by character."""
        start_time = time.time()

        response_content = self._get_response(prompt)

        # Stream the response in chunks
        chunk_size = 10
        for i in range(0, len(response_content), chunk_size):
            chunk = response_content[i:i + chunk_size]
            on_chunk(chunk)
            time.sleep(self._delay / 10)  # Small delay between chunks

        duration = time.time() - start_time
        token_estimate = self._estimate_tokens(response_content)

        return AgentResponse(
            content=response_content,
            token_estimate=token_estimate,
            duration_seconds=duration,
            agent_name=self._name,
            success=True,
            error=None
        )

    def is_available(self) -> bool:
        """Mock agents are always available."""
        return True

    @property
    def name(self) -> str:
        return self._name

    @property
    def cost_tier(self) -> str:
        return self._cost_tier

    def _get_response(self, prompt: str) -> str:
        """Match prompt against configured responses."""
        prompt_lower = prompt.lower()

        # Try exact keyword matches
        for keyword, response in self._responses.items():
            if keyword.lower() in prompt_lower:
                return response.format(prompt=prompt)

        # Fall back to default response
        if "default" in self._responses:
            return self._responses["default"].format(prompt=prompt)

        # Ultimate fallback
        return f"[{self._name}] Mock response to: {prompt[:100]}..."

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate: ~4 chars per token."""
        return max(1, len(text) // 4)
