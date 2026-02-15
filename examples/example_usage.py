"""
Example usage of LLMesh programmatically (not via CLI).

This demonstrates how to use LLMesh as a library in your own Python code.
"""

from llmesh.agents.mock import MockAgent
from llmesh.orchestrator import Orchestrator, OrchestratorConfig
from llmesh.tui.display import SimpleTUI


def main():
    """Run a simple example with mock agents."""

    # Create mock agents
    gemini_agent = MockAgent(
        name="mock_gemini",
        cost_tier="free",
        responses={
            "plan": """
Here's my plan:

PROJECT STRUCTURE:
- app.py (main application)
- requirements.txt (dependencies)

---
SUBTASK: Create Flask app
DIFFICULTY: EASY
FILES: app.py
REASON: Simple Flask boilerplate
---

---
SUBTASK: Add requirements file
DIFFICULTY: EASY
FILES: requirements.txt
REASON: Simple dependency list
---
            """,
            "revision": """
REVISED PLAN:

---
SUBTASK: Create Flask app with error handling
DIFFICULTY: EASY
FILES: app.py
REASON: Simple Flask boilerplate with basic error handling
---

---
SUBTASK: Add requirements file
DIFFICULTY: EASY
FILES: requirements.txt
REASON: Simple dependency list
---
            """,
            "integration": """
=== FILE: app.py ===
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)
=== END FILE ===

=== FILE: requirements.txt ===
Flask==3.0.0
=== END FILE ===
            """,
            "default": "Mock Gemini response for: {prompt}"
        }
    )

    claude_agent = MockAgent(
        name="mock_claude",
        cost_tier="expensive",
        responses={
            "review": "Plan looks good. Suggestion: Add basic error handling to the Flask app.",
            "final": "LGTM. Code is clean and follows Flask best practices.",
            "default": "Mock Claude response for: {prompt}"
        }
    )

    # Create TUI
    tui = SimpleTUI()

    # Create orchestrator config
    config = OrchestratorConfig(
        strategy="plan-review-execute",
        dry_run=False,  # Set to True to see plan only
        verbose=True
    )

    # Create orchestrator
    orchestrator = Orchestrator(
        agents=[gemini_agent, claude_agent],
        config=config,
        on_event=tui.handle_event
    )

    # Run the task
    task = "Build a simple Flask hello world web application"
    print(f"Task: {task}\n")

    result = orchestrator.run(task)

    # Display results
    if result.success:
        print("\n" + "="*70)
        print("SUCCESS!")
        print("="*70)
        print(f"\nFinal Output:\n{result.final_output}\n")
        print(f"Token Usage: {result.stats.tokens_by_agent}")
        print(f"Savings: {result.stats.savings_percent:.1f}%")
        print(f"Duration: {result.stats.duration_seconds:.2f}s")
    else:
        print(f"\nFailed: {result.error}")


if __name__ == "__main__":
    main()
