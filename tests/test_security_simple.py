"""
test_security_simple.py: Simple test suite for security improvements
Tests core security functionality without heavy dependencies
"""
import sys
import os
import re
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_gitignore_conceals_credentials():
    """Test that .gitignore properly conceals admin credentials"""
    gitignore_path = os.path.join(os.path.dirname(__file__), '..', '.gitignore')
    
    assert os.path.exists(gitignore_path), ".gitignore file should exist"
    
    with open(gitignore_path, 'r') as f:
        gitignore_content = f.read()
    
    # Check that sensitive files are in gitignore
    assert '.guardian_master_password.txt' in gitignore_content, \
        ".guardian_master_password.txt should be in .gitignore"
    assert '.guardian_secret' in gitignore_content, \
        ".guardian_secret should be in .gitignore"
    assert '.guardian_admin' in gitignore_content, \
        ".guardian_admin should be in .gitignore"
    
    # Check that comments are present
    assert 'Admin credentials' in gitignore_content or 'admin' in gitignore_content.lower(), \
        ".gitignore should have comments about admin credentials"
    
    print("✅ .gitignore properly conceals admin credentials")
    return True


def test_credential_files_not_in_git():
    """Test that credential files are not tracked by git"""
    try:
        # Check git ls-files for sensitive files
        result = subprocess.run(
            ['git', 'ls-files'],
            cwd=os.path.join(os.path.dirname(__file__), '..'),
            capture_output=True,
            text=True,
            timeout=10
        )
        
        tracked_files = result.stdout
        
        # These files should NOT be in git tracking
        assert '.guardian_master_password.txt' not in tracked_files, \
            ".guardian_master_password.txt should not be tracked by git"
        assert '.guardian_secret' not in tracked_files, \
            ".guardian_secret should not be tracked by git"
        assert '.guardian_admin' not in tracked_files, \
            ".guardian_admin should not be tracked by git"
        
        print("✅ Credential files are not tracked by git")
        return True
    except Exception as e:
        print(f"⚠️  Could not check git status: {e}")
        return False


def test_gitignore_no_corruption():
    """Test that .gitignore has no null bytes or corruption"""
    gitignore_path = os.path.join(os.path.dirname(__file__), '..', '.gitignore')
    
    with open(gitignore_path, 'rb') as f:
        content = f.read()
    
    # Check for null bytes
    assert b'\x00' not in content, ".gitignore should not contain null bytes"
    
    # Check it's valid UTF-8
    try:
        content.decode('utf-8')
    except UnicodeDecodeError:
        raise AssertionError(".gitignore should be valid UTF-8")
    
    print("✅ .gitignore has no corruption or null bytes")
    return True


def test_input_validation_patterns():
    """Test input validation regex patterns"""
    
    # Test agent ID pattern
    agent_id_pattern = r'^[a-zA-Z0-9_-]+$'
    
    # Valid agent IDs
    valid_ids = ["learning_agent", "behavioral-analytics", "dmer_monitor_123"]
    for agent_id in valid_ids:
        assert re.match(agent_id_pattern, agent_id), \
            f"Valid agent ID '{agent_id}' should match pattern"
    
    # Invalid agent IDs
    invalid_ids = ["agent@123", "agent id", "agent/path", "agent;cmd"]
    for agent_id in invalid_ids:
        assert not re.match(agent_id_pattern, agent_id), \
            f"Invalid agent ID '{agent_id}' should not match pattern"
    
    # Test username pattern
    username_pattern = r'^[a-zA-Z0-9_]{3,32}$'
    
    # Valid usernames
    valid_usernames = ["admin", "user123", "test_user", "AdminUser99"]
    for username in valid_usernames:
        assert re.match(username_pattern, username), \
            f"Valid username '{username}' should match pattern"
    
    # Invalid usernames
    invalid_usernames = ["ab", "a"*33, "user@admin", "user name", "user;DROP"]
    for username in invalid_usernames:
        assert not re.match(username_pattern, username), \
            f"Invalid username '{username}' should not match pattern"
    
    print("✅ Input validation patterns work correctly")
    return True


