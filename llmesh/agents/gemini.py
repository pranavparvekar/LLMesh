"""
Gemini CLI adapter.

Uses stdin piping for long prompts to avoid command-line length limits.
Gemini's -p docs: "Appended to input on stdin (if any)"
"""

import subprocess
import shutil
import time
import sys
from typing import Callable

from llmesh.agents.base import BaseAgent, AgentResponse, AgentNotFound, AgentTimeout

_IS_WINDOWS = sys.platform == "win32"


class GeminiAgent(BaseAgent):
    """Gemini CLI adapter."""

    def __init__(self):
        self.cli_command = shutil.which("gemini") or "gemini"

    def _base_cmd(self) -> list:
        """Base command. Prompt goes via stdin; -p "" enables non-interactive mode."""
        return [self.cli_command, "-p", ""]

    def send(self, prompt: str, timeout: int = 180) -> AgentResponse:
        """Send prompt via stdin, capture response."""
        start_time = time.time()

        try:
            result = subprocess.run(
                self._base_cmd(),
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=_IS_WINDOWS,
            )

            duration = time.time() - start_time

            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error"
                return AgentResponse(
                    content="",
                    token_estimate=0,
                    duration_seconds=duration,
                    agent_name=self.name,
                    success=False,
                    error=f"Gemini CLI failed: {error_msg}"
                )

            output = result.stdout.strip()
            return AgentResponse(
                content=output,
                token_estimate=self._estimate_tokens(output),
                duration_seconds=duration,
                agent_name=self.name,
                success=True,
            )

        except FileNotFoundError:
            raise AgentNotFound(f"{self.cli_command} is not installed or not in PATH")
        except subprocess.TimeoutExpired:
            raise AgentTimeout(f"{self.cli_command} timed out after {timeout}s")
        except Exception as e:
            return AgentResponse(
                content="", token_estimate=0,
                duration_seconds=time.time() - start_time,
                agent_name=self.name, success=False, error=str(e)
            )

    def stream(self, prompt: str, on_chunk: Callable[[str], None]) -> AgentResponse:
        """Send prompt via stdin, stream response line-by-line."""
        start_time = time.time()

        try:
            process = subprocess.Popen(
                self._base_cmd(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                shell=_IS_WINDOWS,
            )

            # Write prompt to stdin and close it
            process.stdin.write(prompt)
            process.stdin.close()

            full_output = []
            for line in iter(process.stdout.readline, ''):
                if line:
                    full_output.append(line)
                    on_chunk(line)

            process.wait()

            stderr = process.stderr.read()
            duration = time.time() - start_time
            output = ''.join(full_output)
            success = process.returncode == 0

            return AgentResponse(
                content=output,
                token_estimate=self._estimate_tokens(output),
                duration_seconds=duration,
                agent_name=self.name,
                success=success,
                error=stderr if not success else None
            )

        except FileNotFoundError:
            raise AgentNotFound(f"{self.cli_command} is not installed or not in PATH")
        except Exception as e:
            return AgentResponse(
                content="", token_estimate=0,
                duration_seconds=time.time() - start_time,
                agent_name=self.name, success=False, error=str(e)
            )

    def is_available(self) -> bool:
        return shutil.which(self.cli_command) is not None

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def cost_tier(self) -> str:
        return "free"

    def _estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)
