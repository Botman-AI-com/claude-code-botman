"""
Custom exceptions for claude-code-botman package.

This module defines all custom exceptions that can be raised during
Claude Code CLI operations.
"""

from typing import Optional, Any


class ClaudeCodeError(Exception):
    """
    Base exception for all Claude Code operations.
    
    This is the base class for all exceptions raised by the claude-code-botman
    package. It provides a common interface for error handling.
    """
    
    def __init__(self, message: str, details: Optional[dict] = None):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """Return string representation of the exception."""
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class ClaudeCodeNotFoundError(ClaudeCodeError):
    """
    Raised when Claude Code CLI is not found on the system.
    
    This exception is raised when the 'claude' command is not available
    in the system PATH or when the Claude Code CLI is not properly installed.
    """
    
    def __init__(self, message: str = "Claude Code CLI not found", details: Optional[dict] = None):
        super().__init__(message, details)


class ClaudeCodeTimeoutError(ClaudeCodeError):
    """
    Raised when a Claude Code CLI operation times out.
    
    This exception is raised when a subprocess call to Claude Code CLI
    exceeds the specified timeout duration.
    """
    
    def __init__(self, timeout: float, message: Optional[str] = None, details: Optional[dict] = None):
        """
        Initialize the timeout exception.
        
        Args:
            timeout: The timeout duration that was exceeded
            message: Optional custom error message
            details: Optional additional error details
        """
        if message is None:
            message = f"Claude Code CLI operation timed out after {timeout} seconds"
        super().__init__(message, details)
        self.timeout = timeout


class ClaudeCodeAuthenticationError(ClaudeCodeError):
    """
    Raised when authentication with Claude Code CLI fails.
    
    This exception is raised when there are issues with API key validation,
    authentication setup, or access permissions.
    """
    
    def __init__(self, message: str = "Authentication failed", details: Optional[dict] = None):
        super().__init__(message, details)


class ClaudeCodeExecutionError(ClaudeCodeError):
    """
    Raised when Claude Code CLI execution fails.
    
    This exception is raised when the Claude Code CLI subprocess returns
    a non-zero exit code or encounters an execution error.
    """
    
    def __init__(
        self, 
        exit_code: int, 
        stdout: str = "", 
        stderr: str = "", 
        command: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[dict] = None
    ):
        """
        Initialize the execution error.
        
        Args:
            exit_code: The exit code returned by the subprocess
            stdout: Standard output from the subprocess
            stderr: Standard error from the subprocess
            command: The command that was executed
            message: Optional custom error message
            details: Optional additional error details
        """
        if message is None:
            message = f"Claude Code CLI execution failed with exit code {exit_code}"
        
        error_details = details or {}
        error_details.update({
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "command": command,
        })
        
        super().__init__(message, error_details)
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.command = command


class ClaudeCodeConfigurationError(ClaudeCodeError):
    """
    Raised when there are configuration-related errors.
    
    This exception is raised when there are issues with configuration
    validation, missing required settings, or invalid parameter values.
    """
    
    def __init__(self, message: str = "Configuration error", details: Optional[dict] = None):
        super().__init__(message, details)


class ClaudeCodePathError(ClaudeCodeError):
    """
    Raised when there are path-related errors.
    
    This exception is raised when there are issues with file paths,
    directory access, or path validation.
    """
    
    def __init__(self, path: str, message: Optional[str] = None, details: Optional[dict] = None):
        """
        Initialize the path error.
        
        Args:
            path: The problematic path
            message: Optional custom error message
            details: Optional additional error details
        """
        if message is None:
            message = f"Path error: {path}"
        
        error_details = details or {}
        error_details["path"] = path
        
        super().__init__(message, error_details)
        self.path = path


class ClaudeCodeModelError(ClaudeCodeError):
    """
    Raised when there are model-related errors.
    
    This exception is raised when there are issues with model selection,
    model availability, or model-specific configurations.
    """
    
    def __init__(self, model: str, message: Optional[str] = None, details: Optional[dict] = None):
        """
        Initialize the model error.
        
        Args:
            model: The problematic model name
            message: Optional custom error message
            details: Optional additional error details
        """
        if message is None:
            message = f"Model error: {model}"
        
        error_details = details or {}
        error_details["model"] = model
        
        super().__init__(message, error_details)
        self.model = model


class ClaudeCodeResponseError(ClaudeCodeError):
    """
    Raised when there are response parsing or processing errors.
    
    This exception is raised when there are issues with parsing Claude's
    response, extracting information, or processing the output.
    """
    
    def __init__(self, response: str, message: Optional[str] = None, details: Optional[dict] = None):
        """
        Initialize the response error.
        
        Args:
            response: The problematic response content
            message: Optional custom error message
            details: Optional additional error details
        """
        if message is None:
            message = "Response processing error"
        
        error_details = details or {}
        error_details["response"] = response
        
        super().__init__(message, error_details)
        self.response = response 