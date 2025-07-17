"""
Configuration management for claude-code-botman package.

This module provides configuration classes and utilities for managing
Claude Code CLI settings, API keys, and operational parameters.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import json

from .exceptions import ClaudeCodeConfigurationError, ClaudeCodeModelError, ClaudeCodePathError


# Supported Claude models (updated for production)
SUPPORTED_MODELS = {
    "claude-opus-4-20250514": "Claude Opus 4 (most powerful)",
    "claude-sonnet-4-20250514": "Claude Sonnet 4 (balanced)",
    "claude-3-5-haiku-20241022": "Claude 3.5 Haiku (fastest)",
    "claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet (legacy)",
    "claude-3-opus-20240229": "Claude 3 Opus (legacy)",
}

# Model aliases for convenience
MODEL_ALIASES = {
    "opus": "claude-opus-4-20250514",
    "sonnet": "claude-sonnet-4-20250514",
    "haiku": "claude-3-5-haiku-20241022",
    "opus-4": "claude-opus-4-20250514",
    "sonnet-4": "claude-sonnet-4-20250514",
    "haiku-3.5": "claude-3-5-haiku-20241022",
}

# Default configuration values
DEFAULT_CONFIG = {
    "model": "claude-sonnet-4-20250514",
    "timeout": 300,
    "max_turns": 10,
    "output_format": "text",
    "verbose": False,
    "auto_continue": False,
    "save_sessions": True,
}


@dataclass
class ClaudeConfig:
    """
    Configuration settings for Claude Code CLI operations.
    
    This class manages all configuration parameters for Claude Code CLI
    interactions, including API keys, model settings, and operational parameters.
    """
    
    # Core settings
    model: str = DEFAULT_CONFIG["model"]
    api_key: Optional[str] = None
    default_path: Path = field(default_factory=lambda: Path("./"))
    
    # Operational settings
    timeout: int = DEFAULT_CONFIG["timeout"]
    max_turns: int = DEFAULT_CONFIG["max_turns"]
    output_format: str = DEFAULT_CONFIG["output_format"]
    verbose: bool = DEFAULT_CONFIG["verbose"]
    
    # Advanced settings
    auto_continue: bool = DEFAULT_CONFIG["auto_continue"]
    save_sessions: bool = DEFAULT_CONFIG["save_sessions"]
    session_dir: Optional[Path] = None
    
    # CLI-specific settings
    allowed_tools: List[str] = field(default_factory=list)
    disallowed_tools: List[str] = field(default_factory=list)
    dangerously_skip_permissions: bool = False  # --dangerously-skip-permissions flag
    
    # New CLI arguments from documentation
    add_dir: List[str] = field(default_factory=list)  # Additional working directories
    input_format: str = "text"  # "text", "stream-json"
    mcp_config: Optional[str] = None  # MCP configuration file or string
    append_system_prompt: Optional[str] = None  # Append to system prompt
    fallback_model: Optional[str] = None  # Fallback model when overloaded
    ide: bool = False  # Automatically connect to IDE
    strict_mcp_config: bool = False  # Only use MCP servers from --mcp-config
    
    # Environment settings
    environment_variables: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and normalize configuration after initialization."""
        self._validate_and_normalize()
    
    def _validate_and_normalize(self):
        """Validate configuration parameters and normalize values."""
        # Handle API key
        if self.api_key is None:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            raise ClaudeCodeConfigurationError(
                "API key must be provided or set in ANTHROPIC_API_KEY environment variable"
            )
        
        # Validate output format
        valid_formats = ["text", "json", "stream-json"]
        if self.output_format not in valid_formats:
            raise ClaudeCodeConfigurationError(
                f"Invalid output format: {self.output_format}. "
                f"Valid formats: {', '.join(valid_formats)}"
            )
        
        # Validate input format
        valid_input_formats = ["text", "stream-json"]
        if self.input_format not in valid_input_formats:
            raise ClaudeCodeConfigurationError(
                f"Invalid input format: {self.input_format}. "
                f"Valid formats: {', '.join(valid_input_formats)}"
            )
        
        # Validate model aliases
        if self.model in MODEL_ALIASES:
            self.model = MODEL_ALIASES[self.model]
        
        # Validate paths
        if self.default_path and not Path(self.default_path).exists():
            raise ClaudeCodePathError(f"Default path does not exist: {self.default_path}")
        
        if self.session_dir and not Path(self.session_dir).exists():
            try:
                Path(self.session_dir).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ClaudeCodePathError(f"Cannot create session directory: {e}")
        
        # Validate add_dir paths
        for dir_path in self.add_dir:
            if not Path(dir_path).exists():
                raise ClaudeCodePathError(f"Additional directory does not exist: {dir_path}")
        
        # Validate MCP config if provided
        if self.mcp_config and not self.mcp_config.startswith('{'):
            # If it's not JSON string, treat as file path
            if not Path(self.mcp_config).exists():
                raise ClaudeCodePathError(f"MCP config file does not exist: {self.mcp_config}")
        
        # Validate fallback model
        if self.fallback_model and self.fallback_model in MODEL_ALIASES:
            self.fallback_model = MODEL_ALIASES[self.fallback_model]
    
    def _normalize_model(self, model: str) -> str:
        """Normalize model name, handling aliases."""
        # Check if it's an alias
        if model.lower() in MODEL_ALIASES:
            return MODEL_ALIASES[model.lower()]
        
        # Check if it's a supported model
        if model in SUPPORTED_MODELS:
            return model
        
        # Check if it's a partial match
        for supported_model in SUPPORTED_MODELS:
            if model.lower() in supported_model.lower():
                return supported_model
        
        # If not found, raise an error
        raise ClaudeCodeModelError(
            model,
            f"Unsupported model: {model}. "
            f"Supported models: {', '.join(SUPPORTED_MODELS.keys())}"
        )
    
    def to_cli_args(self) -> List[str]:
        """Convert configuration to CLI arguments."""
        args = []
        
        # Output format
        if self.output_format != "text":
            args.extend(["--output-format", self.output_format])
        
        # Input format
        if self.input_format != "text":
            args.extend(["--input-format", self.input_format])
        
        # Verbose
        if self.verbose:
            args.append("--verbose")
        
        # Debug mode
        if self.verbose:  # Using verbose as debug indicator
            args.append("--debug")
        
        # Dangerously skip permissions
        if self.dangerously_skip_permissions:
            args.append("--dangerously-skip-permissions")
        
        # Allowed tools
        if self.allowed_tools:
            args.append("--allowedTools")
            args.extend(self.allowed_tools)
        
        # Disallowed tools
        if self.disallowed_tools:
            args.append("--disallowedTools")
            args.extend(self.disallowed_tools)
        
        # Additional directories
        if self.add_dir:
            args.append("--add-dir")
            args.extend(self.add_dir)
        
        # MCP configuration
        if self.mcp_config:
            args.extend(["--mcp-config", self.mcp_config])
        
        # Append system prompt
        if self.append_system_prompt:
            args.extend(["--append-system-prompt", self.append_system_prompt])
        
        # Fallback model
        if self.fallback_model:
            args.extend(["--fallback-model", self.fallback_model])
        
        # IDE connection
        if self.ide:
            args.append("--ide")
        
        # Strict MCP config
        if self.strict_mcp_config:
            args.append("--strict-mcp-config")
        
        return args
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "model": self.model,
            "api_key": "***" if self.api_key else None,  # Mask API key
            "default_path": str(self.default_path),
            "timeout": self.timeout,
            "max_turns": self.max_turns,
            "output_format": self.output_format,
            "input_format": self.input_format,
            "verbose": self.verbose,
            "auto_continue": self.auto_continue,
            "save_sessions": self.save_sessions,
            "session_dir": str(self.session_dir) if self.session_dir else None,
            "allowed_tools": self.allowed_tools,
            "disallowed_tools": self.disallowed_tools,
            "dangerously_skip_permissions": self.dangerously_skip_permissions,
            "add_dir": self.add_dir,
            "mcp_config": self.mcp_config,
            "append_system_prompt": self.append_system_prompt,
            "fallback_model": self.fallback_model,
            "ide": self.ide,
            "strict_mcp_config": self.strict_mcp_config,
            "environment_variables": self.environment_variables,
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ClaudeConfig":
        """Create configuration from dictionary."""
        # Handle path conversion
        if "default_path" in config_dict:
            config_dict["default_path"] = Path(config_dict["default_path"])
        
        if "session_dir" in config_dict and config_dict["session_dir"]:
            config_dict["session_dir"] = Path(config_dict["session_dir"])
        
        return cls(**config_dict)
    
    @classmethod
    def from_file(cls, config_file: Union[str, Path]) -> "ClaudeConfig":
        """Load configuration from JSON file."""
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise ClaudeCodeConfigurationError(
                f"Configuration file not found: {config_path}"
            )
        
        try:
            with open(config_path, "r") as f:
                config_dict = json.load(f)
            return cls.from_dict(config_dict)
        except json.JSONDecodeError as e:
            raise ClaudeCodeConfigurationError(
                f"Invalid JSON in configuration file: {e}"
            )
        except Exception as e:
            raise ClaudeCodeConfigurationError(
                f"Error loading configuration file: {e}"
            )
    
    def save_to_file(self, config_file: Union[str, Path]):
        """Save configuration to JSON file."""
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            raise ClaudeCodeConfigurationError(
                f"Error saving configuration file: {e}"
            )
    
    def copy(self, **kwargs) -> "ClaudeConfig":
        """Create a copy of the configuration with optional overrides."""
        config_dict = self.to_dict()
        
        # Remove masked API key and restore original
        config_dict["api_key"] = self.api_key
        
        # Apply overrides
        config_dict.update(kwargs)
        
        return self.from_dict(config_dict)
    
    def get_environment(self) -> Dict[str, str]:
        """Get environment variables for subprocess execution."""
        env = os.environ.copy()
        
        # Add API key
        if self.api_key:
            env["ANTHROPIC_API_KEY"] = self.api_key
        
        # Add custom environment variables
        env.update(self.environment_variables)
        
        return env


