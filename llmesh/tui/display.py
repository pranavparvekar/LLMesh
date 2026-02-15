"""
Terminal UI for watching agents discuss in real-time.

Supports both simple print-based output and curses-based interactive TUI.
"""

import sys
import io
import os
from typing import Dict, Any

# Fix Windows console encoding for Unicode emojis
if sys.platform == "win32":
    try:
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
        # Only wrap if not already wrapped in utf-8
        if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'buffer') and getattr(sys.stderr, 'encoding', '').lower() != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass  # If reconfiguration fails, continue without emojis


class SimpleTUI:
    """
    Simple print-based TUI for when curses is not available.

    Just prints messages as they arrive:
    [Agent] Phase: message...
    """

    def __init__(self):
        self.current_phase = ""
        self.agent_colors = {
            "claude": "\033[94m",      # Blue
            "gemini": "\033[92m",      # Green
            "mock": "\033[93m",        # Yellow
            "mock_claude": "\033[94m",
            "mock_gemini": "\033[92m",
        }
        self.reset_color = "\033[0m"
        self.token_counts = {}

    def handle_event(self, event_type: str, data: Dict[str, Any]):
        """Handle an event from the orchestrator."""

        if event_type == "phase_start":
            phase = data.get("phase", "")
            agent = data.get("agent", "")
            self.current_phase = phase
            print(f"\n{'='*60}")
            print(f"Phase: {phase.upper()} | Agent: {agent}")
            print(f"{'='*60}\n")

        elif event_type == "agent_start":
            agent = data.get("agent", "")
            phase = data.get("phase", "")
            color = self.agent_colors.get(agent, "")
            print(f"{color}🤖 {agent.upper()} ({phase}):{self.reset_color}")

        elif event_type == "agent_chunk":
            chunk = data.get("chunk", "")
            print(chunk, end="", flush=True)

        elif event_type == "agent_done":
            agent = data.get("agent", "")
            response = data.get("response")
            if response:
                self.token_counts[agent] = self.token_counts.get(agent, 0) + response.token_estimate
            print()  # Newline after agent completes

        elif event_type == "subtasks_parsed":
            count = data.get("count", 0)
            print(f"\n📋 Parsed {count} subtasks from plan\n")

        elif event_type == "subtask_start":
            index = data.get("index", 0)
            subtask = data.get("subtask")
            agent = data.get("agent", "")
            if subtask:
                print(f"\n  [{index+1}] {subtask.difficulty}: {subtask.description[:60]}...")
                print(f"      → Assigned to: {agent}")

        elif event_type == "subtask_complete":
            index = data.get("index", 0)
            print(f"      ✅ Subtask {index+1} complete")

        elif event_type == "task_complete":
            result = data.get("result")
            stats = data.get("stats")
            print(f"\n{'='*60}")
            print("✅ TASK COMPLETE")
            print(f"{'='*60}")
            if stats:
                print(f"\nToken Usage:")
                for agent, tokens in stats.tokens_by_agent.items():
                    print(f"  {agent}: {tokens:,} tokens")
                print(f"\nTotal Duration: {stats.duration_seconds:.2f}s")
                print(f"Token Savings: {stats.savings_percent:.1f}%")
                print(f"Phases: {', '.join(stats.phases_completed)}")
            print()

        elif event_type == "error":
            message = data.get("message", "")
            print(f"\n❌ ERROR: {message}\n", file=sys.stderr)

    def finalize(self):
        """Clean up (no-op for simple TUI)."""
        pass


def try_create_tui(use_simple: bool = False) -> SimpleTUI:
    """
    Try to create the best available TUI.

    For now, always returns SimpleTUI.
    Future: Try curses-based TUI first, fallback to SimpleTUI.

    Args:
        use_simple: Force simple print-based TUI

    Returns:
        TUI instance
    """
    # If simple requested or rich not available, return SimpleTUI
    if use_simple:
        return SimpleTUI()

    try:
        from llmesh.tui.rich_display import RichTUI
        return RichTUI()
    except ImportError:
        return SimpleTUI()
