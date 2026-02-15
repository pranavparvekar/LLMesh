"""
User configuration.

Stored in ~/.llmesh/config.json
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


DEFAULT_CONFIG = {
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
    "show_token_estimates": True
}


class Config:
    """Configuration manager for LLMesh."""

    def __init__(self):
        self.config_dir = Path.home() / ".llmesh"
        self.config_file = self.config_dir / "config.json"
        self.data = self.load()

    def load(self) -> Dict[str, Any]:
        """Load configuration from disk or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")
                return DEFAULT_CONFIG.copy()
        else:
            return DEFAULT_CONFIG.copy()

    def save(self):
        """Save configuration to disk."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def get(self, key: str, default=None):
        """Get a configuration value."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        """Set a configuration value."""
        self.data[key] = value
        self.save()

    @property
    def default_strategy(self) -> str:
        return self.data.get("default_strategy", "plan-review-execute")

    @property
    def max_rounds(self) -> int:
        return self.data.get("max_rounds", 10)

    @property
    def work_dir(self) -> str:
        return self.data.get("work_dir", ".")
