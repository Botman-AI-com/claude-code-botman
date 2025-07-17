# claude-code-botman

A Python wrapper library for the Claude Code CLI that enables programmatic interaction with Claude's coding assistant.

## Overview

claude-code-botman provides a simple Python interface to execute Claude Code commands from your scripts with full subprocess management, configuration handling, and response parsing.

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from claude_code_botman import ClaudeCode

# Basic usage
claude = ClaudeCode()
response = claude("Write a hello world function in Python")

# With configuration
claude = ClaudeCode(model="sonnet", timeout=60)
response = claude("Refactor this code for better performance")

# With rules from CLAUDE.md
claude = ClaudeCode(rules="./CLAUDE.md")
response = claude("Follow the project guidelines and add tests")
```

## Features

- **Simple API**: Single method call to execute Claude Code commands
- **Configuration Management**: Flexible config system with environment variable support
- **Response Parsing**: Structured parsing of Claude's responses including file changes and errors
- **Session Management**: Support for conversation continuity
- **Batch Operations**: Process multiple commands efficiently
- **Error Handling**: Comprehensive exception handling with specific error types

## Requirements

- Python 3.7+
- Claude Code CLI installed and configured

## Development

```bash
# Run tests
pytest

# Format code
black claude_code_botman/ tests/ examples/

# Type checking
mypy claude_code_botman/
```

## License

MIT