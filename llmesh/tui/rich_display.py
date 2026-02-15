import sys
from typing import Dict, Any, List

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
except ImportError:
    pass  # Allow import even if rich not installed, handled in display.py

class RichTUI:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        
        # Split into main sections
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3),
        )
        
        # Split main into side-by-side agent panels
        self.layout["main"].split_row(
            Layout(name="left", ratio=1),  # Claude
            Layout(name="right", ratio=1), # Gemini
        )
        
        # Data buffers
        self.buffers = {
            "claude": [],
            "gemini": []
        }
        self.agent_status = {
            "claude": "Idle",
            "gemini": "Idle"
        }
        
        # Provide default status for mock agents too
        self.buffers["mock_claude"] = self.buffers["claude"]
        self.buffers["mock_gemini"] = self.buffers["gemini"]
        self.agent_status["mock_claude"] = "Idle"
        self.agent_status["mock_gemini"] = "Idle"

        self.global_phase = "Initializing"
        self.stats = {
            "tokens": 0, 
            "savings": 0.0, 
            "duration": 0.0
        }
        
        self.live = None
        self._started = False

    def _get_panel_content(self, agent_name: str) -> str:
        # Get last N lines
        # Handle mock agents mapping to main panels
        key = agent_name
        if agent_name.startswith("mock_"):
            key = agent_name.replace("mock_", "")
        
        # If mapped key not in buffers (e.g. some other agent), return empty
        if key not in self.buffers:
            return ""

        lines = self.buffers[key]
        return "\n".join(lines[-30:])

    def update_render(self):
        # Header
        self.layout["header"].update(
            Panel(
                Text("LLMesh Orchestrator", justify="center", style="bold white"),
                style="blue on black",
                box=box.ROUNDED
            )
        )
        
        # Left Panel (Claude)
        claude_content = self._get_panel_content("claude")
        self.layout["left"].update(
            Panel(
                claude_content,
                title=f"Claude ({self.agent_status.get('claude', 'Idle')})",
                border_style="blue",
                box=box.ROUNDED,
                padding=(0, 1)
            )
        )
        
        # Right Panel (Gemini)
        gemini_content = self._get_panel_content("gemini")
        self.layout["right"].update(
            Panel(
                gemini_content,
                title=f"Gemini ({self.agent_status.get('gemini', 'Idle')})",
                border_style="green",
                box=box.ROUNDED,
                padding=(0, 1)
            )
        )
        
        # Footer
        stats_text = f"Phase: {self.global_phase} | Savings: {self.stats['savings']:.1f}% | Duration: {self.stats['duration']:.1f}s"
        self.layout["footer"].update(
            Panel(
                Text(stats_text, justify="center"),
                style="white on black",
                box=box.ROUNDED
            )
        )

    def start(self):
        if not self._started:
            self.live = Live(self.layout, refresh_per_second=10, screen=True)
            self.live.start()
            self._started = True

    def finalize(self):
        if self._started and self.live:
            self.live.stop()
            self._started = False

    def handle_event(self, event_type: str, data: Dict[str, Any]):
        if not self._started:
            self.start()

        if event_type == "phase_start":
            self.global_phase = data.get("phase", "Unknown").upper()
            
        elif event_type == "agent_start":
            agent = data.get("agent", "unknown")
            phase = data.get("phase", "")
            
            # Map mock agents to real names for status
            display_agent = agent.replace("mock_", "")
            self.agent_status[display_agent] = f"Working: {phase}"
            
            self._append_log(display_agent, f"\n--- Started {phase} ---")
            
        elif event_type == "agent_chunk":
            agent = data.get("agent", "unknown")
            chunk = data.get("chunk", "")
            display_agent = agent.replace("mock_", "")
            # Simplistic buffering
            self._append_text(display_agent, chunk)
            
        elif event_type == "agent_done":
            agent = data.get("agent", "unknown")
            display_agent = agent.replace("mock_", "")
            self.agent_status[display_agent] = "Idle"
            self._append_log(display_agent, "\n--- Completed ---")
            
        elif event_type == "subtasks_parsed":
            count = data.get("count", 0)
            self._append_log("gemini", f"\n[Plan] Parsed {count} subtasks")

        elif event_type == "subtask_start":
            subtask = data.get("subtask")
            if subtask:
                 self._append_log("gemini", f"\n[Task] {subtask.description[:40]}...")

        elif event_type == "task_complete":
            self.global_phase = "Complete"
            stats = data.get("stats")
            if stats:
                self.stats["savings"] = stats.savings_percent
                self.stats["duration"] = stats.duration_seconds
                
        elif event_type == "error":
            msg = data.get("message", "Error")
            self._append_log("claude", f"[ERROR] {msg}")
            self._append_log("gemini", f"[ERROR] {msg}")

        self.update_render()

    def _append_log(self, agent: str, message: str):
        if agent in self.buffers:
            self.buffers[agent].append(message)
        # Also sync mock buffers
        if f"mock_{agent}" in self.buffers:
             self.buffers[f"mock_{agent}"].append(message)

    def _append_text(self, agent: str, text: str):
        if agent not in self.buffers:
            return
            
        # Handle newlines for cleaner buffer
        lines = text.split('\n')
        if not lines:
            return
            
        # Append to last line if it exists
        if self.buffers[agent]:
            self.buffers[agent][-1] += lines[0]
        else:
            self.buffers[agent].append(lines[0])
            
        # Append remaining lines
        if len(lines) > 1:
            self.buffers[agent].extend(lines[1:])
