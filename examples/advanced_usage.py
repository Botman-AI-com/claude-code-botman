#!/usr/bin/env python3
"""
Advanced usage examples for claude-code-botman library.

This script demonstrates advanced features including:
- All CLI arguments from official documentation
- Permission management
- Session handling
- Tool configuration
- Environment variable configuration
"""

import os
import sys
from pathlib import Path

from claude_code_botman import ClaudeCode, ClaudeConfig, ClaudeCodeError


def demonstrate_permission_modes():
    """Demonstrate different permission modes."""
    print("🔒 Permission Modes Demo")
    print("=" * 30)
    
    # Test different permission modes
    permission_modes = ["prompt", "allow", "deny", "plan"]
    
    for mode in permission_modes:
        try:
            config = ClaudeConfig(
                model="claude-sonnet-4-20250514",
                permission_mode=mode,
                verbose=True
            )
            
            claude_code = ClaudeCode(config=config)
            print(f"✅ Permission mode '{mode}' configured successfully")
            
            # Example usage with this permission mode
            if mode == "allow":
                # This would allow all operations without prompting
                print(f"  - Mode '{mode}': All operations allowed without prompting")
            elif mode == "deny":
                # This would deny all operations without prompting
                print(f"  - Mode '{mode}': All operations denied without prompting")
            elif mode == "plan":
                # This would show a plan without executing
                print(f"  - Mode '{mode}': Show execution plan without running")
            else:
                # Default prompt mode
                print(f"  - Mode '{mode}': Prompt user for each operation")
                
        except Exception as e:
            print(f"❌ Error with permission mode '{mode}': {e}")
        
        print()


def demonstrate_tool_configuration():
    """Demonstrate tool allow/disallow configuration."""
    print("🛠️ Tool Configuration Demo")
    print("=" * 30)
    
    # Configure allowed and disallowed tools
    config = ClaudeConfig(
        model="claude-sonnet-4-20250514",
        allowed_tools=[
            "Bash(git log:*)",
            "Bash(git diff:*)",
            "Read"
        ],
        disallowed_tools=[
            "Bash(rm:*)",
            "Bash(sudo:*)",
            "Edit"
        ],
        permission_mode="prompt",
        verbose=True
    )
    
    claude_code = ClaudeCode(config=config)
    
    print("✅ Tool configuration:")
    print(f"  Allowed tools: {config.allowed_tools}")
    print(f"  Disallowed tools: {config.disallowed_tools}")
    print()
    
    # Test with a safe git operation
    try:
        result = claude_code(
            "Show me the git status of this repository",
            path="./"
        )
        print(f"Git status result: {result}")
    except ClaudeCodeError as e:
        print(f"Expected error (tool restrictions): {e}")
    print()


def demonstrate_directory_configuration():
    """Demonstrate additional directory configuration."""
    print("📁 Directory Configuration Demo")
    print("=" * 30)
    
    # Create some test directories
    test_dirs = ["./test_dir1", "./test_dir2"]
    for dir_path in test_dirs:
        Path(dir_path).mkdir(exist_ok=True)
        # Create a test file in each directory
        (Path(dir_path) / "test.txt").write_text(f"Test content in {dir_path}")
    
    try:
        config = ClaudeConfig(
            model="claude-sonnet-4-20250514",
            add_dir=test_dirs,
            permission_mode="allow",  # Allow operations for demo
            verbose=True
        )
        
        claude_code = ClaudeCode(config=config)
        
        print("✅ Additional directories configured:")
        for dir_path in config.add_dir:
            print(f"  - {dir_path}")
        
        # Test accessing files in additional directories
        result = claude_code(
            "List the contents of the test directories I've given you access to",
            path="./"
        )
        print(f"Directory listing result: {result}")
        
    except Exception as e:
        print(f"❌ Error with directory configuration: {e}")
    finally:
        # Clean up test directories
        import shutil
        for dir_path in test_dirs:
            if Path(dir_path).exists():
                shutil.rmtree(dir_path)
    print()


def demonstrate_output_formats():
    """Demonstrate different output formats."""
    print("📄 Output Format Demo")
    print("=" * 30)
    
    formats = ["text", "json", "stream-json"]
    
    for fmt in formats:
        try:
            config = ClaudeConfig(
                model="claude-sonnet-4-20250514",
                output_format=fmt,
                input_format="text",
                verbose=True
            )
            
            claude_code = ClaudeCode(config=config)
            
            print(f"✅ Output format '{fmt}' configured")
            
            # Simple test
            result = claude_code("Say hello in a brief way")
            print(f"  Result ({fmt}): {result[:100]}...")
            
        except Exception as e:
            print(f"❌ Error with format '{fmt}': {e}")
        
        print()


def demonstrate_session_management():
    """Demonstrate session continuation and resumption."""
    print("💬 Session Management Demo")
    print("=" * 30)
    
    try:
        claude_code = ClaudeCode(
            model="claude-sonnet-4-20250514",
            verbose=True,
            save_sessions=True
        )
        
        # Start a conversation
        print("Starting initial conversation...")
        result1 = claude_code("My name is Alice. Remember this.")
        print(f"Initial: {result1}")
        
        # Continue the conversation
        print("\nContinuing conversation...")
        result2 = claude_code.continue_conversation("What is my name?")
        print(f"Continued: {result2}")
        
        # Get session information
        current_session = claude_code.get_current_session()
        if current_session:
            print(f"\nCurrent session: {current_session.session_id}")
            
            # Resume the session explicitly
            print("Resuming session explicitly...")
            result3 = claude_code.resume_session(
                current_session.session_id,
                "What did I tell you about my name earlier?"
            )
            print(f"Resumed: {result3}")
        
        # Show all sessions
        sessions = claude_code.get_sessions()
        print(f"\nTotal sessions: {len(sessions)}")
        
    except Exception as e:
        print(f"❌ Session management error: {e}")
    
    print()


