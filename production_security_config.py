"""
Production Security Configuration for GuardianShield APIs
This module provides secure configurations for production deployment
"""

import os
from typing import List
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException, Depends

# Security configurations
PRODUCTION_MODE = os.getenv("GUARDIAN_PRODUCTION", "false").lower() == "true"
API_SECRET_KEY = os.getenv("GUARDIAN_API_SECRET", "dev-secret-change-in-production")
ALLOWED_ORIGINS = os.getenv("GUARDIAN_ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# Authentication
security = HTTPBearer(auto_error=False)

class ProductionSecurityMiddleware:
    """Production security middleware for GuardianShield APIs"""
    
    @staticmethod
    def get_cors_middleware():
        """Get CORS middleware with appropriate settings"""
        if PRODUCTION_MODE:
            return CORSMiddleware, {
                "allow_origins": ALLOWED_ORIGINS,
                "allow_credentials": False,
                "allow_methods": ["GET", "POST"],
                "allow_headers": ["Authorization", "Content-Type"],
            }
        else:
            # Development settings
            return CORSMiddleware, {
                "allow_origins": ["*"],
                "allow_credentials": True,
                "allow_methods": ["*"],
                "allow_headers": ["*"],
            }
    
    @staticmethod
    async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Verify API key for production endpoints"""
        if not PRODUCTION_MODE:
            return True  # Skip authentication in development
        
        if not credentials:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        if credentials.credentials != API_SECRET_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        return True
    
    @staticmethod
    def get_security_headers():
        """Get security headers for responses"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY", 
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'"
        }

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv("GUARDIAN_RATE_LIMIT", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("GUARDIAN_RATE_WINDOW", "60"))

# Input validation
MAX_REQUEST_SIZE = int(os.getenv("GUARDIAN_MAX_REQUEST_SIZE", "10485760"))  # 10MB
ALLOWED_FILE_TYPES = [".json", ".txt", ".csv"]

def validate_request_size(content_length: int):
    """Validate request size"""
    if content_length > MAX_REQUEST_SIZE:
        raise HTTPException(status_code=413, detail="Request too large")

def sanitize_input(input_data: str) -> str:
    """Sanitize user input"""
    if not input_data:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", "&", "\"", "'", ";", "(", ")", "{", "}", "[", "]"]
    sanitized = input_data
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")
    
    return sanitized[:1000]  # Limit length

# Logging configuration
SECURITY_LOG_LEVEL = os.getenv("GUARDIAN_LOG_LEVEL", "INFO")
AUDIT_LOG_ENABLED = os.getenv("GUARDIAN_AUDIT_LOG", "true").lower() == "true"

def log_security_event(event_type: str, details: dict):
    """Log security events for audit trail"""
    if AUDIT_LOG_ENABLED:
        import logging
        security_logger = logging.getLogger("guardian.security")
        security_logger.info(f"Security Event: {event_type} - {details}")

# Database security
def get_secure_db_config():
    """Get secure database configuration"""
    return {
        "check_same_thread": False if PRODUCTION_MODE else True,
        "timeout": 30,
        "isolation_level": "SERIALIZABLE",
        "foreign_keys": True
    }

# Environment validation
def validate_production_environment():
    """Validate production environment configuration"""
    if not PRODUCTION_MODE:
        return True
    
    issues = []
    
    if API_SECRET_KEY == "dev-secret-change-in-production":
        issues.append("API_SECRET_KEY must be changed for production")
    
    if "localhost" in ALLOWED_ORIGINS[0]:
        issues.append("ALLOWED_ORIGINS should not include localhost in production")
    
    required_env_vars = [
        "GUARDIAN_API_SECRET",
        "GUARDIAN_ALLOWED_ORIGINS",
        "GUARDIAN_LOG_LEVEL"
    ]
    
    for var in required_env_vars:
        if not os.getenv(var):
            issues.append(f"Missing required environment variable: {var}")
    
    if issues:
        raise RuntimeError(f"Production environment validation failed: {'; '.join(issues)}")
    
    return True