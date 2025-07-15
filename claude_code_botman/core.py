"""
Core functionality for claude-code-botman package.

This module provides the main ClaudeCode class and related functionality
for interacting with Claude Code CLI through subprocess calls.
"""

import subprocess
import asyncio
import os
import json
import logging
import threading
import time
from typing import Optional, Dict, Any, Union, List, Callable
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass, field

from .config import ClaudeConfig, get_default_config
from .utils import (
    ClaudeResponse,
    validate_claude_cli,
    sanitize_path,
    ensure_directory_exists,
    is_safe_path,
    format_command_args,
    escape_shell_arg,
    measure_execution_time,
    retry_on_failure,
)
from .exceptions import (
    ClaudeCodeError,
    ClaudeCodeNotFoundError,
    ClaudeCodeTimeoutError,
    ClaudeCodeAuthenticationError,
    ClaudeCodeExecutionError,
    ClaudeCodePathError,
    ClaudeCodeConfigurationError,
)


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class SessionInfo:
    """Information about a Claude Code session."""
    session_id: str
    path: Path
    created_at: float
    last_used: float
    model: str
    
    def is_expired(self, max_age: float = 3600) -> bool:
        """Check if session is expired."""
        return time.time() - self.last_used > max_age


class ClaudeCode:
    """
    A Python wrapper for Claude Code CLI that enables programmatic interaction
    with Claude's coding assistant through subprocess calls.
    
    This class provides a convenient interface for executing Claude Code CLI
    commands from Python, handling subprocess management, error handling,
    and response parsing.
    """
    
    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None,
        default_path: Union[str, Path] = "./",
        timeout: int = 300,
        verbose: bool = False,
        max_turns: int = 10,
        config: Optional[ClaudeConfig] = None,
        rules: Optional[Union[str, Path]] = None,
        **kwargs
    ):
        """
        Initialize ClaudeCode instance.
        
        Args:
            model: Claude model to use
            api_key: Anthropic API key (if None, uses environment variable)
            default_path: Default working directory
            timeout: Subprocess timeout in seconds
            verbose: Enable verbose logging
            max_turns: Maximum number of agentic turns
            config: Optional ClaudeConfig instance
            rules: Path to CLAUDE.md file with rules and instructions
            **kwargs: Additional configuration options
        """
        # Load rules from file if provided
        rules_content = None
        if rules is not None:
            rules_content = self._load_rules_file(rules)
        
        # Use provided config or create new one
        if config is not None:
            self.config = config
            # Apply rules to existing config if provided
            if rules_content and not self.config.append_system_prompt:
                self.config.append_system_prompt = rules_content
            elif rules_content and self.config.append_system_prompt:
                # Append rules to existing system prompt
                self.config.append_system_prompt = f"{self.config.append_system_prompt}\n\n{rules_content}"
        else:
            config_params = {
                "model": model,
                "api_key": api_key,
                "default_path": default_path,
                "timeout": timeout,
                "verbose": verbose,
                "max_turns": max_turns,
                **kwargs
            }
            # Add rules to system prompt if provided
            if rules_content:
                config_params["append_system_prompt"] = rules_content
            
            self.config = ClaudeConfig(**config_params)
        
        # Validate Claude CLI installation
        validate_claude_cli()
        
        # Session management
        self._sessions: Dict[str, SessionInfo] = {}
        self._current_session_id: Optional[str] = None
        self._session_lock = threading.Lock()
        
        # Setup logging if verbose
        if self.config.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        if rules_content and self.config.verbose:
            logger.info(f"Loaded rules from: {rules}")
        
        logger.info(f"ClaudeCode initialized with model: {self.config.model}")
    
    def __call__(
        self,
        prompt: str,
        path: Optional[Union[str, Path]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Execute Claude Code CLI with given prompt.
        
        Args:
            prompt: The prompt to send to Claude
            path: Working directory (uses default if None)
            model: Model to use (uses default if None)
            **kwargs: Additional CLI arguments
            
        Returns:
            str: Claude's response as string
            
        Raises:
            ClaudeCodeError: If execution fails
        """
        response = self._execute_claude_command(
            prompt=prompt,
            path=path,
            model=model,
            **kwargs
        )
        
        if not response.success:
            raise ClaudeCodeExecutionError(
                response.exit_code,
                response.raw_output,
                response.stderr,
                message=f"Claude execution failed: {response.errors}"
            )
        
        return response.text
    
    async def async_call(
        self,
        prompt: str,
        path: Optional[Union[str, Path]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Async version of __call__.
        
        Args:
            prompt: The prompt to send to Claude
            path: Working directory (uses default if None)
            model: Model to use (uses default if None)
            **kwargs: Additional CLI arguments
            
        Returns:
            str: Claude's response as string
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.__call__,
            prompt,
            path,
            model,
            **kwargs
        )
    
    @measure_execution_time
    @retry_on_failure(max_retries=2, delay=1.0)
    def _execute_claude_command(
        self,
        prompt: str,
        path: Optional[Union[str, Path]] = None,
        model: Optional[str] = None,
        use_print_mode: bool = True,
        continue_conversation: bool = False,
        resume_session: Optional[str] = None,
        **kwargs
    ) -> ClaudeResponse:
        """
        Execute Claude CLI command and return structured response.
        
        Args:
            prompt: The prompt to send to Claude
            path: Working directory
            model: Model to use
            use_print_mode: Whether to use print mode
            continue_conversation: Whether to continue the most recent conversation
            resume_session: Session ID to resume
            **kwargs: Additional CLI arguments
            
        Returns:
            ClaudeResponse: Structured response object
        """
        # Determine working directory
        work_path = self._resolve_path(path)
        
        # Build command
        command = self._build_command(
            prompt=prompt,
            model=model,
            use_print_mode=use_print_mode,
            continue_conversation=continue_conversation,
            resume_session=resume_session,
            **kwargs
        )
        
        # Execute command
        try:
            result = subprocess.run(
                command,
                cwd=work_path,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                env=self.config.get_environment()
            )
            
            logger.debug(f"Command executed: {' '.join(command)}")
            logger.debug(f"Exit code: {result.returncode}")
            logger.debug(f"Stdout: {result.stdout[:500]}...")
            
            if result.stderr:
                logger.debug(f"Stderr: {result.stderr}")
            
            # Create response object
            response = ClaudeResponse(
                raw_output=result.stdout,
                exit_code=result.returncode,
                stderr=result.stderr
            )
            
            # Update session info if available
            if response.session_id:
                self._update_session_info(response.session_id, work_path)
            
            return response
            
        except subprocess.TimeoutExpired:
            raise ClaudeCodeTimeoutError(
                self.config.timeout,
                f"Claude CLI command timed out after {self.config.timeout} seconds"
            )
        except FileNotFoundError:
            raise ClaudeCodeNotFoundError(
                "Claude CLI not found. Please ensure it's installed and in PATH."
            )
        except Exception as e:
            raise ClaudeCodeExecutionError(
                -1,
                "",
                str(e),
                message=f"Unexpected error executing Claude CLI: {e}"
            )
    
    def _build_command(
        self,
        prompt: str,
        model: Optional[str] = None,
        use_print_mode: bool = True,
        continue_conversation: bool = False,
        resume_session: Optional[str] = None,
        **kwargs
    ) -> List[str]:
        """
        Build Claude CLI command with arguments.
        
        Args:
            prompt: The prompt to send
            model: Model to use
            use_print_mode: Whether to use print mode
            continue_conversation: Whether to continue the most recent conversation
            resume_session: Session ID to resume
            **kwargs: Additional arguments
            
        Returns:
            List[str]: Command arguments
        """
        command = ["claude"]
        
        # Add print mode flag
        if use_print_mode:
            command.append("-p")
        
        # Add continue conversation flag
        if continue_conversation:
            command.append("--continue")
        
        # Add resume session flag
        if resume_session:
            command.extend(["--resume", resume_session])
        
        # Add model if specified
        if model:
            command.extend(["--model", model])
        elif self.config.model:
            command.extend(["--model", self.config.model])
        
        # Add configuration-based arguments
        command.extend(self.config.to_cli_args())
        
        # Add additional arguments
        if kwargs:
            command.extend(format_command_args(**kwargs))
        
        # Add prompt (escaped for safety)
        command.append(escape_shell_arg(prompt))
        
        return command
    
    def _resolve_path(self, path: Optional[Union[str, Path]]) -> Path:
        """
        Resolve working directory path.
        
        Args:
            path: Path to resolve
            
        Returns:
            Path: Resolved path
        """
        if path is None:
            return self.config.default_path
        
        resolved_path = sanitize_path(path)
        
        # Ensure path exists
        if not resolved_path.exists():
            raise ClaudeCodePathError(
                str(resolved_path),
                f"Working directory does not exist: {resolved_path}"
            )
        
        # Safety check - ensure path is safe relative to default path
        if not is_safe_path(resolved_path, self.config.default_path):
            logger.warning(f"Path {resolved_path} is outside default path {self.config.default_path}")
        
        return resolved_path
    
    def _update_session_info(self, session_id: str, path: Path):
        """Update session information."""
        with self._session_lock:
            current_time = time.time()
            
            if session_id in self._sessions:
                self._sessions[session_id].last_used = current_time
            else:
                self._sessions[session_id] = SessionInfo(
                    session_id=session_id,
                    path=path,
                    created_at=current_time,
                    last_used=current_time,
                    model=self.config.model
                )
            
            self._current_session_id = session_id
    
    def _load_rules_file(self, rules_path: Union[str, Path]) -> str:
        """
        Load rules from a CLAUDE.md file.
        
        Args:
            rules_path: Path to the rules file (usually CLAUDE.md)
            
        Returns:
            str: Content of the rules file
            
        Raises:
            ClaudeCodePathError: If the rules file doesn't exist or can't be read
        """
        try:
            rules_file = Path(rules_path).resolve()
            
            if not rules_file.exists():
                raise ClaudeCodePathError(
                    str(rules_path),
                    f"Rules file not found: {rules_file}"
                )
            
            if not rules_file.is_file():
                raise ClaudeCodePathError(
                    str(rules_path),
                    f"Rules path is not a file: {rules_file}"
                )
            
            # Read the file content
            content = rules_file.read_text(encoding='utf-8')
            
            if not content.strip():
                logger.warning(f"Rules file is empty: {rules_file}")
                return ""
            
            logger.debug(f"Loaded {len(content)} characters from rules file: {rules_file}")
            return content
            
        except Exception as e:
            if isinstance(e, ClaudeCodePathError):
                raise
            raise ClaudeCodePathError(
                str(rules_path),
                f"Error reading rules file: {e}"
            )
    
    def execute_command(
        self,
        command: str,
        path: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> subprocess.CompletedProcess:
        """
        Execute raw Claude CLI command.
        
        Args:
            command: Raw command string
            path: Working directory
            **kwargs: Additional arguments
            
        Returns:
            subprocess.CompletedProcess: Raw subprocess result
        """
        work_path = self._resolve_path(path)
        
        # Parse command string into list
        import shlex
        command_list = shlex.split(command)
        
        # Ensure first element is 'claude'
        if not command_list or command_list[0] != "claude":
            command_list.insert(0, "claude")
        
        try:
            return subprocess.run(
                command_list,
                cwd=work_path,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                env=self.config.get_environment()
            )
        except subprocess.TimeoutExpired:
            raise ClaudeCodeTimeoutError(self.config.timeout)
        except Exception as e:
            raise ClaudeCodeExecutionError(-1, "", str(e))
    
    def continue_conversation(
        self,
        prompt: str,
        path: Optional[Union[str, Path]] = None
    ) -> str:
        """
        Continue the most recent conversation.
        
        Args:
            prompt: The prompt to send
            path: Working directory
            
        Returns:
            str: Claude's response
        """
        response = self._execute_claude_command(
            prompt=prompt,
            path=path,
            continue_conversation=True
        )
        
        if not response.success:
            raise ClaudeCodeExecutionError(
                response.exit_code,
                response.raw_output,
                response.stderr
            )
        
        return response.text
    
    def resume_session(
        self,
        session_id: str,
        prompt: str,
        path: Optional[Union[str, Path]] = None
    ) -> str:
        """
        Resume a specific session by ID.
        
        Args:
            session_id: Session ID to resume
            prompt: The prompt to send
            path: Working directory
            
        Returns:
            str: Claude's response
        """
        response = self._execute_claude_command(
            prompt=prompt,
            path=path,
            resume_session=session_id
        )
        
        if not response.success:
            raise ClaudeCodeExecutionError(
                response.exit_code,
                response.raw_output,
                response.stderr
            )
        
        return response.text
    
    def get_sessions(self) -> Dict[str, SessionInfo]:
        """Get all active sessions."""
        with self._session_lock:
            return self._sessions.copy()
    
    def get_current_session(self) -> Optional[SessionInfo]:
        """Get current session info."""
        with self._session_lock:
            if self._current_session_id:
                return self._sessions.get(self._current_session_id)
            return None
    
    def cleanup_expired_sessions(self, max_age: float = 3600):
        """Clean up expired sessions."""
        with self._session_lock:
            expired_sessions = [
                session_id for session_id, info in self._sessions.items()
                if info.is_expired(max_age)
            ]
            
            for session_id in expired_sessions:
                del self._sessions[session_id]
                logger.debug(f"Cleaned up expired session: {session_id}")
    
    def set_config(self, **kwargs) -> 'ClaudeCode':
        """
        Create a new instance with updated configuration.
        
        Args:
            **kwargs: Configuration parameters to update
            
        Returns:
            ClaudeCode: New instance with updated configuration
        """
        new_config = self.config.copy(**kwargs)
        return ClaudeCode(config=new_config)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup_expired_sessions()


class ClaudeCodeContext:
    """
    Context manager for Claude Code operations.
    
    This class provides a context manager interface for managing
    Claude Code operations with automatic cleanup and resource management.
    """
    
    def __init__(
        self,
        config: Optional[ClaudeConfig] = None,
        auto_cleanup: bool = True,
        **kwargs
    ):
        """
        Initialize context manager.
        
        Args:
            config: Optional ClaudeConfig instance
            auto_cleanup: Whether to automatically cleanup on exit
            **kwargs: Additional configuration options
        """
        self.config = config or ClaudeConfig(**kwargs)
        self.auto_cleanup = auto_cleanup
        self.claude_code: Optional[ClaudeCode] = None
        self._temp_files: List[Path] = []
        self._temp_dirs: List[Path] = []
    
    def __enter__(self) -> ClaudeCode:
        """Enter context manager."""
        self.claude_code = ClaudeCode(config=self.config)
        return self.claude_code
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self.auto_cleanup and self.claude_code:
            self.claude_code.cleanup_expired_sessions()
        
        # Clean up temporary files and directories
        self._cleanup_temp_resources()
    
    def _cleanup_temp_resources(self):
        """Clean up temporary resources."""
        for temp_file in self._temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")
        
        for temp_dir in self._temp_dirs:
            try:
                if temp_dir.exists():
                    import shutil
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp dir {temp_dir}: {e}")
    
    def create_temp_file(self, suffix: str = ".tmp") -> Path:
        """Create a temporary file that will be cleaned up."""
        import tempfile
        temp_file = Path(tempfile.mktemp(suffix=suffix))
        self._temp_files.append(temp_file)
        return temp_file
    
    def create_temp_dir(self) -> Path:
        """Create a temporary directory that will be cleaned up."""
        import tempfile
        temp_dir = Path(tempfile.mkdtemp())
        self._temp_dirs.append(temp_dir)
        return temp_dir


class ClaudeCodeBatch:
    """
    Handle multiple Claude Code operations in batch.
    
    This class allows you to queue multiple operations and execute them
    in batch, with support for parallel execution and result aggregation.
    """
    
    def __init__(
        self,
        claude_code: ClaudeCode,
        max_parallel: int = 3,
        fail_fast: bool = False
    ):
        """
        Initialize batch processor.
        
        Args:
            claude_code: ClaudeCode instance to use
            max_parallel: Maximum number of parallel operations
            fail_fast: Whether to stop on first failure
        """
        self.claude_code = claude_code
        self.max_parallel = max_parallel
        self.fail_fast = fail_fast
        self._operations: List[Dict[str, Any]] = []
        self._results: List[Union[str, Exception]] = []
    
    def add_operation(
        self,
        prompt: str,
        path: Optional[Union[str, Path]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> 'ClaudeCodeBatch':
        """
        Add operation to batch.
        
        Args:
            prompt: The prompt to send
            path: Working directory
            model: Model to use
            **kwargs: Additional arguments
            
        Returns:
            ClaudeCodeBatch: Self for method chaining
        """
        self._operations.append({
            "prompt": prompt,
            "path": path,
            "model": model,
            **kwargs
        })
        return self
    
    def execute_batch(self) -> List[Union[str, Exception]]:
        """
        Execute all operations in batch.
        
        Returns:
            List[Union[str, Exception]]: Results or exceptions for each operation
        """
        if not self._operations:
            return []
        
        self._results = []
        
        if self.max_parallel == 1:
            # Sequential execution
            for operation in self._operations:
                result = self._execute_single_operation(operation)
                self._results.append(result)
                
                if self.fail_fast and isinstance(result, Exception):
                    break
        else:
            # Parallel execution
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
                futures = [
                    executor.submit(self._execute_single_operation, operation)
                    for operation in self._operations
                ]
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    self._results.append(result)
                    
                    if self.fail_fast and isinstance(result, Exception):
                        # Cancel remaining futures
                        for f in futures:
                            f.cancel()
                        break
        
        return self._results
    
    def _execute_single_operation(self, operation: Dict[str, Any]) -> Union[str, Exception]:
        """Execute a single operation."""
        try:
            return self.claude_code(**operation)
        except Exception as e:
            logger.error(f"Batch operation failed: {e}")
            return e
    
    def get_results(self) -> List[Union[str, Exception]]:
        """Get results of executed operations."""
        return self._results.copy()
    
    def get_successful_results(self) -> List[str]:
        """Get only successful results."""
        return [
            result for result in self._results
            if isinstance(result, str)
        ]
    
    def get_failed_results(self) -> List[Exception]:
        """Get only failed results."""
        return [
            result for result in self._results
            if isinstance(result, Exception)
        ]
    
    def clear(self) -> 'ClaudeCodeBatch':
        """Clear all operations and results."""
        self._operations.clear()
        self._results.clear()
        return self
    
    def __len__(self) -> int:
        """Get number of operations."""
        return len(self._operations) 