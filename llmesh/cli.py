"""
CLI entry point.

Usage:
    llmesh "build a REST API with auth"
    llmesh --agents claude,gemini "refactor auth module"
    llmesh --strategy plan-review-execute "build a dashboard"
    llmesh --dry-run "migrate database"  # show plan without executing
"""

import argparse
import sys
from typing import List

from llmesh.agents.base import BaseAgent, AgentNotFound
from llmesh.agents.mock import MockAgent
from llmesh.agents.claude import ClaudeAgent
from llmesh.agents.gemini import GeminiAgent
from llmesh.orchestrator import Orchestrator, OrchestratorConfig
from llmesh.tui.display import try_create_tui
from llmesh.config import Config


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="LLMesh - Multi-Agent Orchestrator for Claude and Gemini CLIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  llmesh "build a REST API with JWT auth"
  llmesh --strategy simple "create a hello world Flask app"
  llmesh --dry-run "build a dashboard with React"
  llmesh --agents mock "test the orchestration"
        """
    )

    parser.add_argument(
        "task",
        type=str,
        help="Task description for the agents to work on"
    )

    parser.add_argument(
        "--agents",
        type=str,
        default="auto",
        help="Comma-separated agent names (default: auto-detect). Options: claude,gemini,mock"
    )

    parser.add_argument(
        "--strategy",
        type=str,
        default=None,
        help="Orchestration strategy (default: from config). Options: plan-review-execute, simple, quality"
    )

    parser.add_argument(
        "--work-dir",
        type=str,
        default=".",
        help="Working directory (default: current directory)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show plan only, don't execute"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show full agent outputs"
    )

    parser.add_argument(
        "--max-rounds",
        type=int,
        default=None,
        help="Maximum discussion rounds (default: from config)"
    )

    parser.add_argument(
        "--simple-tui",
        action="store_true",
        help="Use simple print-based TUI (no curses)"
    )

    return parser.parse_args()


def create_agents(agent_names: str) -> List[BaseAgent]:
    """
    Create agent instances based on requested names.

    Args:
        agent_names: Comma-separated agent names or "auto"

    Returns:
        List of available agents
    """
    if agent_names == "auto":
        # Auto-detect available agents
        agents = []

        # Try Claude
        try:
            claude = ClaudeAgent()
            if claude.is_available():
                agents.append(claude)
                print(f"✓ Found Claude CLI")
        except Exception:
            pass

        # Try Gemini
        try:
            gemini = GeminiAgent()
            if gemini.is_available():
                agents.append(gemini)
                print(f"✓ Found Gemini CLI")
        except Exception:
            pass

        # Fallback to mock agents if no real agents found
        if not agents:
            print("⚠ No real CLIs found. Using mock agents for demonstration.")
            agents = [
                MockAgent(
                    name="mock_gemini",
                    cost_tier="free",
                    responses={
                        "plan": "Mock plan:\n---\nSUBTASK: Create main file\nDIFFICULTY: EASY\nFILES: main.py\nREASON: Simple boilerplate\n---",
                        "default": "Mock {prompt[:50]}... [simulated response]"
                    }
                ),
                MockAgent(
                    name="mock_claude",
                    cost_tier="expensive",
                    responses={
                        "review": "Mock review: Looks good, minor suggestions...",
                        "default": "Mock {prompt[:50]}... [simulated response]"
                    }
                )
            ]

        return agents

    else:
        # Manually specified agents
        requested = [name.strip().lower() for name in agent_names.split(",")]
        agents = []

        for name in requested:
            if name == "claude":
                agent = ClaudeAgent()
                if not agent.is_available():
                    print(f"⚠ Claude CLI not found. Install from: https://claude.ai/download")
                    continue
                agents.append(agent)
                print(f"✓ Using Claude CLI")

            elif name == "gemini":
                agent = GeminiAgent()
                if not agent.is_available():
                    print(f"⚠ Gemini CLI not found.")
                    continue
                agents.append(agent)
                print(f"✓ Using Gemini CLI")

            elif name == "mock":
                agents.append(MockAgent(name="mock_gemini", cost_tier="free"))
                agents.append(MockAgent(name="mock_claude", cost_tier="expensive"))
                print(f"✓ Using Mock agents")

        return agents


def main():
    """Main entry point for llmesh CLI."""
    args = parse_args()

    # Load config
    config = Config()

    # Create agents
    print("Initializing agents...")
    agents = create_agents(args.agents)

    if not agents:
        print("❌ Error: No agents available. Install Claude or Gemini CLI, or use --agents mock")
        return 1

    # Create orchestrator config
    orch_config = OrchestratorConfig(
        strategy=args.strategy or config.default_strategy,
        max_rounds=args.max_rounds or config.max_rounds,
        work_dir=args.work_dir,
        verbose=args.verbose,
        dry_run=args.dry_run
    )

    # Create TUI
    tui = try_create_tui(use_simple=args.simple_tui)

    # Create orchestrator
    orchestrator = Orchestrator(
        agents=agents,
        config=orch_config,
        on_event=tui.handle_event
    )

    # Run the task
    print(f"\nTask: {args.task}")
    print(f"Strategy: {orch_config.strategy}")
    print()

    try:
        result = orchestrator.run(args.task)

        if result.success:
            print("\n" + "="*60)
            print("FINAL OUTPUT")
            print("="*60)
            print(result.final_output)
            print()
            return 0
        else:
            print(f"\n❌ Task failed: {result.error}")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        return 130

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    finally:
        tui.finalize()


if __name__ == "__main__":
    sys.exit(main())
