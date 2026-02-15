"""
Orchestrator — Manages multi-agent discussion and task execution.

The orchestrator implements different strategies for how agents collaborate:

Strategy 1: "plan-review-execute" (default)
    1. Cheap agent creates a plan
    2. Expensive agent reviews and critiques
    3. Cheap agent revises plan
    4. Both agents execute subtasks (easy→cheap, hard→expensive)
    5. Cheap agent integrates
    6. Expensive agent does final review

Strategy 2: "simple" - just route to the cheap agent for everything
Strategy 3: "quality" - route everything to expensive agent
"""

import time
from datetime import datetime
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass

from llmesh.agents.base import BaseAgent, AgentResponse
from llmesh.discussion import DiscussionResult, DiscussionMessage, DiscussionStats
from llmesh.planner import TaskPlanner, Subtask, _RESPONSE_ONLY_PREFIX
from llmesh.router import TaskRouter


@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator."""
    strategy: str = "plan-review-execute"
    max_rounds: int = 10
    work_dir: str = "."
    verbose: bool = False
    dry_run: bool = False


class Orchestrator:
    """
    Main orchestrator that runs multi-agent workflows.

    Usage:
        orch = Orchestrator(agents=[claude_agent, gemini_agent])
        result = orch.run("build a REST API", strategy="plan-review-execute")
    """

    def __init__(
        self,
        agents: List[BaseAgent],
        config: OrchestratorConfig = None,
        on_event: Callable[[str, Dict], None] = None
    ):
        """
        Initialize orchestrator.

        Args:
            agents: List of BaseAgent instances
            config: Configuration options
            on_event: Optional callback for events (for TUI display)
        """
        self.agents = agents
        self.config = config or OrchestratorConfig()
        self.router = TaskRouter(agents)
        self.on_event = on_event or (lambda event, data: None)

    def run(self, task: str) -> DiscussionResult:
        """
        Run the full orchestration workflow.

        Args:
            task: The task description from user

        Returns:
            DiscussionResult with complete conversation and stats
        """
        start_time = time.time()

        result = DiscussionResult(task=task)
        result.stats.total_rounds = 0

        try:
            strategy = self.config.strategy.lower()

            if strategy == "plan-review-execute":
                self._run_plan_review_execute(task, result)
            elif strategy == "simple":
                self._run_simple(task, result)
            elif strategy == "quality":
                self._run_quality(task, result)
            else:
                raise ValueError(f"Unknown strategy: {strategy}")

            result.success = True

        except Exception as e:
            result.success = False
            result.error = str(e)
            self._emit_event("error", {"message": str(e)})

        # Finalize stats
        result.stats.duration_seconds = time.time() - start_time
        result.stats.calculate_savings()

        self._emit_event("task_complete", {
            "result": result,
            "stats": result.stats
        })

        return result

    def _run_plan_review_execute(self, task: str, result: DiscussionResult):
        """
        Execute the plan-review-execute strategy.

        1. Cheap agent plans
        2. Expensive agent reviews
        3. Cheap agent revises
        4. Execute subtasks (routed by difficulty)
        5. Cheap agent integrates
        6. Expensive agent final review
        """
        cheap_agent = self.router.get_cheap_agent()
        expensive_agent = self.router.get_expensive_agent()

        # Phase 1: PLANNING
        self._emit_phase_start("planning", cheap_agent.name)
        plan_prompt = TaskPlanner.create_planning_prompt(task)
        plan_response = self._send_to_agent(cheap_agent, plan_prompt, "planning", result)
        plan = plan_response.content

        # Phase 2: REVIEW
        self._emit_phase_start("review", expensive_agent.name)
        review_prompt = TaskPlanner.create_review_prompt(task, plan)
        review_response = self._send_to_agent(expensive_agent, review_prompt, "review", result)
        feedback = review_response.content

        # Phase 3: REVISION
        self._emit_phase_start("revision", cheap_agent.name)
        revision_prompt = TaskPlanner.create_revision_prompt(task, plan, feedback)
        revision_response = self._send_to_agent(cheap_agent, revision_prompt, "revision", result)
        revised_plan = revision_response.content

        # Parse subtasks
        subtasks = TaskPlanner.parse_subtasks(revised_plan)
        self._emit_event("subtasks_parsed", {"count": len(subtasks), "subtasks": subtasks})

        if self.config.dry_run:
            result.final_output = f"DRY RUN - Plan:\n{revised_plan}\n\nSubtasks: {len(subtasks)}"
            return

        # Phase 4: EXECUTION
        self._emit_phase_start("execution", "multiple agents")
        subtasks = self.router.route_subtasks(subtasks)
        execution_results = []

        for i, subtask in enumerate(subtasks):
            self._emit_event("subtask_start", {
                "index": i,
                "subtask": subtask,
                "agent": subtask.assigned_agent
            })

            agent = self.router.get_agent(subtask.assigned_agent)
            exec_prompt = self._create_execution_prompt(task, revised_plan, subtask, execution_results)
            exec_response = self._send_to_agent(agent, exec_prompt, "execution", result)

            subtask.result = exec_response.content
            subtask.status = "done"
            execution_results.append(exec_response.content)

            self._emit_event("subtask_complete", {
                "index": i,
                "subtask": subtask
            })

        # Phase 5: INTEGRATION
        self._emit_phase_start("integration", cheap_agent.name)
        integration_prompt = self._create_integration_prompt(task, revised_plan, execution_results)
        integration_response = self._send_to_agent(cheap_agent, integration_prompt, "integration", result)
        integrated_code = integration_response.content

        # Phase 6: FINAL REVIEW
        self._emit_phase_start("final_review", expensive_agent.name)
        final_review_prompt = self._create_final_review_prompt(task, integrated_code)
        final_response = self._send_to_agent(expensive_agent, final_review_prompt, "final_review", result)

        result.final_output = integrated_code
        result.stats.phases_completed = ["planning", "review", "revision", "execution", "integration", "final_review"]

    def _run_simple(self, task: str, result: DiscussionResult):
        """Simple strategy: just use cheap agent for everything."""
        cheap_agent = self.router.get_cheap_agent()

        self._emit_phase_start("execution", cheap_agent.name)
        prompt = _RESPONSE_ONLY_PREFIX + f"Complete this task:\n\n{task}\n\nProvide complete working code."
        response = self._send_to_agent(cheap_agent, prompt, "execution", result)

        result.final_output = response.content
        result.stats.phases_completed = ["execution"]

    def _run_quality(self, task: str, result: DiscussionResult):
        """Quality strategy: use expensive agent for everything."""
        expensive_agent = self.router.get_expensive_agent()

        self._emit_phase_start("execution", expensive_agent.name)
        prompt = _RESPONSE_ONLY_PREFIX + f"Complete this task with high quality:\n\n{task}\n\nProvide complete, well-architected code."
        response = self._send_to_agent(expensive_agent, prompt, "execution", result)

        result.final_output = response.content
        result.stats.phases_completed = ["execution"]

    def _send_to_agent(
        self,
        agent: BaseAgent,
        prompt: str,
        phase: str,
        result: DiscussionResult
    ) -> AgentResponse:
        """Send a prompt to an agent and record the response."""
        self._emit_event("agent_start", {
            "agent": agent.name,
            "phase": phase
        })

        # Use streaming if on_event is provided (for TUI)
        if self.on_event:
            response = agent.stream(
                prompt,
                lambda chunk: self._emit_event("agent_chunk", {
                    "agent": agent.name,
                    "chunk": chunk
                })
            )
        else:
            response = agent.send(prompt)

        self._emit_event("agent_done", {
            "agent": agent.name,
            "response": response
        })

        # Record message
        message = DiscussionMessage(
            agent_name=agent.name,
            phase=phase,
            content=response.content,
            timestamp=datetime.now(),
            token_estimate=response.token_estimate
        )
        result.add_message(message)
        result.stats.total_rounds += 1

        return response

    def _create_execution_prompt(
        self,
        task: str,
        plan: str,
        subtask: Subtask,
        previous_results: List[str]
    ) -> str:
        """Create execution prompt for a subtask."""
        plan_summary = plan[:500] + "..." if len(plan) > 500 else plan

        context = ""
        if previous_results:
            recent_results = previous_results[-3:]  # Last 3 results for context
            context = "\n\nCONTEXT — What has been built so far:\n"
            context += "\n---\n".join(recent_results)

        return _RESPONSE_ONLY_PREFIX + f"""You are implementing a specific subtask as part of a larger project.

