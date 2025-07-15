"""
Unit tests for claude_code_botman.utils module.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import subprocess

from claude_code_botman.utils import (
    ClaudeResponse,
    check_claude_cli_installed,
    get_claude_cli_version,
    validate_claude_cli,
    format_command_args,
    validate_model_name,
    sanitize_path,
    ensure_directory_exists,
    is_safe_path,
    parse_cli_output,
    escape_shell_arg,
    get_system_info,
    measure_execution_time,
    retry_on_failure,
)
from claude_code_botman.exceptions import (
    ClaudeCodeNotFoundError,
    ClaudeCodePathError,
    ClaudeCodeResponseError,
)


class TestClaudeResponse:
    """Test cases for ClaudeResponse class."""
    
    def test_init_basic(self):
        """Test ClaudeResponse initialization."""
        response = ClaudeResponse(
            raw_output="Hello World!",
            exit_code=0,
            stderr=""
        )
        
        assert response.raw_output == "Hello World!"
        assert response.exit_code == 0
        assert response.stderr == ""
        assert response.timestamp is not None
        assert response.success is True
    
    def test_init_with_error(self):
        """Test ClaudeResponse initialization with error."""
        response = ClaudeResponse(
            raw_output="Error occurred",
            exit_code=1,
            stderr="Command failed"
        )
        
        assert response.exit_code == 1
        assert response.stderr == "Command failed"
        assert response.success is False
    
    def test_parse_json_output(self):
        """Test parsing JSON output."""
        json_output = '{"message": "Hello", "files": ["test.py"]}'
        response = ClaudeResponse(raw_output=json_output)
        
        assert response.parsed_content["message"] == "Hello"
        assert response.parsed_content["files"] == ["test.py"]
    
    def test_extract_files_created(self):
        """Test extracting files created from output."""
        output = """
        Creating hello.py
        Created file: world.txt
        Writing to test.js
        Saved to config.json
        """
        response = ClaudeResponse(raw_output=output)
        
        files = response.files_created
        assert "hello.py" in files
        assert "world.txt" in files
        assert "test.js" in files
        assert "config.json" in files
    
    def test_extract_files_modified(self):
        """Test extracting files modified from output."""
        output = """
        Modified main.py
        Updated: config.yaml
        Editing src/utils.py
        Changed package.json
        """
        response = ClaudeResponse(raw_output=output)
        
        files = response.files_modified
        assert "main.py" in files
        assert "config.yaml" in files
        assert "src/utils.py" in files
        assert "package.json" in files
    
    def test_extract_commands_executed(self):
        """Test extracting commands executed from output."""
        output = """
        Executing: npm install
        Running: python setup.py build
        Command: git add .
        $ make test
        """
        response = ClaudeResponse(raw_output=output)
        
        commands = response.commands_executed
        assert "npm install" in commands
        assert "python setup.py build" in commands
        assert "git add ." in commands
        assert "make test" in commands
    
    def test_extract_errors(self):
        """Test extracting errors from output."""
        output = """
        Error: File not found
        ERROR: Compilation failed
        Failed: Network timeout
        Exception: Invalid syntax
        """
        response = ClaudeResponse(raw_output=output)
        
        errors = response.errors
        assert "File not found" in errors
        assert "Compilation failed" in errors
        assert "Network timeout" in errors
        assert "Invalid syntax" in errors
    
    def test_extract_warnings(self):
        """Test extracting warnings from output."""
        output = """
        Warning: Deprecated function used
        WARN: Memory usage high
        Caution: Untested feature
        """
        response = ClaudeResponse(raw_output=output)
        
        warnings = response.warnings
        assert "Deprecated function used" in warnings
        assert "Memory usage high" in warnings
        assert "Untested feature" in warnings
    
    def test_extract_session_id(self):
        """Test extracting session ID from output."""
        output = "Session ID: abc123def456"
        response = ClaudeResponse(raw_output=output)
        
        assert response.session_id == "abc123def456"
    
    def test_properties(self):
        """Test ClaudeResponse properties."""
        output = """
        Created file: test.py
        Modified: config.yaml
        Executing: npm test
        Warning: Deprecated API
        Error: Connection failed
        """
        response = ClaudeResponse(raw_output=output, exit_code=1)
        
        assert response.text == output
        assert len(response.files_created) > 0
        assert len(response.files_modified) > 0
        assert len(response.commands_executed) > 0
        assert len(response.warnings) > 0
        assert len(response.errors) > 0
        assert response.has_errors is True
        assert response.has_warnings is True
        assert response.success is False
    
    def test_to_dict(self):
        """Test to_dict method."""
        response = ClaudeResponse(
            raw_output="Test output",
            exit_code=0,
            stderr=""
        )
        
        result = response.to_dict()
        
        assert result["raw_output"] == "Test output"
        assert result["exit_code"] == 0
        assert result["stderr"] == ""
        assert "timestamp" in result
        assert "parsed_content" in result
        assert result["success"] is True
    
    def test_str_and_repr(self):
        """Test string representations."""
        response = ClaudeResponse(
            raw_output="Test output",
            exit_code=0
        )
        
        assert str(response) == "Test output"
        assert "ClaudeResponse" in repr(response)
        assert "success=True" in repr(response)


class TestCliValidation:
    """Test cases for CLI validation functions."""
    
    @patch('claude_code_botman.utils.shutil.which')
    def test_check_claude_cli_installed_true(self, mock_which):
        """Test check_claude_cli_installed when CLI is available."""
        mock_which.return_value = "/usr/local/bin/claude"
        
        result = check_claude_cli_installed()
        
        assert result is True
        mock_which.assert_called_once_with("claude")
    
    @patch('claude_code_botman.utils.shutil.which')
    def test_check_claude_cli_installed_false(self, mock_which):
        """Test check_claude_cli_installed when CLI is not available."""
        mock_which.return_value = None
        
        result = check_claude_cli_installed()
        
        assert result is False
    
    @patch('claude_code_botman.utils.subprocess.run')
    def test_get_claude_cli_version_success(self, mock_run):
        """Test get_claude_cli_version with successful response."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="claude version 1.2.3"
        )
        
        result = get_claude_cli_version()
        
        assert result == "1.2.3"
        mock_run.assert_called_once_with(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
    
    @patch('claude_code_botman.utils.subprocess.run')
    def test_get_claude_cli_version_failure(self, mock_run):
        """Test get_claude_cli_version with failure."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="Error"
        )
        
        result = get_claude_cli_version()
        
        assert result is None
    
    @patch('claude_code_botman.utils.subprocess.run')
    def test_get_claude_cli_version_timeout(self, mock_run):
        """Test get_claude_cli_version with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("claude", 10)
        
        result = get_claude_cli_version()
        
        assert result is None
    
    @patch('claude_code_botman.utils.check_claude_cli_installed')
    def test_validate_claude_cli_not_found(self, mock_check):
        """Test validate_claude_cli when CLI is not found."""
        mock_check.return_value = False
        
        with pytest.raises(ClaudeCodeNotFoundError):
            validate_claude_cli()
    
    @patch('claude_code_botman.utils.get_claude_cli_version')
    @patch('claude_code_botman.utils.check_claude_cli_installed')
    def test_validate_claude_cli_not_responding(self, mock_check, mock_version):
        """Test validate_claude_cli when CLI is not responding."""
        mock_check.return_value = True
        mock_version.return_value = None
        
        with pytest.raises(ClaudeCodeNotFoundError):
            validate_claude_cli()
    
    @patch('claude_code_botman.utils.get_claude_cli_version')
    @patch('claude_code_botman.utils.check_claude_cli_installed')
    def test_validate_claude_cli_success(self, mock_check, mock_version):
        """Test validate_claude_cli with successful validation."""
        mock_check.return_value = True
        mock_version.return_value = "1.2.3"
        
        # Should not raise any exception
        validate_claude_cli()


class TestCommandFormatting:
    """Test cases for command formatting functions."""
    
    def test_format_command_args_basic(self):
        """Test format_command_args with basic arguments."""
        args = format_command_args(verbose=True, model="claude-sonnet-4")
        
        assert "--verbose" in args
        assert "--model" in args
        assert "claude-sonnet-4" in args
    
    def test_format_command_args_boolean_false(self):
        """Test format_command_args with false boolean."""
        args = format_command_args(verbose=False, debug=True)
        
        assert "--verbose" not in args
        assert "--debug" in args
    
    def test_format_command_args_list(self):
        """Test format_command_args with list values."""
        args = format_command_args(files=["file1.py", "file2.py"])
        
        assert "--files" in args
        assert "file1.py" in args
        assert "file2.py" in args
    
    def test_format_command_args_none_value(self):
        """Test format_command_args with None values."""
        args = format_command_args(model=None, timeout=30)
        
        assert "--model" not in args
        assert "--timeout" in args
        assert "30" in args
    
    def test_format_command_args_underscore_conversion(self):
        """Test format_command_args converts underscores to hyphens."""
        args = format_command_args(max_turns=5, output_format="json")
        
        assert "--max-turns" in args
        assert "--output-format" in args
        assert "5" in args
        assert "json" in args
    
    def test_escape_shell_arg(self):
        """Test escape_shell_arg function."""
        # Test basic string
        assert escape_shell_arg("hello") == "'hello'"
        
        # Test string with spaces
        assert escape_shell_arg("hello world") == "'hello world'"
        
        # Test string with special characters
        result = escape_shell_arg("echo 'hello'; rm -rf /")
        assert "'" in result or '"' in result


class TestModelValidation:
    """Test cases for model validation functions."""
    
    def test_validate_model_name_supported(self):
        """Test validate_model_name with supported model."""
        assert validate_model_name("claude-sonnet-4-20250514") is True
        assert validate_model_name("claude-opus-4-20250514") is True
    
    def test_validate_model_name_alias(self):
        """Test validate_model_name with model alias."""
        assert validate_model_name("sonnet") is True
        assert validate_model_name("opus") is True
    
    def test_validate_model_name_partial_match(self):
        """Test validate_model_name with partial match."""
        assert validate_model_name("sonnet-4") is True
        assert validate_model_name("opus-4") is True
    
    def test_validate_model_name_invalid(self):
        """Test validate_model_name with invalid model."""
        assert validate_model_name("invalid-model") is False
        assert validate_model_name("gpt-4") is False


class TestPathHandling:
    """Test cases for path handling functions."""
    
    def test_sanitize_path_basic(self):
        """Test sanitize_path with basic path."""
        path = sanitize_path("./test")
        assert isinstance(path, Path)
        assert path.is_absolute()
    
    def test_sanitize_path_with_traversal(self):
        """Test sanitize_path with directory traversal."""
        # Should still work but log warning
        path = sanitize_path("../test")
        assert isinstance(path, Path)
    
    def test_sanitize_path_invalid(self):
        """Test sanitize_path with invalid path."""
        with pytest.raises(ClaudeCodePathError):
            sanitize_path("\x00invalid")
    
    def test_ensure_directory_exists_new(self):
        """Test ensure_directory_exists with new directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "new_dir"
            
            result = ensure_directory_exists(test_dir)
            
            assert result == test_dir
            assert test_dir.exists()
            assert test_dir.is_dir()
    
    def test_ensure_directory_exists_existing(self):
        """Test ensure_directory_exists with existing directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = ensure_directory_exists(temp_dir)
            
            assert result == Path(temp_dir).resolve()
            assert result.exists()
    
    def test_is_safe_path_safe(self):
        """Test is_safe_path with safe path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            safe_path = base_path / "subdir"
            
            assert is_safe_path(safe_path, base_path) is True
    
    def test_is_safe_path_unsafe(self):
        """Test is_safe_path with unsafe path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "base"
            unsafe_path = Path(temp_dir) / "other"
            
            base_path.mkdir()
            unsafe_path.mkdir()
            
            assert is_safe_path(unsafe_path, base_path) is False


class TestOutputParsing:
    """Test cases for output parsing functions."""
    
    def test_parse_cli_output_text(self):
        """Test parse_cli_output with text format."""
        output = "Hello World!"
        result = parse_cli_output(output, "text")
        
        assert result["text"] == "Hello World!"
    
    def test_parse_cli_output_json(self):
        """Test parse_cli_output with JSON format."""
        output = '{"message": "Hello", "status": "success"}'
        result = parse_cli_output(output, "json")
        
        assert result["message"] == "Hello"
        assert result["status"] == "success"
    
    def test_parse_cli_output_stream_json(self):
        """Test parse_cli_output with stream-json format."""
        output = '{"line": 1}\n{"line": 2}\n{"line": 3}'
        result = parse_cli_output(output, "stream-json")
        
        assert "stream_results" in result
        assert len(result["stream_results"]) == 3
        assert result["stream_results"][0]["line"] == 1
    
    def test_parse_cli_output_invalid_json(self):
        """Test parse_cli_output with invalid JSON."""
        output = '{"invalid": json}'
        
        with pytest.raises(ClaudeCodeResponseError):
            parse_cli_output(output, "json")


class TestSystemInfo:
    """Test cases for system info functions."""
    
    @patch('claude_code_botman.utils.check_claude_cli_installed')
    @patch('claude_code_botman.utils.get_claude_cli_version')
    def test_get_system_info(self, mock_version, mock_installed):
        """Test get_system_info function."""
        mock_installed.return_value = True
        mock_version.return_value = "1.2.3"
        
        info = get_system_info()
        
        assert "platform" in info
        assert "python_version" in info
        assert "claude_cli_installed" in info
        assert "claude_cli_version" in info
        assert "working_directory" in info
        assert "environment_variables" in info
        
        assert info["claude_cli_installed"] is True
        assert info["claude_cli_version"] == "1.2.3"


class TestDecorators:
    """Test cases for decorator functions."""
    
    def test_measure_execution_time(self):
        """Test measure_execution_time decorator."""
        @measure_execution_time
        def test_function():
            return "result"
        
        result = test_function()
        assert result == "result"
    
    def test_retry_on_failure_success(self):
        """Test retry_on_failure decorator with success."""
        @retry_on_failure(max_retries=2)
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    def test_retry_on_failure_eventual_success(self):
        """Test retry_on_failure decorator with eventual success."""
        call_count = 0
        
        @retry_on_failure(max_retries=2, delay=0.1)
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"
        
        result = test_function()
        assert result == "success"
        assert call_count == 2
    
    def test_retry_on_failure_max_retries(self):
        """Test retry_on_failure decorator with max retries exceeded."""
        @retry_on_failure(max_retries=2, delay=0.1)
        def test_function():
            raise Exception("Persistent failure")
        
        with pytest.raises(Exception) as exc_info:
            test_function()
        
        assert str(exc_info.value) == "Persistent failure" 