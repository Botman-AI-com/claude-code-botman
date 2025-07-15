"""
claude-code-botman: A Python wrapper for Claude Code CLI

This package provides a convenient Python interface for interacting with
Claude Code CLI through subprocess calls, enabling programmatic access to
Claude's coding assistant capabilities.
"""

__version__ = "0.1.0"
__author__ = "Octavio Pavon"
__email__ = "octavio.pavon@botman-ai.com"
__license__ = "MIT"

from .core import ClaudeCode, ClaudeCodeContext, ClaudeCodeBatch
from .config import ClaudeConfig, load_config_from_env
from .exceptions import (
    ClaudeCodeError,
    ClaudeCodeNotFoundError,
    ClaudeCodeTimeoutError,
    ClaudeCodeAuthenticationError,
    ClaudeCodeExecutionError,
)
from .utils import ClaudeResponse

__all__ = [
    "ClaudeCode",
    "ClaudeCodeContext",
    "ClaudeCodeBatch",
    "ClaudeConfig",
    "load_config_from_env",
    "ClaudeResponse",
    "ClaudeCodeError",
    "ClaudeCodeNotFoundError",
    "ClaudeCodeTimeoutError",
    "ClaudeCodeAuthenticationError",
    "ClaudeCodeExecutionError",
] 