OVERALL TASK: {task}
PROJECT PLAN SUMMARY: {plan_summary}

YOUR SUBTASK: {subtask.description}
FILES TO CREATE/MODIFY: {', '.join(subtask.files) if subtask.files else 'Not specified'}
{context}

Write the complete implementation. Include:
- Full working code (not pseudocode)
- Necessary imports
- Comments for complex logic
- Error handling

Output ONLY the code with file paths. Use this format:
=== FILE: path/to/file.py ===
[code here]
=== END FILE ==="""

    def _create_integration_prompt(
        self,
        task: str,
        plan: str,
        results: List[str]
    ) -> str:
        """Create integration prompt."""
        return _RESPONSE_ONLY_PREFIX + f"""You are integrating code from multiple developers into a final project.

TASK: {task}
PLAN: {plan[:500]}...

CODE PIECES:
{chr(10).join(results)}

Combine everything into a coherent, working project:
1. Resolve any conflicts or inconsistencies
2. Add any missing imports
3. Create __init__.py files as needed
4. Make sure the project runs

Output the complete final project using:
=== FILE: path/to/file.py ===
[code here]
=== END FILE ==="""

    def _create_final_review_prompt(self, task: str, code: str) -> str:
        """Create final review prompt."""
        return _RESPONSE_ONLY_PREFIX + f"""Quick review of this completed project. ONLY flag critical issues.

TASK: {task}

FINAL CODE:
{code}

Check for:
1. Security vulnerabilities
2. Logic errors
3. Missing error handling
4. Anything that would break in production

If everything looks good, say "LGTM" and note any minor suggestions.
Be BRIEF. Max 5 bullet points."""

    def _emit_event(self, event_type: str, data: Dict):
        """Emit an event for the TUI or other listeners."""
        if self.on_event:
            self.on_event(event_type, data)

    def _emit_phase_start(self, phase: str, agent: str):
        """Emit a phase start event."""
        self._emit_event("phase_start", {
            "phase": phase,
            "agent": agent
        })
