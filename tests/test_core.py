"""
Unit tests for claude_code_botman.core module.
"""

import pytest
import subprocess
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from claude_code_botman.core import ClaudeCode, ClaudeCodeContext, ClaudeCodeBatch, SessionInfo
from claude_code_botman.config import ClaudeConfig
from claude_code_botman.utils import ClaudeResponse
from claude_code_botman.exceptions import (
    ClaudeCodeNotFoundError,
    ClaudeCodeTimeoutError,
    ClaudeCodeExecutionError,
    ClaudeCodePathError,
)


class TestClaudeCode:
    """Test cases for ClaudeCode class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        with patch('claude_code_botman.core.validate_claude_cli'):
            config = ClaudeConfig(
                api_key="test-key",
                model="claude-sonnet-4-20250514",
                default_path=Path.cwd(),
                timeout=30,
                verbose=False
            )
            return config
    
    @pytest.fixture
    def claude_code(self, mock_config):
        """Create a ClaudeCode instance for testing."""
        return ClaudeCode(config=mock_config)
    
    def test_init_with_config(self, mock_config):
        """Test ClaudeCode initialization with config."""
        claude_code = ClaudeCode(config=mock_config)
        assert claude_code.config == mock_config
        assert claude_code._sessions == {}
        assert claude_code._current_session_id is None
    
    def test_init_with_parameters(self):
        """Test ClaudeCode initialization with individual parameters."""
        with patch('claude_code_botman.core.validate_claude_cli'):
            claude_code = ClaudeCode(
                model="claude-opus-4-20250514",
                api_key="test-key",
                default_path="./test",
                timeout=60,
                verbose=True
            )
            assert claude_code.config.model == "claude-opus-4-20250514"
            assert claude_code.config.api_key == "test-key"
            assert claude_code.config.timeout == 60
            assert claude_code.config.verbose is True
    
    @patch('claude_code_botman.core.subprocess.run')
    def test_call_success(self, mock_run, claude_code):
        """Test successful __call__ method."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Hello World!",
            stderr=""
        )
        
        result = claude_code("Create a hello world file")
        
        assert result == "Hello World!"
        mock_run.assert_called_once()
    
    @patch('claude_code_botman.core.subprocess.run')
    def test_call_failure(self, mock_run, claude_code):
        """Test __call__ method with execution failure."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="Error occurred",
            stderr="Command failed"
        )
        
        with pytest.raises(ClaudeCodeExecutionError) as exc_info:
            claude_code("Invalid command")
        
        assert exc_info.value.exit_code == 1
        assert "Error occurred" in str(exc_info.value)
    
    @patch('claude_code_botman.core.subprocess.run')
    def test_call_timeout(self, mock_run, claude_code):
        """Test __call__ method with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("claude", 30)
        
        with pytest.raises(ClaudeCodeTimeoutError) as exc_info:
            claude_code("Long running command")
        
        assert exc_info.value.timeout == 30
    
    @patch('claude_code_botman.core.subprocess.run')
    def test_call_cli_not_found(self, mock_run, claude_code):
        """Test __call__ method when CLI is not found."""
        mock_run.side_effect = FileNotFoundError("claude not found")
        
        with pytest.raises(ClaudeCodeNotFoundError):
            claude_code("Test command")
    
    @pytest.mark.asyncio
    @patch('claude_code_botman.core.subprocess.run')
    async def test_async_call(self, mock_run, claude_code):
        """Test async_call method."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Async result",
            stderr=""
        )
        
        result = await claude_code.async_call("Test async command")
        
        assert result == "Async result"
    
    def test_build_command_basic(self, claude_code):
        """Test _build_command with basic parameters."""
        command = claude_code._build_command("Test prompt")
        
        assert command[0] == "claude"
        assert "-p" in command
        assert "--model" in command
        assert "claude-sonnet-4-20250514" in command
        assert "'Test prompt'" in command
    
    def test_build_command_with_model(self, claude_code):
        """Test _build_command with custom model."""
        command = claude_code._build_command("Test prompt", model="claude-opus-4-20250514")
        
        assert "--model" in command
        assert "claude-opus-4-20250514" in command
    
    def test_build_command_with_kwargs(self, claude_code):
        """Test _build_command with additional arguments."""
        command = claude_code._build_command(
            "Test prompt",
            verbose=True,
            max_turns=5
        )
        
        assert "--verbose" in command
        assert "--max-turns" in command
        assert "5" in command
    
    def test_resolve_path_default(self, claude_code):
        """Test _resolve_path with default path."""
        path = claude_code._resolve_path(None)
        assert path == claude_code.config.default_path
    
    def test_resolve_path_custom(self, claude_code):
        """Test _resolve_path with custom path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = claude_code._resolve_path(temp_dir)
            assert path == Path(temp_dir).resolve()
    
    def test_resolve_path_nonexistent(self, claude_code):
        """Test _resolve_path with nonexistent path."""
        with pytest.raises(ClaudeCodePathError):
            claude_code._resolve_path("/nonexistent/path")
    
    def test_update_session_info(self, claude_code):
        """Test _update_session_info method."""
        session_id = "test-session-123"
        path = Path.cwd()
        
        claude_code._update_session_info(session_id, path)
        
        assert session_id in claude_code._sessions
        assert claude_code._current_session_id == session_id
        assert claude_code._sessions[session_id].session_id == session_id
        assert claude_code._sessions[session_id].path == path
    
    @patch('claude_code_botman.core.subprocess.run')
    def test_continue_conversation(self, mock_run, claude_code):
        """Test continue_conversation method."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Continued conversation",
            stderr=""
        )
        
        result = claude_code.continue_conversation("Continue this")
        
        assert result == "Continued conversation"
        # Verify that continue flag was passed
        call_args = mock_run.call_args
        assert any("continue" in str(arg) for arg in call_args[0][0])
    
    @patch('claude_code_botman.core.subprocess.run')
    def test_resume_session(self, mock_run, claude_code):
        """Test resume_session method."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Resumed session",
            stderr=""
        )
        
        result = claude_code.resume_session("session-123", "Resume this")
        
        assert result == "Resumed session"
        # Verify that resume flag was passed
        call_args = mock_run.call_args
        assert any("session-123" in str(arg) for arg in call_args[0][0])
    
    def test_get_sessions(self, claude_code):
        """Test get_sessions method."""
        # Add some test sessions
        claude_code._update_session_info("session-1", Path.cwd())
        claude_code._update_session_info("session-2", Path.cwd())
        
        sessions = claude_code.get_sessions()
        
        assert len(sessions) == 2
        assert "session-1" in sessions
        assert "session-2" in sessions
    
    def test_get_current_session(self, claude_code):
        """Test get_current_session method."""
        # Initially no current session
        assert claude_code.get_current_session() is None
        
        # Add a session
        claude_code._update_session_info("current-session", Path.cwd())
        
        current = claude_code.get_current_session()
        assert current is not None
        assert current.session_id == "current-session"
    
    def test_cleanup_expired_sessions(self, claude_code):
        """Test cleanup_expired_sessions method."""
        import time
        
        # Add a session and make it appear expired
        claude_code._update_session_info("old-session", Path.cwd())
        claude_code._sessions["old-session"].last_used = time.time() - 7200  # 2 hours ago
        
        # Add a current session
        claude_code._update_session_info("new-session", Path.cwd())
        
        # Cleanup with 1 hour max age
        claude_code.cleanup_expired_sessions(max_age=3600)
        
        # Only new session should remain
        assert "old-session" not in claude_code._sessions
        assert "new-session" in claude_code._sessions
    
    def test_set_config(self, claude_code):
        """Test set_config method."""
        new_claude = claude_code.set_config(model="claude-opus-4-20250514", timeout=120)
        
        assert new_claude.config.model == "claude-opus-4-20250514"
        assert new_claude.config.timeout == 120
        assert new_claude is not claude_code  # Should be a new instance
    
    def test_context_manager(self, claude_code):
        """Test context manager functionality."""
        with claude_code as cc:
            assert cc is claude_code
        
        # Should have cleaned up expired sessions
        # This is hard to test without mocking, but we can at least verify
        # that the context manager works


class TestClaudeCodeContext:
    """Test cases for ClaudeCodeContext class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        return ClaudeConfig(
            api_key="test-key",
            model="claude-sonnet-4-20250514",
            default_path=Path.cwd(),
            timeout=30
        )
    
    @patch('claude_code_botman.core.validate_claude_cli')
    def test_context_manager(self, mock_validate, mock_config):
        """Test ClaudeCodeContext as context manager."""
        context = ClaudeCodeContext(config=mock_config)
        
        with context as claude_code:
            assert isinstance(claude_code, ClaudeCode)
            assert claude_code.config == mock_config
    
    @patch('claude_code_botman.core.validate_claude_cli')
    def test_create_temp_file(self, mock_validate, mock_config):
        """Test create_temp_file method."""
        context = ClaudeCodeContext(config=mock_config)
        
        with context:
            temp_file = context.create_temp_file(".txt")
            assert temp_file.suffix == ".txt"
            assert temp_file in context._temp_files
    
    @patch('claude_code_botman.core.validate_claude_cli')
    def test_create_temp_dir(self, mock_validate, mock_config):
        """Test create_temp_dir method."""
        context = ClaudeCodeContext(config=mock_config)
        
        with context:
            temp_dir = context.create_temp_dir()
            assert temp_dir.is_dir()
            assert temp_dir in context._temp_dirs


class TestClaudeCodeBatch:
    """Test cases for ClaudeCodeBatch class."""
    
    @pytest.fixture
    def mock_claude_code(self):
        """Create a mock ClaudeCode instance."""
        mock = Mock(spec=ClaudeCode)
        mock.return_value = "Mocked response"
        return mock
    
    def test_init(self, mock_claude_code):
        """Test ClaudeCodeBatch initialization."""
        batch = ClaudeCodeBatch(mock_claude_code, max_parallel=2, fail_fast=True)
        
        assert batch.claude_code == mock_claude_code
        assert batch.max_parallel == 2
        assert batch.fail_fast is True
        assert len(batch._operations) == 0
    
    def test_add_operation(self, mock_claude_code):
        """Test add_operation method."""
        batch = ClaudeCodeBatch(mock_claude_code)
        
        result = batch.add_operation("Test prompt", path="./test", model="claude-opus-4-20250514")
        
        assert result is batch  # Should return self for chaining
        assert len(batch._operations) == 1
        assert batch._operations[0]["prompt"] == "Test prompt"
        assert batch._operations[0]["path"] == "./test"
        assert batch._operations[0]["model"] == "claude-opus-4-20250514"
    
    def test_execute_batch_sequential(self, mock_claude_code):
        """Test execute_batch with sequential execution."""
        batch = ClaudeCodeBatch(mock_claude_code, max_parallel=1)
        
        batch.add_operation("Prompt 1")
        batch.add_operation("Prompt 2")
        
        # Mock the claude_code call
        mock_claude_code.side_effect = ["Response 1", "Response 2"]
        
        results = batch.execute_batch()
        
        assert len(results) == 2
        assert results[0] == "Response 1"
        assert results[1] == "Response 2"
        assert mock_claude_code.call_count == 2
    
    def test_execute_batch_parallel(self, mock_claude_code):
        """Test execute_batch with parallel execution."""
        batch = ClaudeCodeBatch(mock_claude_code, max_parallel=2)
        
        batch.add_operation("Prompt 1")
        batch.add_operation("Prompt 2")
        
        # Mock the claude_code call
        mock_claude_code.side_effect = ["Response 1", "Response 2"]
        
        results = batch.execute_batch()
        
        assert len(results) == 2
        assert "Response 1" in results
        assert "Response 2" in results
        assert mock_claude_code.call_count == 2
    
    def test_execute_batch_with_failure(self, mock_claude_code):
        """Test execute_batch with failure and fail_fast."""
        batch = ClaudeCodeBatch(mock_claude_code, fail_fast=True)
        
        batch.add_operation("Prompt 1")
        batch.add_operation("Prompt 2")
        
        # Mock the claude_code call to fail on first operation
        mock_claude_code.side_effect = [Exception("Test error"), "Response 2"]
        
        results = batch.execute_batch()
        
        assert len(results) == 1  # Should stop after first failure
        assert isinstance(results[0], Exception)
        assert str(results[0]) == "Test error"
    
    def test_get_successful_results(self, mock_claude_code):
        """Test get_successful_results method."""
        batch = ClaudeCodeBatch(mock_claude_code)
        batch._results = ["Success 1", Exception("Error"), "Success 2"]
        
        successful = batch.get_successful_results()
        
        assert len(successful) == 2
        assert "Success 1" in successful
        assert "Success 2" in successful
    
    def test_get_failed_results(self, mock_claude_code):
        """Test get_failed_results method."""
        batch = ClaudeCodeBatch(mock_claude_code)
        error = Exception("Test error")
        batch._results = ["Success 1", error, "Success 2"]
        
        failed = batch.get_failed_results()
        
        assert len(failed) == 1
        assert failed[0] is error
    
    def test_clear(self, mock_claude_code):
        """Test clear method."""
        batch = ClaudeCodeBatch(mock_claude_code)
        batch.add_operation("Test")
        batch._results = ["Result"]
        
        result = batch.clear()
        
        assert result is batch
        assert len(batch._operations) == 0
        assert len(batch._results) == 0
    
    def test_len(self, mock_claude_code):
        """Test __len__ method."""
        batch = ClaudeCodeBatch(mock_claude_code)
        
        assert len(batch) == 0
        
        batch.add_operation("Test 1")
        batch.add_operation("Test 2")
        
        assert len(batch) == 2


class TestSessionInfo:
    """Test cases for SessionInfo class."""
    
    def test_init(self):
        """Test SessionInfo initialization."""
        import time
        current_time = time.time()
        path = Path.cwd()
        
        session = SessionInfo(
            session_id="test-123",
            path=path,
            created_at=current_time,
            last_used=current_time,
            model="claude-sonnet-4-20250514"
        )
        
        assert session.session_id == "test-123"
        assert session.path == path
        assert session.created_at == current_time
        assert session.last_used == current_time
        assert session.model == "claude-sonnet-4-20250514"
    
    def test_is_expired(self):
        """Test is_expired method."""
        import time
        current_time = time.time()
        
        # Recent session
        recent_session = SessionInfo(
            session_id="recent",
            path=Path.cwd(),
            created_at=current_time,
            last_used=current_time,
            model="claude-sonnet-4-20250514"
        )
        assert not recent_session.is_expired(max_age=3600)
        
        # Old session
        old_session = SessionInfo(
            session_id="old",
            path=Path.cwd(),
            created_at=current_time - 7200,
            last_used=current_time - 7200,
            model="claude-sonnet-4-20250514"
        )
        assert old_session.is_expired(max_age=3600)


# Integration tests (require actual Claude CLI)
class TestClaudeCodeIntegration:
    """Integration tests for ClaudeCode (require actual Claude CLI)."""
    
    @pytest.mark.integration
    @pytest.mark.cli
    def test_real_claude_cli_call(self):
        """Test with real Claude CLI (if available)."""
        pytest.skip("Requires actual Claude CLI installation and API key")
        
        # This would be enabled in a real test environment
        # claude_code = ClaudeCode(api_key="real-api-key")
        # result = claude_code("Say hello")
        # assert "hello" in result.lower()
    
    @pytest.mark.integration
    @pytest.mark.cli
    def test_real_file_operations(self):
        """Test file operations with real Claude CLI."""
        pytest.skip("Requires actual Claude CLI installation and API key")
        
        # This would test actual file creation/modification
        # with tempfile.TemporaryDirectory() as temp_dir:
        #     claude_code = ClaudeCode(api_key="real-api-key", default_path=temp_dir)
        #     result = claude_code("Create a hello.txt file with 'Hello World'")
        #     hello_file = Path(temp_dir) / "hello.txt"
        #     assert hello_file.exists()
        #     assert "Hello World" in hello_file.read_text() 