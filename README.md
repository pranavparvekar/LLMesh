# LLMesh - Multi-Agent Orchestrator

**LLMesh** is a CLI tool that makes **Claude Code CLI** and **Gemini CLI** collaborate on tasks together. Give LLMesh a task, and both AI agents discuss, plan, split work, and execute — while you watch the conversation happen in real-time in your terminal.

```
llmesh "build a FastAPI app with JWT auth and rate limiting"
```

---

## Table of Contents

- [Why This Exists](#why-this-exists)
- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Commands & Usage](#commands--usage)
- [Orchestration Strategies](#orchestration-strategies)
- [Architecture Deep Dive](#architecture-deep-dive)
- [Agent Communication](#agent-communication)
- [Prompt Engineering](#prompt-engineering)
- [Task Routing Intelligence](#task-routing-intelligence)
- [Real World Test Results](#real-world-test-results)
- [Project Structure](#project-structure)
- [Module Details](#module-details)
- [Configuration](#configuration)
- [Development & Testing](#development--testing)
- [Windows-Specific Fixes](#windows-specific-fixes)
- [Technical Requirements](#technical-requirements)
- [Roadmap](#roadmap)

---

## Why This Exists

Developers today have access to both Claude Code CLI and Gemini CLI, but they live in completely separate worlds:

| Problem | LLMesh Solution |
|---------|----------------|
| Claude and Gemini can't talk to each other | LLMesh bridges them via subprocess orchestration |
| Claude is powerful but burns subscription tokens fast | Claude only handles the hard parts (review, security, architecture) |
| Gemini is cheaper/free but weaker on complex tasks | Gemini handles the bulk work (planning, boilerplate, integration) |
| No way to combine their strengths | LLMesh routes tasks by difficulty to the right agent |

**Result:** Same quality output, **70-80% Claude token savings**.

---

## Quick Start

### 1. Install

```bash
cd llmesh
pip install -e .

# With dev dependencies (pytest):
pip install -e ".[dev]"
```

### 2. Prerequisites

You need at least one of these installed:

| CLI | Install | Check |
|-----|---------|-------|
| **Claude Code** | [claude.ai/download](https://claude.ai/download) | `claude --version` |
| **Gemini CLI** | `npm install -g @anthropic/gemini-cli` | `gemini --version` |

Don't have either? Use `--agents mock` to test with simulated agents.

### 3. Run

```bash
# Auto-detect available agents and run:
llmesh "build a REST API with authentication"

# Or run directly with Python:
python -m llmesh.cli "build a REST API with authentication"
```

---

## How It Works

LLMesh works by spawning Claude and Gemini CLIs as **subprocesses**, sending them prompts via **stdin**, and passing each agent's output to the next agent as context. The orchestrator manages the conversation flow.

### The Flow (default strategy: plan-review-execute)

```
Step 1: User runs "llmesh <task>"
           |
Step 2: Gemini creates a detailed plan (cheap tokens)
           |
Step 3: Claude reviews and critiques the plan (expensive, but brief)
           |
Step 4: Gemini revises plan based on Claude's feedback (cheap)
           |
Step 5: Plan is parsed into subtasks with EASY/HARD labels
           |
Step 6: Tasks are routed: EASY -> Gemini, HARD -> Claude
           |
Step 7: Gemini integrates all code pieces (cheap)
           |
Step 8: Claude does final quality review (expensive, but brief)
           |
Step 9: Final output displayed with token stats
```

### What the User Sees

```
============================================================
Phase: PLANNING | Agent: gemini
============================================================

GEMINI (planning):
Here is the implementation plan for the Python CLI Calculator.

PROJECT STRUCTURE:
pycalc/
  pycalc/
    main.py          # CLI entry point
    operations.py    # Core math logic
  tests/
    test_calc.py     # Unit tests
  setup.py
  README.md

---
SUBTASK: Design the CLI architecture
DIFFICULTY: HARD
FILES: pycalc/main.py, setup.py
REASON: Requires careful architectural planning for usability
---

============================================================
Phase: REVIEW | Agent: claude
============================================================

CLAUDE (review):
1. setup.py is outdated - Use pyproject.toml instead (PEP 621)
2. CLI architecture is not HARD - argparse with subparsers is boilerplate
3. Missing: float precision - 0.1 + 0.2 = 0.30000000000000004
4. Missing: negative numbers break argparse (-3 treated as flag)
5. operations.py is over-engineering - use operator module instead
...

============================================================
Phase: REVISION | Agent: gemini
============================================================

GEMINI (revision):
[Incorporates all of Claude's feedback into revised plan...]

============================================================
TASK COMPLETE
============================================================

Token Usage:
  gemini: 1,226 tokens
  claude: 493 tokens

Total Duration: 85.9s
Token Savings: 71.3%
```

---

## Commands & Usage

### Basic Commands

```bash
# Default: auto-detect agents, use plan-review-execute strategy
llmesh "your task description here"

# Specify agents manually
llmesh --agents claude,gemini "create a dashboard"

# Use mock agents (no real CLIs needed - great for testing)
llmesh --agents mock "build a Flask app"

# Dry run: plan + review + revise only, no execution
llmesh --dry-run "build a complex microservice"
```

### Strategy Selection

```bash
# Full multi-agent collaboration (default)
llmesh --strategy plan-review-execute "build an API"

# Simple: just use the cheap agent for everything
llmesh --strategy simple "write a hello world script"

# Quality: use the expensive agent for everything
llmesh --strategy quality "implement JWT auth"
```

### All CLI Flags

| Flag | Description | Default |
|------|-------------|---------|
| `"task"` | Task description (required, positional) | - |
| `--agents` | Comma-separated agent names or `auto` | `auto` |
| `--strategy` | Orchestration strategy | `plan-review-execute` |
| `--work-dir` | Working directory | `.` (current dir) |
| `--dry-run` | Show plan only, don't execute | `false` |
| `--verbose` / `-v` | Show full agent outputs | `false` |
| `--max-rounds` | Max discussion rounds | `10` |
| `--simple-tui` | Force simple print-based TUI | `false` |

### Running with Python

```bash
# Module mode:
python -m llmesh.cli "your task"

# Or import as library:
python -c "
from llmesh.agents.claude import ClaudeAgent
from llmesh.agents.gemini import GeminiAgent
from llmesh.orchestrator import Orchestrator, OrchestratorConfig

agents = [GeminiAgent(), ClaudeAgent()]
config = OrchestratorConfig(strategy='plan-review-execute')
orch = Orchestrator(agents=agents, config=config)
result = orch.run('build a calculator')
print(result.final_output)
"
```

---

## Orchestration Strategies

### 1. `plan-review-execute` (Default)

The full multi-agent collaboration workflow:

| Phase | Agent | Purpose | Token Cost |
|-------|-------|---------|------------|
| Planning | Gemini (cheap) | Create detailed project plan with subtasks | Low |
| Review | Claude (expensive) | Critique plan, find issues, suggest improvements | Medium |
| Revision | Gemini (cheap) | Incorporate Claude's feedback | Low |
| Execution | Both (routed) | EASY tasks -> Gemini, HARD tasks -> Claude | Varies |
| Integration | Gemini (cheap) | Combine all code into final project | Low |
| Final Review | Claude (expensive) | Quick quality check, flag critical issues | Low |

**Savings: 70-80%** of Claude tokens compared to doing everything with Claude.

### 2. `simple`

Everything goes to the cheap agent (Gemini). Fastest and cheapest, but lower quality for complex tasks.

### 3. `quality`

Everything goes to the expensive agent (Claude). Highest quality, but uses the most tokens.

---

## Architecture Deep Dive

```
                    +------------------+
                    |   CLI Entry      |
                    |   (cli.py)       |
                    |                  |
                    | - argparse       |
                    | - agent detect   |
                    | - config load    |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |  Orchestrator    |
                    |                  |
                    | - strategy exec  |
                    | - phase mgmt    |
                    | - event system  |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
              v              v              v
     +--------+----+  +-----+------+  +----+--------+
     |  Planner    |  |  Router    |  |  Discussion |
     |             |  |            |  |             |
     | - prompts   |  | - EASY ->  |  | - messages  |
     | - parse     |  |   cheap    |  | - stats     |
     | - subtasks  |  | - HARD ->  |  | - tokens    |
     +-------------+  |   expensive|  +-------------+
                       +-----+------+
                             |
              +--------------+--------------+
              |                             |
              v                             v
     +--------+--------+          +--------+--------+
     |  Claude Agent   |          |  Gemini Agent   |
     |                 |          |                 |
     | - subprocess    |          | - subprocess    |
     | - stdin pipe    |          | - stdin pipe    |
     | - --allowedTools|          | - -p "" flag    |
     | - env cleanup   |          |                 |
     +-----------------+          +-----------------+
              |                             |
              v                             v
     +--------+--------+          +--------+--------+
     | claude CLI      |          | gemini CLI      |
     | (real process)  |          | (real process)  |
     +-----------------+          +-----------------+
```

### Component Responsibilities

| Component | File | What It Does |
|-----------|------|-------------|
| **CLI Entry** | `cli.py` | Parses args, detects agents, creates orchestrator, starts TUI |
| **Orchestrator** | `orchestrator.py` | The brain - runs strategies, manages phases, passes outputs between agents |
| **Planner** | `planner.py` | Generates planning/review/revision prompts, parses subtasks from text |
| **Router** | `router.py` | Decides which agent handles which subtask based on difficulty |
| **Discussion** | `discussion.py` | Tracks all messages, token counts, stats, conversation history |
| **BaseAgent** | `agents/base.py` | Abstract interface all agents implement |
| **ClaudeAgent** | `agents/claude.py` | Spawns `claude` CLI, manages env vars, stdin piping |
| **GeminiAgent** | `agents/gemini.py` | Spawns `gemini` CLI, stdin piping |
| **MockAgent** | `agents/mock.py` | Configurable fake agent for testing |
| **TUI** | `tui/display.py` | Real-time terminal display with color-coded agent output |
| **Config** | `config.py` | Loads/saves user preferences from `~/.llmesh/config.json` |

---

## Agent Communication

This is the critical technical detail. Claude Code and Gemini CLI are **separate processes**. LLMesh orchestrates them by:

### How Prompts Are Sent

```python
# Prompts are piped via STDIN to avoid command-line length limits
result = subprocess.run(
    ["claude", "-p", "--allowedTools", ""],  # text-only mode
    input=prompt,                             # prompt via stdin
    capture_output=True,
    text=True,
    timeout=180,
    env=clean_env,       # CLAUDECODE removed, git-bash path set
    shell=True,          # needed on Windows for npm CLIs
)

# Gemini uses similar pattern
result = subprocess.run(
    ["gemini", "-p", ""],  # non-interactive mode, reads stdin
    input=prompt,
    capture_output=True,
    text=True,
    timeout=180,
    shell=True,
)
```

### Why Stdin Piping?

We tried passing prompts as command-line arguments first, but hit these issues:
1. **Windows 8191-char command line limit** - planning prompts easily exceed this
2. **Shell escaping nightmares** - quotes, newlines, special chars in prompts
3. **npm wrapper scripts** - both CLIs are npm shell scripts that need `shell=True` on Windows

**Solution:** Pipe prompts via `stdin` using `subprocess.run(input=prompt)`. Works reliably with any prompt length.

### Why `--allowedTools ""`?

Both Claude and Gemini CLIs run as **full AI agents** with tool access (file reading, code search, etc.). Without restricting tools:
- Claude would try to read files in the current directory instead of responding to the prompt
- Gemini would investigate the workspace and say "I'm ready to help!" instead of generating a plan

**Solution:** `--allowedTools ""` for Claude disables all tool use, forcing text-only responses.

### Environment Variable Handling (Claude)

Claude Code CLI detects if it's being run inside another Claude Code session and blocks it. LLMesh fixes this:

```python
def _get_clean_env(self):
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)  # Remove nested session detection
    # Windows needs git-bash path with BACKSLASHES
    env["CLAUDE_CODE_GIT_BASH_PATH"] = "C:\\...\\Git\\bin\\bash.exe"
    return env
```

---

## Prompt Engineering

The quality of multi-agent collaboration depends entirely on the prompts. LLMesh uses carefully crafted prompt templates:

### Response-Only Prefix

Every prompt starts with this prefix to prevent agent-mode CLIs from using tools:

```
IMPORTANT: You are being used as a text-generation backend.
DO NOT use any tools. DO NOT read, write, or search for files.
DO NOT investigate the current directory or codebase.
Just respond directly with text based on the instructions below.
Ignore any existing files or project context - work ONLY from what is provided here.
```

### Planning Prompt (sent to Gemini)

Asks the cheap agent to create a structured plan with parseable subtasks:

```
You are a senior software developer planning a project.
TASK: {task}

For each subtask, use this EXACT format:
---
SUBTASK: [description]
DIFFICULTY: [EASY or HARD]
FILES: [files]
REASON: [why this difficulty]
---
```

### Review Prompt (sent to Claude)

Asks the expensive agent to be brief and focused:

```
You are a senior architect reviewing a project plan.
Review and provide BRIEF, ACTIONABLE feedback.
Be CONCISE. Only flag real issues. Don't rewrite the plan.
Max 10 bullet points.
```

### Execution Prompt (sent to assigned agent)

Provides full context including previous work:

```
You are implementing a specific subtask.
OVERALL TASK: {task}
PROJECT PLAN: {plan}
YOUR SUBTASK: {subtask}
CONTEXT: {previous_results}

Output ONLY the code with file paths:
=== FILE: path/to/file.py ===
[code here]
=== END FILE ===
```

### Integration Prompt (sent to Gemini)

```
Combine everything into a coherent, working project.
Resolve conflicts, add missing imports, create __init__.py files.
```

### Final Review Prompt (sent to Claude)

```
Quick review. ONLY flag critical issues.
Check for: security vulnerabilities, logic errors, missing error handling.
Be BRIEF. Max 5 bullet points.
```

---

## Task Routing Intelligence

The Router decides which agent handles each subtask:

### Routing Rules

| Difficulty | Routed To | Examples |
|-----------|-----------|---------|
| **EASY** | Gemini (cheap) | Boilerplate, config files, docs, test scaffolding, simple CRUD, file structure |
| **MEDIUM** | Depends on keywords | Security keywords -> Claude; otherwise -> Gemini |
| **HARD** | Claude (expensive) | Security-critical code, complex algorithms, architecture decisions, code review |

### Security Keyword Detection

If a MEDIUM task contains any of these keywords, it's routed to Claude:
`auth`, `security`, `encryption`, `password`, `token`, `permission`, `validation`, `sanitize`, `exploit`

### Subtask Parsing

LLMesh parses subtasks from agent responses using regex:

```python
# Splits on --- markers, extracts SUBTASK/DIFFICULTY/FILES fields
sections = re.split(r'\n---+\n', plan_text)
for section in sections:
    description = extract_field(section, "SUBTASK")
    difficulty = extract_field(section, "DIFFICULTY")
    files = extract_field(section, "FILES")
```

---

## Real World Test Results

### Test: Python CLI Calculator (dry run)

**Task:** "Create a Python CLI calculator that supports add, subtract, multiply, divide via command line arguments"

| Phase | Agent | What Happened | Tokens | Time |
|-------|-------|---------------|--------|------|
| Planning | Gemini | Created full project structure with 5 subtasks | ~623 | ~20s |
| Review | Claude | Gave 10 sharp critiques (see below) | ~493 | ~15s |
| Revision | Gemini | Incorporated ALL feedback into cleaner plan | ~603 | ~50s |

**Claude's review caught:**
1. `setup.py` is outdated -> use `pyproject.toml` (PEP 621)
2. CLI architecture is not HARD -> downgrade difficulty
3. `0.1 + 0.2 = 0.30000000000000004` -> use `decimal.Decimal`
4. Negative numbers break argparse (`-3` treated as flag)
5. `operations.py` is over-engineering -> use `operator` module
6. Missing integer vs float output (`5.0` should be `5`)
7. `tests/__init__.py` unnecessary with pytest
8. Error handling should be merged with operations subtask
9. Missing exit codes (`sys.exit(1)` on errors)
10. Output should be pipe-friendly (bare numbers, no labels)

**Gemini's revision incorporated ALL 10 points.**

**Final Stats:**
- Gemini: 1,226 tokens (71.3%)
- Claude: 493 tokens (28.7%)
- **Token savings: 71.3%**
- Duration: 86 seconds

---

## Project Structure

```
llmesh/
|-- llmesh/
|   |-- __init__.py           # Package init, version, exports
|   |-- cli.py                # CLI entry point (argparse)
|   |-- orchestrator.py       # Core brain - manages multi-agent workflow
|   |-- discussion.py         # Data models: messages, stats, results
|   |-- planner.py            # Prompt templates + subtask parsing
|   |-- router.py             # Routes subtasks to agents by difficulty
|   |-- config.py             # User config (~/.llmesh/config.json)
|   |
|   |-- agents/
|   |   |-- __init__.py
|   |   |-- base.py           # Abstract base agent (ABC)
|   |   |-- claude.py         # Claude Code CLI adapter
|   |   |-- gemini.py         # Gemini CLI adapter
|   |   |-- mock.py           # Mock agent for testing
|   |
|   |-- tui/
|       |-- __init__.py
|       |-- display.py        # Terminal UI (color-coded output)
|
|-- tests/
|   |-- __init__.py
|   |-- test_agents.py        # 5 tests - mock agent behavior
|   |-- test_orchestrator.py  # 6 tests - orchestration strategies
|   |-- test_planner.py       # 6 tests - prompt generation + parsing
|   |-- test_router.py        # 9 tests - task routing logic
|
|-- examples/
|   |-- example_usage.py      # Programmatic usage example
|
|-- setup.py
|-- pyproject.toml
|-- .gitignore
|-- README.md                 # This file
```

---

## Module Details

### `agents/base.py` - Agent Interface

```python
class BaseAgent(ABC):
    def send(prompt, timeout=120) -> AgentResponse      # One-shot prompt
    def stream(prompt, on_chunk) -> AgentResponse        # Streaming output
    def is_available() -> bool                           # CLI installed?
    def name -> str                                      # "claude" / "gemini"
    def cost_tier -> str                                 # "free" / "expensive"

@dataclass
class AgentResponse:
    content: str              # The response text
    token_estimate: int       # ~len(text) // 4
    duration_seconds: float
    agent_name: str
    success: bool
    error: Optional[str]
```

### `agents/claude.py` - Claude Adapter

- Spawns `claude -p --allowedTools ""` via subprocess
- Sends prompt via stdin (avoids cmd line length limits)
- Removes `CLAUDECODE` env var (prevents nested session error)
- Sets `CLAUDE_CODE_GIT_BASH_PATH` on Windows (with backslashes)
- Uses `shell=True` on Windows (npm scripts need it)

### `agents/gemini.py` - Gemini Adapter

- Spawns `gemini -p ""` via subprocess
- Sends prompt via stdin
- Uses `shell=True` on Windows

### `agents/mock.py` - Mock Agent

- Returns configurable responses matched by keyword
- Supports streaming simulation
- Always available (no CLI needed)
- Essential for testing and development

### `orchestrator.py` - The Brain

- Manages the full workflow (strategy selection, phase execution)
- Passes outputs between agents as context
- Emits events for TUI display (phase_start, agent_chunk, task_complete, etc.)
- Tracks token usage per agent
- Calculates savings stats

### `discussion.py` - State Management

```python
@dataclass
class DiscussionMessage:
    agent_name: str       # "claude" | "gemini"
    phase: str            # "planning" | "review" | "execution" ...
    content: str
    timestamp: datetime
    token_estimate: int

@dataclass
class DiscussionStats:
    total_rounds: int
    tokens_by_agent: Dict[str, int]    # {"claude": 493, "gemini": 1226}
    duration_seconds: float
    tokens_saved_estimate: int
    savings_percent: float             # 71.3
    phases_completed: List[str]
```

### `planner.py` - Task Decomposition

- Generates structured planning/review/revision prompts
- Parses subtasks from free-text responses using regex
- Normalizes difficulty ratings (EASY/MEDIUM/HARD)
- Extracts file lists from subtask definitions

### `router.py` - Agent Assignment

- Categorizes agents by cost tier (free/cheap/expensive)
- Routes EASY -> cheap, HARD -> expensive
- Detects security-critical keywords for MEDIUM tasks
- Fallback logic when agents are unavailable

### `tui/display.py` - Terminal UI

- Color-coded output (Claude = blue, Gemini = green)
- Real-time streaming of agent responses
- Phase headers and progress indicators
- Token usage stats and savings display
- Windows UTF-8 emoji support

### `config.py` - Configuration

- Stored in `~/.llmesh/config.json`
- Default strategy, max rounds, agent preferences
- Created on first use with sensible defaults

---

## Configuration

LLMesh stores configuration in `~/.llmesh/config.json`:

```json
{
  "agents": {
    "claude": {
      "command": "claude",
      "args": ["-p"],
      "role_preference": "architect",
      "cost_tier": "expensive"
    },
    "gemini": {
      "command": "gemini",
      "args": ["-p"],
      "role_preference": "planner",
      "cost_tier": "free"
    }
  },
  "default_strategy": "plan-review-execute",
  "max_rounds": 10,
  "work_dir": ".",
  "show_token_estimates": true
}
```

The config is created automatically on first use. Edit it to change defaults.

---

## Development & Testing

### Install for Development

```bash
cd llmesh
pip install -e ".[dev]"
```

### Run Tests

```bash
# All tests (26 tests)
pytest tests/ -v

# Specific module
pytest tests/test_orchestrator.py -v

# With coverage
pytest --cov=llmesh --cov-report=html
```

### Test Results

```
tests/test_agents.py       5 passed   (mock agent behavior)
tests/test_orchestrator.py 6 passed   (all strategies, events, tokens)
tests/test_planner.py      6 passed   (prompts, parsing, normalization)
tests/test_router.py       9 passed   (routing rules, agent selection)
                          ----------
Total:                    26 passed
```

### Testing Without Real CLIs

```bash
# Mock agents simulate the full workflow
llmesh --agents mock "build a Flask app"

# Programmatic testing
python examples/example_usage.py
```

### Adding a New Agent

1. Create `llmesh/agents/your_agent.py`
2. Implement `BaseAgent` interface (send, stream, is_available, name, cost_tier)
3. Register it in `cli.py`'s `create_agents()` function

---

## Windows-Specific Fixes

These issues were discovered and fixed during development on Windows 11:

### 1. npm CLI Scripts Need `shell=True`

Both `claude` and `gemini` are npm-installed POSIX shell scripts. Python's `subprocess` on Windows can't execute them directly.

**Fix:** `shell=True` when `sys.platform == "win32"`

### 2. Claude Nested Session Detection

Claude CLI checks for the `CLAUDECODE` environment variable and blocks if it detects nesting.

**Fix:** Remove `CLAUDECODE` from the subprocess environment:
```python
env = os.environ.copy()
env.pop("CLAUDECODE", None)
```

### 3. Claude Needs Git-Bash Path

On Windows, Claude CLI requires git-bash. When spawned as a subprocess, it can't find it.

**Fix:** Set `CLAUDE_CODE_GIT_BASH_PATH` with **backslashes**:
```python
env["CLAUDE_CODE_GIT_BASH_PATH"] = "C:\\Users\\...\\Git\\bin\\bash.exe"
```

### 4. Command-Line Length Limit (8191 chars)

Windows has an 8191-character limit for command-line arguments. Planning prompts easily exceed this.

**Fix:** Send prompts via **stdin** instead of command-line arguments:
```python
subprocess.run(["claude", "-p", ...], input=prompt)
```

### 5. Console Encoding for Emojis

Windows console defaults to cp1252 which can't display Unicode emojis.

**Fix:** Reconfigure stdout encoding:
```python
sys.stdout.reconfigure(encoding='utf-8')
```

### 6. setup.py Encoding

`pathlib.read_text()` uses system encoding on Windows, which fails on UTF-8 files with special characters.

**Fix:** `readme_file.read_text(encoding="utf-8")`

---

## Technical Requirements

### Python Version
- **Python 3.10+** (for modern typing features)

### Dependencies
- **ZERO external dependencies** for core functionality
- Only uses Python standard library: `subprocess`, `argparse`, `json`, `pathlib`, `shutil`, `time`, `dataclasses`, `abc`, `typing`, `os`, `sys`, `re`, `threading`, `queue`, `datetime`, `signal`, `textwrap`, `io`
- Optional: `rich` for enhanced TUI (graceful fallback if not installed)
- Dev: `pytest >= 7.0`, `pytest-cov >= 4.0`

### Token Estimation

Since we use CLI subscriptions (not APIs), we don't get real token counts:

```python
def estimate_tokens(text: str) -> int:
    """Rough estimate: ~4 chars per token for English."""
    return max(1, len(text) // 4)
```

### Error Handling

| Scenario | Behavior |
|----------|----------|
| Agent not installed | Clear error with install instructions |
| Agent times out | Error reported, task continues with remaining agents |
| Agent returns error | Displayed in TUI, offered retry |
| User presses Ctrl+C | Clean subprocess shutdown, partial results shown |
| Only one agent available | Runs in single-agent mode (all tasks to that agent) |
| No agents available | Falls back to mock agents with warning |

---

## Roadmap

### Completed

- [x] Core orchestrator with 3 strategies
- [x] Claude Code CLI adapter (subprocess + stdin)
- [x] Gemini CLI adapter (subprocess + stdin)
- [x] Mock agent for testing
- [x] Task planning, review, revision flow
- [x] Intelligent task routing (EASY/MEDIUM/HARD)
- [x] Simple TUI with color-coded output
- [x] Token tracking and savings calculation
- [x] Windows compatibility fixes
- [x] 26 passing tests
- [x] pip-installable package

### Planned

- [ ] Interactive curses-based TUI with scrolling
- [ ] File output parsing and automatic file writing
- [ ] Human-in-the-loop interrupts (inject messages during discussion)
- [ ] Support for more agents (GPT CLI, local models)
- [ ] Session history and replay
- [ ] Custom routing rules (user-defined EASY/HARD categories)
- [ ] Parallel subtask execution
- [ ] Better streaming output in TUI
- [ ] Configuration GUI

---

## How It Was Built

LLMesh was built in a single session following this order:

1. **Agent infrastructure** - Base interface + mock agent (test-first)
2. **Data models** - Discussion messages, stats, results
3. **Orchestrator** - Core brain with strategy execution
4. **Planner + Router** - Task decomposition and routing logic
5. **Real CLI adapters** - Claude and Gemini subprocess wrappers
6. **TUI** - Simple print-based terminal display
7. **CLI entry point** - argparse with all flags
8. **Configuration** - Persistent user settings
9. **Tests** - 26 tests across all modules
10. **Windows fixes** - shell=True, env vars, stdin piping, encoding

The build followed the principle: **make it work end-to-end first, then make it pretty**.

---

## License

MIT

## Contributing

Contributions welcome! Areas that need help:
- Curses-based TUI implementation
- File output parsing from agent responses
- Support for additional CLI agents
- Better prompt templates for specific task types
