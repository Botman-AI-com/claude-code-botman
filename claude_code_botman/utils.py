"""
Utility functions for claude-code-botman package.

This module provides utility functions for CLI validation, output parsing,
path handling, and other common operations.
"""

import subprocess
import shutil
import json
import re
import os
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from .exceptions import (
    ClaudeCodeNotFoundError,
    ClaudeCodePathError,
    ClaudeCodeResponseError,
    ClaudeCodeModelError,
)


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ClaudeResponse:
    """
    Structured response from Claude Code CLI.
    
    This class parses and structures the output from Claude Code CLI,
    providing convenient access to different parts of the response.
    """
    
    raw_output: str
    exit_code: int = 0
    stderr: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        """Initialize response parsing."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        
        self.parsed_content = self._parse_output()
    
    def _parse_output(self) -> Dict[str, Any]:
        """Parse raw output into structured format."""
        try:
            # Try to parse as JSON first (for --output-format json)
            if self.raw_output.strip().startswith('{'):
                return json.loads(self.raw_output)
        except json.JSONDecodeError:
            pass
        
        # Parse text output
        content = {
            "text": self.raw_output,
            "files_created": self._extract_files_created(),
            "files_modified": self._extract_files_modified(),
            "commands_executed": self._extract_commands_executed(),
            "errors": self._extract_errors(),
            "warnings": self._extract_warnings(),
            "session_id": self._extract_session_id(),
        }
        
        return content
    
    def _extract_files_created(self) -> List[str]:
        """Extract list of files created from output."""
        files = []
        
        # Look for patterns like "Created file: filename" or "Creating filename"
        patterns = [
            r"Created?\s+(?:file\s+)?[:\-]?\s*([^\s\n]+)",
            r"Creating\s+([^\s\n]+)",
            r"Writing\s+to\s+([^\s\n]+)",
            r"Saved\s+to\s+([^\s\n]+)",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.raw_output, re.IGNORECASE)
            files.extend(matches)
        
        return list(set(files))  # Remove duplicates
    
    def _extract_files_modified(self) -> List[str]:
        """Extract list of files modified from output."""
        files = []
        
        patterns = [
            r"Modified\s+(?:file\s+)?[:\-]?\s*([^\s\n]+)",
            r"Updated\s+([^\s\n]+)",
            r"Editing\s+([^\s\n]+)",
            r"Changed\s+([^\s\n]+)",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.raw_output, re.IGNORECASE)
            files.extend(matches)
        
        return list(set(files))
    
    def _extract_commands_executed(self) -> List[str]:
        """Extract list of commands executed from output."""
        commands = []
        
        patterns = [
            r"Executing:\s*([^\n]+)",
            r"Running:\s*([^\n]+)",
            r"Command:\s*([^\n]+)",
            r"\$\s*([^\n]+)",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.raw_output, re.IGNORECASE)
            commands.extend(matches)
        
        return commands
    
    def _extract_errors(self) -> List[str]:
        """Extract error messages from output."""
        errors = []
        
        patterns = [
            r"Error:\s*([^\n]+)",
            r"ERROR:\s*([^\n]+)",
            r"Failed:\s*([^\n]+)",
            r"Exception:\s*([^\n]+)",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.raw_output, re.IGNORECASE)
            errors.extend(matches)
        
        return errors
    
    def _extract_warnings(self) -> List[str]:
        """Extract warning messages from output."""
        warnings = []
        
        patterns = [
            r"Warning:\s*([^\n]+)",
            r"WARN:\s*([^\n]+)",
            r"Caution:\s*([^\n]+)",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.raw_output, re.IGNORECASE)
            warnings.extend(matches)
        
        return warnings
    
    def _extract_session_id(self) -> Optional[str]:
        """Extract session ID from output."""
        patterns = [
            r"Session\s+ID:\s*([^\s\n]+)",
            r"Session:\s*([^\s\n]+)",
            r"ID:\s*([a-zA-Z0-9\-]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.raw_output, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @property
    def text(self) -> str:
        """Get text content of the response."""
        return self.parsed_content.get("text", self.raw_output)
    
    @property
    def files_created(self) -> List[str]:
        """Get list of files created."""
        return self.parsed_content.get("files_created", [])
    
    @property
    def files_modified(self) -> List[str]:
        """Get list of files modified."""
        return self.parsed_content.get("files_modified", [])
    
    @property
    def commands_executed(self) -> List[str]:
        """Get list of commands executed."""
        return self.parsed_content.get("commands_executed", [])
    
    @property
    def errors(self) -> List[str]:
        """Get list of errors."""
        return self.parsed_content.get("errors", [])
    
    @property
    def warnings(self) -> List[str]:
        """Get list of warnings."""
        return self.parsed_content.get("warnings", [])
    
    @property
    def session_id(self) -> Optional[str]:
        """Get session ID."""
        return self.parsed_content.get("session_id")
    
    @property
    def has_errors(self) -> bool:
        """Check if response contains errors."""
        return len(self.errors) > 0 or self.exit_code != 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if response contains warnings."""
        return len(self.warnings) > 0
    
    @property
    def success(self) -> bool:
        """Check if operation was successful."""
        return self.exit_code == 0 and not self.has_errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "raw_output": self.raw_output,
            "exit_code": self.exit_code,
            "stderr": self.stderr,
            "timestamp": self.timestamp.isoformat(),
            "parsed_content": self.parsed_content,
            "success": self.success,
        }
    
    def __str__(self) -> str:
        """String representation of the response."""
        return self.text
    
    def __repr__(self) -> str:
        """Detailed representation of the response."""
        return f"ClaudeResponse(success={self.success}, files_created={len(self.files_created)}, exit_code={self.exit_code})"