def get_default_config() -> ClaudeConfig:
    """Get default configuration instance."""
    return ClaudeConfig()


def load_config_from_env() -> ClaudeConfig:
    """Load configuration from environment variables."""
    config_dict = {}
    
    # Map environment variables to config keys
    env_mapping = {
        "CLAUDE_MODEL": "model",
        "CLAUDE_TIMEOUT": "timeout",
        "CLAUDE_MAX_TURNS": "max_turns",
        "CLAUDE_OUTPUT_FORMAT": "output_format",
        "CLAUDE_INPUT_FORMAT": "input_format",
        "CLAUDE_VERBOSE": "verbose",
        "CLAUDE_AUTO_CONTINUE": "auto_continue",
        "CLAUDE_SAVE_SESSIONS": "save_sessions",
        "CLAUDE_DEFAULT_PATH": "default_path",
        "CLAUDE_SESSION_DIR": "session_dir",
        "CLAUDE_DANGEROUSLY_SKIP_PERMISSIONS": "dangerously_skip_permissions",
        "CLAUDE_MCP_CONFIG": "mcp_config",
        "CLAUDE_APPEND_SYSTEM_PROMPT": "append_system_prompt",
        "CLAUDE_FALLBACK_MODEL": "fallback_model",
        "CLAUDE_IDE": "ide",
        "CLAUDE_STRICT_MCP_CONFIG": "strict_mcp_config",
    }
    
    # Load basic configuration
    for env_var, config_key in env_mapping.items():
        value = os.getenv(env_var)
        if value is not None:
            # Convert boolean strings
            if config_key in ["verbose", "auto_continue", "save_sessions", 
                            "dangerously_skip_permissions", "ide", "strict_mcp_config"]:
                config_dict[config_key] = value.lower() in ("true", "1", "yes", "on")
            # Convert numeric strings
            elif config_key in ["timeout", "max_turns"]:
                config_dict[config_key] = int(value)
            else:
                config_dict[config_key] = value
    
    # Load list-based configurations
    allowed_tools = os.getenv("CLAUDE_ALLOWED_TOOLS")
    if allowed_tools:
        config_dict["allowed_tools"] = [tool.strip() for tool in allowed_tools.split(",")]
    
    disallowed_tools = os.getenv("CLAUDE_DISALLOWED_TOOLS")
    if disallowed_tools:
        config_dict["disallowed_tools"] = [tool.strip() for tool in disallowed_tools.split(",")]
    
    add_dir = os.getenv("CLAUDE_ADD_DIR")
    if add_dir:
        config_dict["add_dir"] = [dir_path.strip() for dir_path in add_dir.split(",")]
    
    # Load environment variables with CLAUDE_ENV_ prefix
    environment_variables = {}
    for key, value in os.environ.items():
        if key.startswith("CLAUDE_ENV_"):
            env_key = key[11:]  # Remove "CLAUDE_ENV_" prefix
            environment_variables[env_key] = value
    
    if environment_variables:
        config_dict["environment_variables"] = environment_variables
    
    # Always include API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        config_dict["api_key"] = api_key
    
    return ClaudeConfig(**config_dict)


def merge_configs(*configs: ClaudeConfig) -> ClaudeConfig:
    """Merge multiple configurations, with later configs taking precedence."""
    if not configs:
        return get_default_config()
    
    base_config = configs[0].to_dict()
    base_config["api_key"] = configs[0].api_key  # Restore original API key
    
    for config in configs[1:]:
        config_dict = config.to_dict()
        config_dict["api_key"] = config.api_key  # Restore original API key
        
        # Merge dictionaries, with later configs taking precedence
        for key, value in config_dict.items():
            if value is not None:
                base_config[key] = value
    
    return ClaudeConfig.from_dict(base_config) 