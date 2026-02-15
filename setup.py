"""Setup configuration for LLMesh."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="llmesh",
    version="0.1.0",
    description="Multi-Agent Orchestrator for Claude Code and Gemini CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="LLMesh Contributors",
    author_email="",
    url="https://github.com/yourusername/llmesh",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        # Zero external dependencies - uses only stdlib
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
        ],
        "rich": [
            "rich>=13.0",  # Optional: for better TUI
        ]
    },
    entry_points={
        "console_scripts": [
            "llmesh=llmesh.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="ai agents llm claude gemini orchestration multi-agent",
)