def check_claude_cli_installed() -> bool:
    """
    Check if Claude Code CLI is installed and accessible.
    
    Returns:
        bool: True if Claude CLI is available, False otherwise
    """
    return shutil.which("claude") is not None


def get_claude_cli_version() -> Optional[str]:
    """
    Get the version of the installed Claude CLI.
    
    Returns:
        Optional[str]: Version string if available, None otherwise
    """
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Extract version from output
            version_match = re.search(r"(\d+\.\d+\.\d+)", result.stdout)
            if version_match:
                return version_match.group(1)
        
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def validate_claude_cli() -> None:
    """
    Validate that Claude CLI is properly installed and accessible.
    
    Raises:
        ClaudeCodeNotFoundError: If Claude CLI is not found or not working
    """
    if not check_claude_cli_installed():
        raise ClaudeCodeNotFoundError(
            "Claude Code CLI not found. Please install it using: npm install -g @anthropic-ai/claude-code"
        )
    
    # Try to get version to ensure it's working
    version = get_claude_cli_version()
    if version is None:
        raise ClaudeCodeNotFoundError(
            "Claude Code CLI is installed but not responding correctly. Please check your installation."
        )
    
    logger.info(f"Claude CLI version {version} detected")


def format_command_args(**kwargs) -> List[str]:
    """
    Format keyword arguments into CLI flags.
    
    Args:
        **kwargs: Keyword arguments to convert to CLI flags
        
    Returns:
        List[str]: List of CLI arguments
    """
    args = []
    
    for key, value in kwargs.items():
        # Convert underscores to hyphens for CLI flags
        flag = f"--{key.replace('_', '-')}"
        
        if isinstance(value, bool):
            if value:
                args.append(flag)
        elif isinstance(value, (list, tuple)):
            args.extend([flag] + [str(v) for v in value])
        elif value is not None:
            args.extend([flag, str(value)])
    
    return args