def test_api_security_enhancements_present():
    """Test that API security enhancements are present in code"""
    api_server_path = os.path.join(os.path.dirname(__file__), '..', 'api_server.py')
    
    assert os.path.exists(api_server_path), "api_server.py should exist"
    
    with open(api_server_path, 'r') as f:
        api_content = f.read()
    
    # Check for rate limiting
    assert 'RateLimitMiddleware' in api_content, \
        "RateLimitMiddleware should be present"
    
    # Check for security headers
    assert 'SecurityHeadersMiddleware' in api_content, \
        "SecurityHeadersMiddleware should be present"
    
    # Check for input validator
    assert 'InputValidator' in api_content, \
        "InputValidator should be present"
    
    # Check for sanitization
    assert 'sanitize_string' in api_content or 'validate_agent_id' in api_content, \
        "Input sanitization methods should be present"
    
    # Check for security headers implementation
    assert 'X-Frame-Options' in api_content or 'X-Content-Type-Options' in api_content, \
        "Security headers should be implemented"
    
    print("✅ API security enhancements are present in code")
    return True


def test_security_manager_enhancements():
    """Test that security manager has enhancements"""
    security_manager_path = os.path.join(os.path.dirname(__file__), '..', 'security_manager.py')
    
    assert os.path.exists(security_manager_path), "security_manager.py should exist"
    
    with open(security_manager_path, 'r') as f:
        security_content = f.read()
    
    # Check for session cleanup
    assert 'cleanup_expired_sessions' in security_content, \
        "Session cleanup method should be present"
    
    # Check for security features
    assert 'token_expiry' in security_content or 'expiry' in security_content, \
        "Token expiry functionality should be present"
    
    print("✅ Security manager enhancements are present")
    return True


def test_readme_security_documentation():
    """Test that README has security documentation"""
    readme_path = os.path.join(os.path.dirname(__file__), '..', 'README.md')
    
    assert os.path.exists(readme_path), "README.md should exist"
    
    with open(readme_path, 'r') as f:
        readme_content = f.read()
    
    # Check for security notice
    assert 'Security' in readme_content or 'security' in readme_content, \
        "README should contain security documentation"
    
    # Check for mention of concealed files
    assert '.guardian_master_password.txt' in readme_content or \
           'guardian_master_password' in readme_content, \
        "README should mention concealed credential files"
    
    # Check for security best practices
    assert 'rate limit' in readme_content.lower() or 'authentication' in readme_content.lower(), \
        "README should mention security features"
    
    print("✅ README contains security documentation")
    return True


def run_all_tests():
    """Run all security tests"""
    tests = [
        ("Gitignore conceals credentials", test_gitignore_conceals_credentials),
        ("Credential files not in git", test_credential_files_not_in_git),
        ("Gitignore has no corruption", test_gitignore_no_corruption),
        ("Input validation patterns", test_input_validation_patterns),
        ("API security enhancements", test_api_security_enhancements_present),
        ("Security manager enhancements", test_security_manager_enhancements),
        ("README security documentation", test_readme_security_documentation),
    ]
    
    print("\n" + "="*60)
    print("Running Security Enhancement Tests")
    print("="*60 + "\n")
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\nTesting: {test_name}")
            print("-" * 40)
            result = test_func()
            if result is not False:  # Accept True or None as pass
                passed += 1
                print(f"✓ PASSED: {test_name}\n")
            else:
                failed += 1
                print(f"✗ FAILED: {test_name}\n")
        except AssertionError as e:
            failed += 1
            print(f"✗ FAILED: {test_name}")
            print(f"  Error: {e}\n")
        except Exception as e:
            failed += 1
            print(f"✗ ERROR: {test_name}")
            print(f"  Exception: {e}\n")
    
    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
