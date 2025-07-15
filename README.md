# Claude Code Botman
```
██████╗  ██████╗ ████████╗███╗   ███╗ █████╗ ███╗   ██╗
██╔══██╗██╔═══██╗╚══██╔══╝████╗ ████║██╔══██╗████╗  ██║
██████╔╝██║   ██║   ██║   ██╔████╔██║███████║██╔██╗ ██║
██╔══██╗██║   ██║   ██║   ██║╚██╔╝██║██╔══██║██║╚██╗██║
██████╔╝╚██████╔╝   ██║   ██║ ╚═╝ ██║██║  ██║██║ ╚████║
╚═════╝  ╚═════╝    ╚═╝   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
``` 
A Python wrapper for Claude Code CLI that enables programmatic interaction with Claude's coding assistant.

## Installation

```bash
pip install claude-code-botman
```

## Quick Start

```python
from claude_code_botman import ClaudeCode

claude = ClaudeCode(model="claude-sonnet-4-20250514")
result = claude("Create a hello world Python script")
print(result)
```

## Features

- Complete CLI support with all arguments
- Permission management and security controls
- Session management and continuation
- Multiple output formats (text, JSON, stream-JSON)
- Environment configuration