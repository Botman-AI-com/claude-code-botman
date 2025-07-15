#!/usr/bin/env python3
"""
Basic usage examples for claude-code-botman.

This script demonstrates the most common use cases for the claude-code-botman
library, including initialization, basic operations, and error handling.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import claude_code_botman
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_code_botman import ClaudeCode, ClaudeCodeError


def main():
    """Main function demonstrating basic usage."""
    
    # Check if API key is available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set your API key:")
        print("export ANTHROPIC_API_KEY='sk-ant-api03-...'")
        return 1
    
    print("🚀 Claude Code Botman - Basic Usage Examples")
    print("=" * 50)
    
    try:
        # Initialize ClaudeCode with basic configuration
        claude_code = ClaudeCode(
            model="claude-sonnet-4-20250514",
            api_key=api_key,
            default_path="./",
            timeout=60,
            verbose=True
        )
        
        print("✅ ClaudeCode initialized successfully")
        print(f"Model: {claude_code.config.model}")
        print(f"Default path: {claude_code.config.default_path}")
        print()
        
        # Example 1: Simple file creation
        print("📝 Example 1: Creating a simple Python file")
        print("-" * 40)
        
        result = claude_code("""
        Create a Python file called 'hello.py' that:
        1. Prints "Hello, World!"
        2. Has a main function
        3. Includes proper if __name__ == "__main__" guard
        """)
        
        print(f"Response: {result}")
        print()  # Simplified - the response parsing happens internally
        print()
        
        # Example 2: Working with specific directory
        print("📁 Example 2: Working in specific directory")
        print("-" * 40)
        
        # Create a temporary directory for this example
        temp_dir = Path("./temp_example")
        temp_dir.mkdir(exist_ok=True)
        
        result = claude_code(
            "Create a simple README.md file with project description",
            path=temp_dir
        )
        
        print(f"Response: {result}")
        print(f"Working directory: {temp_dir}")
        print()
        
        # Example 3: Using different models
        print("🤖 Example 3: Using different models")
        print("-" * 40)
        
        # Create instance with Haiku model (faster)
        claude_haiku = claude_code.set_config(model="claude-haiku-3-5-20241022")
        
        result = claude_haiku("Create a simple JSON configuration file")
        
        print(f"Response from Haiku: {result}")
        print()
        
        # Example 4: Using rules from CLAUDE.md file
        print("📋 Example 4: Using rules from CLAUDE.md file")
        print("-" * 40)
        
        # Create a sample CLAUDE.md file
        claude_md_content = """# Project Rules and Configuration

## Code Style Preferences
- Use clear, descriptive variable names
- Add docstrings to all functions
- Follow PEP 8 style guidelines
- Maximum line length: 88 characters

## File Organization
- Put all utility functions in utils.py
- Use main() function with if __name__ == "__main__" guard
- Include proper imports at the top

## Specific Instructions
- Always add error handling with try-catch blocks
- Write code that is self-documenting
- Prefer readability over clever tricks
"""
        
        # Write the rules file
        rules_file = Path("./example_claude.md")
        rules_file.write_text(claude_md_content)
        
        try:
            # Initialize ClaudeCode with rules
            claude_with_rules = ClaudeCode(
                model="claude-sonnet-4-20250514",
                api_key=api_key,
                rules="./example_claude.md",
                verbose=True
            )
            
            result = claude_with_rules("Create a Python utility function that calculates the factorial of a number")
            print(f"Response with rules applied: {result}")
            print()
            
        finally:
            # Clean up the rules file
            if rules_file.exists():
                rules_file.unlink()
        
        # Example 5: Continuing conversations
        print("💬 Example 5: Continuing conversations")
        print("-" * 40)
        
        # First message
        result1 = claude_code("Create a Python class called 'Calculator'")
        print(f"First response: {result1}")
        
        # Continue the conversation
        result2 = claude_code.continue_conversation("Add methods for basic math operations")
        print(f"Continued response: {result2}")
        print()
        
        # Example 6: Error handling
        print("⚠️ Example 6: Error handling")
        print("-" * 40)
        
        try:
            # This might fail if the path doesn't exist
            result = claude_code("Create a file", path="/nonexistent/path")
        except ClaudeCodeError as e:
            print(f"Caught expected error: {e}")
        print()
        
        # Example 7: Getting system information
        print("ℹ️ Example 7: System information")
        print("-" * 40)
        
        sessions = claude_code.get_sessions()
        print(f"Active sessions: {len(sessions)}")
        
        current_session = claude_code.get_current_session()
        if current_session:
            print(f"Current session ID: {current_session.session_id}")
            print(f"Session path: {current_session.path}")
        
        print()
        
        # Cleanup
        print("🧹 Cleaning up...")
        claude_code.cleanup_expired_sessions()
        
        # Remove temporary directory
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)
        
        print("✅ Examples completed successfully!")
        return 0
        
    except ClaudeCodeError as e:
        print(f"❌ Claude Code error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 