#!/usr/bin/env python3
"""
Main demonstration script for claude-code-botman library.

This script demonstrates various usage patterns including:
- Basic usage without rules
- Using CLAUDE.md rules files
- Different models
- Various configurations
- Error handling
"""

import os
import sys
import time
from pathlib import Path
from claude_code_botman import ClaudeCode, ClaudeConfig
from claude_code_botman.exceptions import ClaudeCodeError, ClaudeCodePathError


def create_sample_rules():
    """Create a sample CLAUDE.md rules file for testing."""
    rules_content = """# Claude Code Test Rules

## Code Style Guidelines
- Use descriptive variable names
- Add comprehensive docstrings to all functions
- Follow PEP 8 style guidelines
- Maximum line length: 88 characters
- Use type hints for function parameters

## File Organization
- Put utility functions in utils.py
- Use main() function with if __name__ == "__main__" guard
- Group related functions together

## Error Handling Standards
- Always use try-catch blocks for risky operations
- Provide meaningful error messages with context
- Use specific exception types

## Documentation Requirements
- Write clear comments for complex logic
- Include usage examples in docstrings
- Document all function parameters and return values

## Testing Instructions
- Write unit tests for all new functionality
- Include both positive and negative test cases
- Use descriptive test names
"""
    
    rules_file = Path("./test_rules.md")
    rules_file.write_text(rules_content)
    return rules_file


def test_execution_1_basic():
    """Test 1: Basic usage without rules."""
    print("🔧 Test 1: Basic usage without rules")
    print("-" * 50)
    
    try:
        claude = ClaudeCode(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            verbose=False  # Reduce verbose output for cleaner testing
        )
        
        result = claude("Create a simple Python function that calculates the factorial of a number")
        
        # Extract just the clean response without debug info
        clean_result = extract_clean_response(result)
        
        print("✅ Test 1 completed successfully")
        print(f"📤 Response length: {len(clean_result)} characters")
        print(f"📄 Preview: {clean_result[:150]}...")
        return True
        
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        return False


def test_execution_2_with_rules():
    """Test 2: Using CLAUDE.md rules file."""
    print("\n🔧 Test 2: Using CLAUDE.md rules file")
    print("-" * 50)
    
    rules_file = None
    try:
        # Create sample rules file
        rules_file = create_sample_rules()
        print(f"📋 Created rules file: {rules_file}")
        
        claude = ClaudeCode(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            rules=rules_file,
            verbose=False  # Reduce verbose output
        )
        
        result = claude("Create a Python class for managing a simple todo list")
        
        # Extract clean response
        clean_result = extract_clean_response(result)
        
        print("✅ Test 2 completed successfully")
        print(f"📤 Response length: {len(clean_result)} characters")
        print(f"📄 Preview: {clean_result[:150]}...")
        return True
        
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        return False
    finally:
        # Clean up rules file
        if rules_file and rules_file.exists():
            rules_file.unlink()
            print(f"🧹 Cleaned up: {rules_file}")


def test_execution_3_different_model():
    """Test 3: Using different model (Haiku for speed)."""
    print("\n🔧 Test 3: Using different model (Haiku)")
    print("-" * 50)
    
    try:
        claude = ClaudeCode(
            model="claude-3-5-haiku-20241022",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            verbose=False
        )
        
        result = claude("Write a simple Python script that prints 'Hello, World!' with proper structure")
        
        # Extract clean response
        clean_result = extract_clean_response(result)
        
        print("✅ Test 3 completed successfully")
        print(f"📤 Response length: {len(clean_result)} characters")
        print(f"📄 Preview: {clean_result[:150]}...")
        return True
        
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        return False


def test_execution_4_with_config():
    """Test 4: Using ClaudeConfig with specific settings."""
    print("\n🔧 Test 4: Using ClaudeConfig with specific settings")
    print("-" * 50)
    
    try:
        config = ClaudeConfig(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            output_format="text",
            verbose=False,  # Reduce verbosity
            max_turns=5,
            append_system_prompt="Always include error handling in your code examples and provide clear explanations."
        )
        
        claude = ClaudeCode(config=config)
        
        result = claude("Create a simple Python function that validates an email address")
        
        # Extract clean response
        clean_result = extract_clean_response(result)
        
        print("✅ Test 4 completed successfully")
        print(f"📤 Response length: {len(clean_result)} characters")
        print(f"📄 Preview: {clean_result[:150]}...")
        return True
        
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        return False