def validate_model_name(model: str) -> bool:
    """
    Validate Claude model name format.
    
    Args:
        model: Model name to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Import here to avoid circular imports
    from .config import SUPPORTED_MODELS, MODEL_ALIASES
    
    if model in SUPPORTED_MODELS or model in MODEL_ALIASES:
        return True
    
    # Check for partial matches
    for supported_model in SUPPORTED_MODELS:
        if model.lower() in supported_model.lower():
            return True
    
    return False


def sanitize_path(path: Union[str, Path]) -> Path:
    """
    Sanitize and validate file paths.
    
    Args:
        path: Path to sanitize
        
    Returns:
        Path: Sanitized path object
        
    Raises:
        ClaudeCodePathError: If path is invalid or unsafe
    """
    try:
        path_obj = Path(path).resolve()
        
        # Check for directory traversal attempts
        if ".." in str(path_obj):
            logger.warning(f"Potential directory traversal in path: {path}")
        
        return path_obj
    except Exception as e:
        raise ClaudeCodePathError(
            str(path),
            f"Invalid path: {e}"
        )


def ensure_directory_exists(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path: The directory path
        
    Raises:
        ClaudeCodePathError: If directory cannot be created
    """
    try:
        path_obj = sanitize_path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj
    except Exception as e:
        raise ClaudeCodePathError(
            str(path),
            f"Cannot create directory: {e}"
        )


def is_safe_path(path: Union[str, Path], base_path: Union[str, Path]) -> bool:
    """
    Check if path is safe (within base path).
    
    Args:
        path: Path to check
        base_path: Base path to check against
        
    Returns:
        bool: True if path is safe, False otherwise
    """
    try:
        path_obj = sanitize_path(path)
        base_obj = sanitize_path(base_path)
        
        # Check if path is within base path
        return base_obj in path_obj.parents or path_obj == base_obj
    except Exception:
        return False


def parse_cli_output(output: str, format_type: str = "text") -> Dict[str, Any]:
    """
    Parse Claude CLI output based on format type.
    
    Args:
        output: Raw CLI output
        format_type: Output format ("text", "json", "stream-json")
        
    Returns:
        Dict[str, Any]: Parsed output
        
    Raises:
        ClaudeCodeResponseError: If parsing fails
    """
    try:
        if format_type == "json":
            return json.loads(output)
        elif format_type == "stream-json":
            # Parse streaming JSON (one JSON object per line)
            lines = output.strip().split('\n')
            results = []
            for line in lines:
                if line.strip():
                    results.append(json.loads(line))
            return {"stream_results": results}
        else:
            # Text format - return as-is with basic parsing
            return {"text": output}
    except json.JSONDecodeError as e:
        raise ClaudeCodeResponseError(
            output,
            f"Failed to parse {format_type} output: {e}"
        )
    except Exception as e:
        raise ClaudeCodeResponseError(
            output,
            f"Unexpected error parsing output: {e}"
        )


def escape_shell_arg(arg: str) -> str:
    """
    Escape shell argument for safe subprocess execution.
    
    Args:
        arg: Argument to escape
        
    Returns:
        str: Escaped argument
    """
    # Use shlex.quote for proper shell escaping
    import shlex
    return shlex.quote(arg)


def get_system_info() -> Dict[str, Any]:
    """
    Get system information for debugging.
    
    Returns:
        Dict[str, Any]: System information
    """
    import platform
    import sys
    
    return {
        "platform": platform.platform(),
        "python_version": sys.version,
        "claude_cli_installed": check_claude_cli_installed(),
        "claude_cli_version": get_claude_cli_version(),
        "working_directory": str(Path.cwd()),
        "environment_variables": {
            key: value for key, value in os.environ.items()
            if key.startswith(("CLAUDE_", "ANTHROPIC_"))
        },
    }


def setup_logging(level: str = "INFO", format_string: Optional[str] = None) -> None:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level
        format_string: Custom format string
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[
            logging.StreamHandler(),
        ]
    )


def measure_execution_time(func):
    """
    Decorator to measure function execution time.
    
    Args:
        func: Function to measure
        
    Returns:
        Decorated function
    """
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f} seconds: {e}")
            raise
    
    return wrapper


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function on failure.
    
    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff: Backoff multiplier for delay
        
    Returns:
        Decorator function
    """
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries + 1} attempts")
            
            raise last_exception
        
        return wrapper
    return decorator 