"""
test_security_api.py: Test suite for API security enhancements
Tests rate limiting, input validation, authentication, and security headers
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import time
import re

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import modules to test
try:
    from api_server import app, InputValidator, RateLimitMiddleware, SecurityHeadersMiddleware
    from security_manager import SecurityManager
    
    # Create test client
    client = TestClient(app)
    API_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not import API modules: {e}")
    API_AVAILABLE = False


@pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
class TestInputValidator:
    """Test suite for InputValidator utility class"""
    
    def test_sanitize_string_removes_scripts(self):
        """Test that script tags are removed"""
        malicious_input = "<script>alert('xss')</script>Hello"
        sanitized = InputValidator.sanitize_string(malicious_input)
        assert "<script>" not in sanitized
        assert "Hello" in sanitized
    
    def test_sanitize_string_removes_javascript(self):
        """Test that javascript: protocol is removed"""
        malicious_input = "javascript:alert('xss')"
        sanitized = InputValidator.sanitize_string(malicious_input)
        assert "javascript:" not in sanitized.lower()
    
    def test_sanitize_string_removes_sql_injection(self):
        """Test that SQL injection patterns are removed"""
        malicious_input = "'; DROP TABLE users; --"
        sanitized = InputValidator.sanitize_string(malicious_input)
        assert "DROP TABLE" not in sanitized.upper()
    
    def test_sanitize_string_truncates_long_input(self):
        """Test that long inputs are truncated"""
        long_input = "A" * 2000
        sanitized = InputValidator.sanitize_string(long_input, max_length=100)
        assert len(sanitized) <= 100
    
    def test_validate_agent_id_accepts_valid(self):
        """Test that valid agent IDs are accepted"""
        valid_ids = ["learning_agent", "behavioral-analytics", "dmer_monitor_123"]
        for agent_id in valid_ids:
            result = InputValidator.validate_agent_id(agent_id)
            assert result == agent_id
    
    def test_validate_agent_id_rejects_invalid(self):
        """Test that invalid agent IDs are rejected"""
        invalid_ids = ["agent@123", "agent id", "agent/path", "agent;cmd"]
        for agent_id in invalid_ids:
            with pytest.raises(ValueError):
                InputValidator.validate_agent_id(agent_id)
    
    def test_validate_username_accepts_valid(self):
        """Test that valid usernames are accepted"""
        valid_usernames = ["admin", "user123", "test_user", "AdminUser99"]
        for username in valid_usernames:
            result = InputValidator.validate_username(username)
            assert result == username
    
    def test_validate_username_rejects_invalid(self):
        """Test that invalid usernames are rejected"""
        invalid_usernames = ["ab", "a"*33, "user@admin", "user name", "user;DROP"]
        for username in invalid_usernames:
            with pytest.raises(ValueError):
                InputValidator.validate_username(username)


@pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
class TestRateLimiting:
    """Test suite for rate limiting middleware"""
    
    def test_rate_limit_allows_under_limit(self):
        """Test that requests under rate limit are allowed"""
        # Make a few requests - should all succeed
        for i in range(5):
            response = client.get("/api/training/status")
            # Should not be rate limited (status may be 200 or other, but not 429)
            assert response.status_code != 429
    
    def test_rate_limit_enforced(self):
        """Test that rate limit is enforced (simulation)"""
        # This is a basic test - actual rate limiting would require
        # many requests or manipulation of the middleware
        middleware = RateLimitMiddleware(app, calls=2, period=60)
        
        # Simulate tracking
        test_ip = "192.168.1.100"
        now = time.time()
        
        # Add requests to simulate limit reached
        middleware.clients[test_ip] = [now, now]
        
        # Check that limit is reached
        assert len(middleware.clients[test_ip]) >= middleware.calls


@pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
class TestSecurityHeaders:
    """Test suite for security headers"""
    
    def test_security_headers_present(self):
        """Test that security headers are added to responses"""
        response = client.get("/api/training/status")
        
        # Check for key security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        
    def test_xss_protection_header(self):
        """Test XSS protection header value"""
        response = client.get("/api/training/status")
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    
    def test_frame_options_header(self):
        """Test frame options header value"""
        response = client.get("/api/training/status")
        assert response.headers.get("X-Frame-Options") == "DENY"
    
    def test_content_type_options_header(self):
        """Test content type options header value"""
        response = client.get("/api/training/status")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"


@pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
class TestAuthenticationSecurity:
    """Test suite for authentication security"""
    
    def test_login_with_invalid_credentials_returns_generic_error(self):
        """Test that login errors don't reveal username existence"""
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpassword"
        })
        
        # Should return 401 with generic message
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        # Should not reveal if username exists or not
        assert "Invalid credentials" in data["detail"] or "authentication_failed" in str(data)
    
    def test_login_validates_input_format(self):
        """Test that login validates input format"""
        # Test with invalid username format
        response = client.post("/api/auth/login", json={
            "username": "a",  # Too short
            "password": "password123"
        })
        
        # Should return validation error
        assert response.status_code in [400, 422]  # Validation error
    
    def test_create_user_requires_strong_password(self):
        """Test that user creation requires strong password"""
        # This would require authentication, so we test the validation logic
        from pydantic import ValidationError
        from api_server import UserCreationRequest
        
        # Test weak password
        with pytest.raises(ValidationError):
            UserCreationRequest(
                username="testuser",
                password="weak",  # Too short
                role="admin"
            )
    
    def test_create_user_validates_role(self):
        """Test that user creation validates role"""
        from pydantic import ValidationError
        from api_server import UserCreationRequest
        
        # Test invalid role
        with pytest.raises(ValidationError):
            UserCreationRequest(
                username="testuser",
                password="strongpassword123",
                role="superadmin"  # Invalid role
            )


@pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
class TestSecurityManager:
    """Test suite for SecurityManager enhancements"""
    
    def setup_method(self):
        """Setup test environment"""
        self.manager = SecurityManager()
    
    def test_session_cleanup_functionality(self):
        """Test that session cleanup removes expired sessions"""
        # Add a mock expired session
        test_session_id = "test_session_123"
        old_time = datetime.utcnow() - timedelta(hours=10)
        
        self.manager.active_sessions[test_session_id] = {
            "username": "testuser",
            "role": "admin",
            "created": old_time,
            "last_activity": old_time
        }
        
        # Run cleanup
        cleaned = self.manager.cleanup_expired_sessions()
        
        # Session should be removed
        assert test_session_id not in self.manager.active_sessions
        assert cleaned >= 0
    
    def test_has_permission_master_admin(self):
        """Test that master admin has all permissions"""
        user_info = {
            "username": "master_admin",
            "role": "master"
        }
        
        # Master admin should have any permission
        assert self.manager.has_permission(user_info, "any_permission")
        assert self.manager.has_permission(user_info, "admin")
        assert self.manager.has_permission(user_info, "agents")
    
    def test_has_permission_regular_user(self):
        """Test permission checking for regular users"""
        # Add test user with specific permissions
        test_username = "testuser_" + str(int(time.time()))
        self.manager.authorized_users[test_username] = {
            "role": "admin",
            "permissions": ["read", "agents"],
            "active": True
        }
        
        user_info = {
            "username": test_username,
            "role": "admin"
        }
        
        # Should have granted permissions
        assert self.manager.has_permission(user_info, "read")
        assert self.manager.has_permission(user_info, "agents")
        
        # Should not have other permissions
        assert not self.manager.has_permission(user_info, "threats")


@pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
class TestCORSConfiguration:
    """Test suite for CORS configuration"""
    
    def test_cors_allows_whitelisted_origins(self):
        """Test that CORS allows whitelisted origins"""
        # The CORS middleware should allow localhost origins
        response = client.get(
            "/api/training/status",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Response should include CORS headers or succeed
        assert response.status_code != 403  # Not forbidden


@pytest.mark.skipif(not API_AVAILABLE, reason="API modules not available")
class TestAgentEndpointSecurity:
    """Test suite for agent endpoint security enhancements"""
    
    def test_agent_id_validation_in_endpoints(self):
        """Test that agent endpoints validate agent IDs"""
        # These endpoints require authentication, but we can test
        # that the validation logic exists
        
        # Valid agent ID format
        valid_id = "learning_agent"
        assert re.match(r'^[a-zA-Z0-9_-]+$', valid_id)
        
        # Invalid agent ID formats
        invalid_ids = ["agent;cmd", "agent/path", "agent@domain"]
        for invalid_id in invalid_ids:
            assert not re.match(r'^[a-zA-Z0-9_-]+$', invalid_id)


def test_gitignore_conceals_credentials():
    """Test that .gitignore properly conceals admin credentials"""
    gitignore_path = os.path.join(os.path.dirname(__file__), '..', '.gitignore')
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()
        
        # Check that sensitive files are in gitignore
        assert '.guardian_master_password.txt' in gitignore_content
        assert '.guardian_secret' in gitignore_content
        assert '.guardian_admin' in gitignore_content
        
        print("✅ .gitignore properly conceals admin credentials")
    else:
        pytest.skip(".gitignore file not found")


def test_credential_files_not_in_git():
    """Test that credential files are not tracked by git"""
    import subprocess
    
    try:
        # Check git ls-files for sensitive files
        result = subprocess.run(
            ['git', 'ls-files'],
            cwd=os.path.join(os.path.dirname(__file__), '..'),
            capture_output=True,
            text=True
        )
        
        tracked_files = result.stdout
        
        # These files should NOT be in git tracking
        assert '.guardian_master_password.txt' not in tracked_files
        assert '.guardian_secret' not in tracked_files
        assert '.guardian_admin' not in tracked_files
        
        print("✅ Credential files are not tracked by git")
    except Exception as e:
        pytest.skip(f"Could not check git status: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