def test_execution_5_session_continuation():
    """Test 5: Session continuation."""
    print("\n🔧 Test 5: Session continuation")
    print("-" * 50)
    
    try:
        claude = ClaudeCode(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            verbose=False,
            save_sessions=True
        )
        
        # First call
        result1 = claude("Create a simple Python class called Calculator")
        clean_result1 = extract_clean_response(result1)
        print("✅ First call completed")
        print(f"📤 Response 1 length: {len(clean_result1)} characters")
        
        # Continue the conversation
        result2 = claude.continue_conversation("Now add a method to this calculator that can handle division by zero")
        clean_result2 = extract_clean_response(result2)
        print("✅ Test 5 completed successfully")
        print(f"📤 Response 2 length: {len(clean_result2)} characters")
        print(f"📄 Preview: {clean_result2[:150]}...")
        return True
        
    except Exception as e:
        print(f"❌ Test 5 failed: {e}")
        return False


def test_execution_6_error_handling():
    """Test 6: Error handling with invalid rules file."""
    print("\n🔧 Test 6: Error handling with invalid rules file")
    print("-" * 50)
    
    try:
        # Try to use a non-existent rules file
        claude = ClaudeCode(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            rules="./nonexistent_rules.md"
        )
        
        print("❌ Test 6 should have failed but didn't")
        return False
        
    except ClaudeCodePathError as e:
        print("✅ Test 6 completed successfully - correctly caught path error")
        print(f"📋 Expected error: {e}")
        return True
    except Exception as e:
        print(f"❌ Test 6 failed with unexpected error: {e}")
        return False


def extract_clean_response(raw_response: str) -> str:
    """Extract clean response by removing debug output and keeping only the actual content."""
    lines = raw_response.split('\n')
    clean_lines = []
    
    for line in lines:
        # Skip debug lines
        if line.strip().startswith('[DEBUG]'):
            continue
        # Skip empty lines at the beginning
        if not line.strip() and not clean_lines:
            continue
        clean_lines.append(line)
    
    # Join and clean up
    clean_response = '\n'.join(clean_lines).strip()
    return clean_response


def main():
    """Main function to run all tests."""
    print("🚀 Claude Code Botman - Comprehensive Test Suite")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  Warning: ANTHROPIC_API_KEY not set")
        print("   Some tests may fail without a valid API key")
        print("   Set your API key: export ANTHROPIC_API_KEY='sk-ant-...'")
        print()
    
    # Run all tests
    tests = [
        test_execution_1_basic,
        test_execution_2_with_rules,
        test_execution_3_different_model,
        test_execution_4_with_config,
        test_execution_5_session_continuation,
        test_execution_6_error_handling
    ]
    
    results = []
    start_time = time.time()
    
    for i, test_func in enumerate(tests, 1):
        test_start = time.time()
        try:
            success = test_func()
            results.append(success)
        except Exception as e:
            print(f"❌ Test {i} crashed: {e}")
            results.append(False)
        
        test_duration = time.time() - test_start
        print(f"⏱️  Test {i} duration: {test_duration:.2f}s")
        
        # Add a small delay between tests
        if i < len(tests):
            time.sleep(1)
    
    # Summary
    total_duration = time.time() - start_time
    successful_tests = sum(results)
    total_tests = len(results)
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"✅ Successful tests: {successful_tests}/{total_tests}")
    print(f"❌ Failed tests: {total_tests - successful_tests}/{total_tests}")
    print(f"⏱️  Total duration: {total_duration:.2f}s")
    print(f"🎯 Success rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests == total_tests:
        print("\n🎉 All tests passed! Claude Code Botman is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - successful_tests} test(s) failed. Check your setup.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 