def demonstrate_environment_config():
    """Demonstrate environment variable configuration."""
    print("🌍 Environment Configuration Demo")
    print("=" * 30)
    
    # Set some environment variables
    os.environ["CLAUDE_MODEL"] = "claude-sonnet-4-20250514"
    os.environ["CLAUDE_VERBOSE"] = "true"
    os.environ["CLAUDE_PERMISSION_MODE"] = "allow"
    os.environ["CLAUDE_OUTPUT_FORMAT"] = "json"
    os.environ["CLAUDE_ALLOWED_TOOLS"] = "Read,Bash(git log:*)"
    os.environ["CLAUDE_MAX_TURNS"] = "5"
    
    try:
        from claude_code_botman.config import load_config_from_env
        
        config = load_config_from_env()
        
        print("✅ Configuration loaded from environment:")
        print(f"  Model: {config.model}")
        print(f"  Verbose: {config.verbose}")
        print(f"  Permission mode: {config.permission_mode}")
        print(f"  Output format: {config.output_format}")
        print(f"  Allowed tools: {config.allowed_tools}")
        print(f"  Max turns: {config.max_turns}")
        
        claude_code = ClaudeCode(config=config)
        print("✅ ClaudeCode initialized with environment config")
        
    except Exception as e:
        print(f"❌ Environment config error: {e}")
    
    print()


def demonstrate_dangerous_mode():
    """Demonstrate dangerous skip permissions mode."""
    print("⚠️ Dangerous Mode Demo")
    print("=" * 30)
    
    print("WARNING: This mode skips all permission prompts!")
    print("Only use this in trusted environments.")
    
    try:
        config = ClaudeConfig(
            model="claude-sonnet-4-20250514",
            dangerously_skip_permissions=True,
            verbose=True
        )
        
        claude_code = ClaudeCode(config=config)
        
        print("✅ Dangerous mode configured (permissions will be skipped)")
        print("  This should only be used in controlled environments")
        
        # Test with a safe operation
        result = claude_code("Echo 'Hello from dangerous mode'")
        print(f"  Result: {result}")
        
    except Exception as e:
        print(f"❌ Dangerous mode error: {e}")
    
    print()


def demonstrate_comprehensive_config():
    """Demonstrate a comprehensive configuration with all options."""
    print("🎯 Comprehensive Configuration Demo")
    print("=" * 40)
    
    try:
        config = ClaudeConfig(
            # Core settings
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            default_path="./",
            
            # Operational settings
            timeout=120,
            max_turns=8,
            output_format="json",
            input_format="text",
            verbose=True,
            
            # Advanced settings
            auto_continue=False,
            save_sessions=True,
            
            # CLI-specific settings
            allowed_tools=["Read", "Bash(git log:*)"],
            disallowed_tools=["Bash(rm:*)", "Bash(sudo:*)"],
            permission_mode="prompt",
            permission_prompt_tool=None,
            dangerously_skip_permissions=False,
            add_dir=[],
            
            # Environment settings
            environment_variables={
                "CUSTOM_VAR": "custom_value"
            }
        )
        
        print("✅ Comprehensive configuration created:")
        config_dict = config.to_dict()
        for key, value in config_dict.items():
            print(f"  {key}: {value}")
        
        # Show CLI arguments that would be generated
        cli_args = config.to_cli_args()
        print(f"\n🔧 Generated CLI arguments:")
        print(f"  {' '.join(cli_args)}")
        
        # Initialize ClaudeCode with this config
        claude_code = ClaudeCode(config=config)
        print(f"\n✅ ClaudeCode initialized successfully")
        print(f"  Model: {claude_code.config.model}")
        print(f"  Default path: {claude_code.config.default_path}")
        print(f"  Permission mode: {claude_code.config.permission_mode}")
        
    except Exception as e:
        print(f"❌ Comprehensive config error: {e}")
    
    print()


def main():
    """Main function to run all advanced usage examples."""
    print("🚀 Claude Code Botman - Advanced Usage Examples")
    print("=" * 50)
    
    # Check if API key is available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("\nPlease set your API key:")
        print("export ANTHROPIC_API_KEY='sk-ant-api03-...'")
        return 1
    
    try:
        # Run all demonstrations
        demonstrate_permission_modes()
        demonstrate_tool_configuration()
        demonstrate_directory_configuration()
        demonstrate_output_formats()
        demonstrate_session_management()
        demonstrate_environment_config()
        demonstrate_dangerous_mode()
        demonstrate_comprehensive_config()
        
        print("✅ All advanced usage examples completed successfully!")
        print("\nKey features demonstrated:")
        print("  ✓ Permission modes (prompt, allow, deny, plan)")
        print("  ✓ Tool allow/disallow lists")
        print("  ✓ Additional directory access")
        print("  ✓ Output format options (text, json, stream-json)")
        print("  ✓ Input format options (text, stream-json)")
        print("  ✓ Session continuation and resumption")
        print("  ✓ Environment variable configuration")
        print("  ✓ Dangerous permission skipping")
        print("  ✓ Comprehensive configuration")
        
        return 0
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 