# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation with @claude-code-botman.mdc guide
- Complete CLI argument support with all official Claude Code features
- Enhanced MCP (Model Context Protocol) integration
- Advanced permission management system
- Session management with continuation and resumption
- Multiple output format support (text, JSON, stream-JSON)
- Environment variable configuration system
- Async support for non-blocking operations
- Batch processing capabilities
- Context manager support
- Comprehensive error handling hierarchy

## [0.1.0] - 2025-01-27

### Added
- **Core Features**
  - `ClaudeCode` class for programmatic CLI interaction
  - Support for all Claude models (Opus, Sonnet, Haiku)
  - Subprocess management with timeout and error handling
  - Path validation and security checks
  - API key management and authentication

- **Configuration Management**
  - `ClaudeConfig` class with comprehensive settings
  - Support for configuration files (JSON)
  - Environment variable integration
  - Model aliases and validation
  - CLI argument generation

- **Advanced Features**
  - `ClaudeCodeContext` context manager
  - `ClaudeCodeBatch` for parallel operations
  - Session tracking and resumption
  - Conversation continuation
  - Response parsing and structured output

- **MCP Integration**
  - MCP configuration file support
  - Strict MCP configuration mode
  - IDE integration with automatic connection
  - Fallback model support for overloaded primary models
  - System prompt appending capabilities

- **Permission Management**
  - Fine-grained tool permission control
  - Allowed/disallowed tools configuration
  - Dangerous permission skipping with warnings
  - Permission prompt tool integration
  - Security-first design patterns

- **Session Management**
  - Persistent session storage
  - Session continuation functionality
  - Session resumption by ID
  - Auto-continue conversation mode
  - Session cleanup and management

- **Response Handling**
  - `ClaudeResponse` class with parsed content
  - File creation/modification tracking
  - Command execution tracking
  - Error and warning extraction
  - Session ID extraction
  - Multiple output format support

- **Error Handling**
  - Comprehensive exception hierarchy
  - Specific error types for different scenarios
  - Detailed error messages with context
  - Graceful error recovery
  - Path validation errors
  - Configuration validation errors

- **Async Support**
  - Async/await compatible methods
  - Non-blocking operations
  - Concurrent execution support
  - Async session management
  - Parallel operation processing

- **Utilities**
  - CLI validation and version checking
  - Path sanitization and safety checks
  - Command argument formatting
  - System information gathering
  - Execution timing and retry decorators

- **Testing**
  - Comprehensive unit test suite
  - Integration tests for CLI interaction
  - Mock-based testing for reliability
  - High test coverage (>80%)
  - Permission testing framework

- **Documentation**
  - Comprehensive README with examples
  - API reference documentation
  - Usage examples (basic and advanced)
  - Configuration guides
  - Development setup instructions
  - @claude-code-botman.mdc comprehensive guide

- **Development Tools**
  - Modern Python packaging (pyproject.toml)
  - Pre-commit hooks configuration
  - Code formatting (Black, isort)
  - Type checking (mypy)
  - Linting (flake8, bandit)
  - Continuous integration setup

### Dependencies
- Python 3.8+ support
- typing-extensions for older Python versions
- No additional runtime dependencies

### Development Dependencies
- pytest for testing
- black for code formatting
- mypy for type checking
- flake8 for linting
- bandit for security scanning
- sphinx for documentation

## [0.0.1] - 2025-01-XX

### Added
- Initial project structure
- Basic package configuration
- Development environment setup

---

## Types of Changes

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes 