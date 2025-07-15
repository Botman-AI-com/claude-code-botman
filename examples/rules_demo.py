#!/usr/bin/env python3
"""
Simple demonstration of the new rules parameter in claude-code-botman.

This script shows how to use CLAUDE.md files to provide instructions
and rules for Claude Code behavior.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import claude_code_botman
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_code_botman import ClaudeCode
from claude_code_botman.exceptions import ClaudeCodePathError


def main():
    """Main function demonstrating rules functionality."""
    
    print("🚀 Claude Code Botman - Rules Demo")
    print("=" * 40)
    
    # Check if API key is available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("This demo will show the initialization without making API calls")
        print()
    
    # Create a sample CLAUDE.md file
    claude_md_content = """# Project Coding Rules

## Code Style Guidelines
- Use clear, descriptive variable names
- Add docstrings to all functions
- Follow PEP 8 style guidelines
- Keep functions small and focused

## File Organization
- Put utility functions in utils.py
- Use main() function with if __name__ == "__main__" guard
- Group related functions together

## Error Handling
- Always use try-catch blocks for risky operations
- Provide meaningful error messages
- Log errors appropriately

## Documentation
- Write clear comments for complex logic
- Include usage examples in docstrings
- Document all function parameters and return values
"""
    
    # Write the rules file
    rules_file = Path("./demo_rules.md")
    print(f"📝 Creating rules file: {rules_file}")
    rules_file.write_text(claude_md_content)
    print(f"✅ Rules file created with {len(claude_md_content)} characters")
    print()
    
    try:
        # Example 1: Basic usage with rules
        print("📋 Example 1: Initialize ClaudeCode with rules")
        print("-" * 45)
        
        claude_with_rules = ClaudeCode(
            model="claude-sonnet-4-20250514",
            api_key=api_key,
            rules=rules_file,
            verbose=True
        )
        
        print("✅ ClaudeCode initialized successfully with rules!")
        print(f"   Model: {claude_with_rules.config.model}")
        print(f"   Rules loaded from: {rules_file}")
        print(f"   System prompt configured: {'Yes' if claude_with_rules.config.append_system_prompt else 'No'}")
        print()
        
        # Example 2: Using relative path
        print("📋 Example 2: Using relative path for rules")
        print("-" * 45)
        
        claude_relative = ClaudeCode(
            model="claude-haiku-3-5-20241022",
            api_key=api_key,
            rules="./demo_rules.md"  # Relative path
        )
        
        print("✅ ClaudeCode initialized with relative path rules!")
        print(f"   Model: {claude_relative.config.model}")
        print()
        
        # Example 3: Error handling for missing rules
        print("📋 Example 3: Error handling for missing rules file")
        print("-" * 45)
        
        try:
            claude_bad = ClaudeCode(
                model="claude-sonnet-4-20250514",
                api_key=api_key,
                rules="./nonexistent_rules.md"
            )
        except ClaudeCodePathError as e:
            print(f"✅ Correctly caught error for missing file:")
            print(f"   Error: {e}")
        print()
        
        # Example 4: Making an actual API call (if API key is available)
        if api_key:
            print("📋 Example 4: Making API call with rules applied")
            print("-" * 45)
            
            try:
                result = claude_with_rules(
                    "Create a simple Python function that adds two numbers"
                )
                print("✅ API call successful!")
                print("📤 Response preview:")
                print(f"   {result[:200]}...")
                if len(result) > 200:
                    print(f"   [... {len(result) - 200} more characters]")
                print()
                
            except Exception as e:
                print(f"⚠️  API call failed: {e}")
                print("   This is normal if you don't have a valid API key or credits")
                print()
        else:
            print("📋 Example 4: Skipped (no API key)")
            print("-" * 45)
            print("   Set ANTHROPIC_API_KEY to test actual API calls")
            print()
        
        print("🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        return 1
    
    finally:
        # Clean up the demo rules file
        if rules_file.exists():
            rules_file.unlink()
            print(f"🧹 Cleaned up demo file: {rules_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 