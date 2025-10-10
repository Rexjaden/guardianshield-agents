"""
utils.py: Enhanced utility functions for GuardianShield agents with security and logging improvements.
"""
import json
import hashlib
import time
import logging
import os
import base64
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

# Try to import cryptography, fallback to basic implementations if not available
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("Warning: cryptography not available, using basic encryption fallbacks")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not available, HTTP features disabled")

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
    load_dotenv()
except ImportError:
    DOTENV_AVAILABLE = False
    print("Warning: python-dotenv not available, using manual environment loading")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecureStorage:
    """Secure storage utility with encryption"""
    
    def __init__(self, password: str = None):
        self.password = password or os.getenv('ENCRYPTION_PASSWORD', 'default_guardian_key')
        
        if CRYPTO_AVAILABLE:
            self._fernet = self._get_fernet_instance()
        else:
            self._fernet = None
            logger.warning("Cryptography not available, using basic encoding for storage")
    
    def _get_fernet_instance(self):
        """Create Fernet instance from password"""
        if not CRYPTO_AVAILABLE:
            return None
            
        password_bytes = self.password.encode()
        salt = b'guardian_shield_salt'  # In production, use random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return Fernet(key)
    
    def encrypt_data(self, data: Any) -> str:
        """Encrypt data and return base64 encoded string"""
        try:
            json_data = json.dumps(data, sort_keys=True)
            
            if CRYPTO_AVAILABLE and self._fernet:
                encrypted = self._fernet.encrypt(json_data.encode())
                return base64.urlsafe_b64encode(encrypted).decode()
            else:
                # Fallback: use simple base64 encoding
                return base64.b64encode(json_data.encode()).decode()
                
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> Any:
        """Decrypt base64 encoded string and return original data"""
        try:
            if CRYPTO_AVAILABLE and self._fernet:
                encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
                decrypted = self._fernet.decrypt(encrypted_bytes)
                return json.loads(decrypted.decode())
            else:
                # Fallback: decode from simple base64
                json_data = base64.b64decode(encrypted_data.encode()).decode()
                return json.loads(json_data)
                
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise

class DataValidator:
    """Enhanced data validation utilities"""
    
    @staticmethod
    def validate_ethereum_address(address: str) -> bool:
        """Validate Ethereum address format"""
        if not address or not isinstance(address, str):
            return False
        
        # Remove 0x prefix if present
        if address.startswith('0x'):
            address = address[2:]
        
        # Check length and hex format
        if len(address) != 40:
            return False
        
        try:
            int(address, 16)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IP address format"""
        if not ip or not isinstance(ip, str):
            return False
        
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        try:
            for part in parts:
                num = int(part)
                if not 0 <= num <= 255:
                    return False
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_threat_data(data: Dict) -> tuple[bool, List[str]]:
        """Validate threat data structure"""
        errors = []
        
        required_fields = ['threat_type', 'description', 'timestamp']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate severity if present
        if 'severity' in data:
            severity = data['severity']
            if not isinstance(severity, (int, float)) or not 1 <= severity <= 10:
                errors.append("Severity must be a number between 1 and 10")
        
        # Validate timestamp
        if 'timestamp' in data:
            timestamp = data['timestamp']
            if not isinstance(timestamp, (int, float)) or timestamp < 0:
                errors.append("Invalid timestamp format")
        
        return len(errors) == 0, errors

class HashUtilities:
    """Enhanced hashing utilities"""
    
    @staticmethod
    def calculate_sha256(data: Union[str, bytes, Dict]) -> str:
        """Calculate SHA256 hash of data"""
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def calculate_md5(data: Union[str, bytes]) -> str:
        """Calculate MD5 hash of data"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        return hashlib.md5(data).hexdigest()
    
    @staticmethod
    def verify_hash(data: Union[str, bytes, Dict], expected_hash: str, algorithm: str = 'sha256') -> bool:
        """Verify data against expected hash"""
        if algorithm.lower() == 'sha256':
            calculated_hash = HashUtilities.calculate_sha256(data)
        elif algorithm.lower() == 'md5':
            calculated_hash = HashUtilities.calculate_md5(data)
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        
        return calculated_hash.lower() == expected_hash.lower()

class TimeUtilities:
    """Enhanced time utilities"""
    
    @staticmethod
    def get_timestamp() -> float:
        """Get current Unix timestamp"""
        return time.time()
    
    @staticmethod
    def format_timestamp(timestamp: float, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format timestamp to readable string"""
        return datetime.fromtimestamp(timestamp).strftime(format_str)
    
    @staticmethod
    def is_recent(timestamp: float, max_age_hours: float = 24) -> bool:
        """Check if timestamp is within the last N hours"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        return (current_time - timestamp) <= max_age_seconds
    
    @staticmethod
    def get_time_ago_string(timestamp: float) -> str:
        """Get human-readable time ago string"""
        current_time = time.time()
        diff = current_time - timestamp
        
        if diff < 60:
            return f"{int(diff)} seconds ago"
        elif diff < 3600:
            return f"{int(diff / 60)} minutes ago"
        elif diff < 86400:
            return f"{int(diff / 3600)} hours ago"
        else:
            return f"{int(diff / 86400)} days ago"

class NetworkUtilities:
    """Enhanced network utilities"""
    
    @staticmethod
    def safe_request(url: str, method: str = 'GET', **kwargs) -> Optional[Any]:
        """Make a safe HTTP request with error handling and timeouts"""
        if not REQUESTS_AVAILABLE:
            logger.warning("HTTP requests not available - requests library not installed")
            return None
            
        try:
            # Set default timeout if not provided
            if 'timeout' not in kwargs:
                kwargs['timeout'] = 30
            
            # Set default headers if not provided
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            
            # Add User-Agent if not present
            if 'User-Agent' not in kwargs['headers']:
                kwargs['headers']['User-Agent'] = 'GuardianShield-Agent/1.0'
            
            method = method.upper()
            if method == 'GET':
                response = requests.get(url, **kwargs)
            elif method == 'POST':
                response = requests.post(url, **kwargs)
            elif method == 'PUT':
                response = requests.put(url, **kwargs)
            elif method == 'DELETE':
                response = requests.delete(url, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response
            
        except Exception as e:  # Catch all exceptions since requests might not be available
            logger.error(f"Network request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in network request: {e}")
            return None
    
    @staticmethod
    def is_url_safe(url: str) -> bool:
        """Check if URL is safe to access"""
        if not url or not isinstance(url, str):
            return False
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = [
            'localhost', '127.0.0.1', '0.0.0.0',
            '192.168.', '10.', '172.',  # Private IP ranges
            'file://', 'ftp://', 'ftps://'
        ]
        
        url_lower = url.lower()
        for pattern in suspicious_patterns:
            if pattern in url_lower:
                return False
        
        return True

class FileUtilities:
    """Enhanced file utilities with security"""
    
    @staticmethod
    def safe_read_json(filepath: str) -> Optional[Dict]:
        """Safely read JSON file with error handling"""
        try:
            if not os.path.exists(filepath):
                logger.warning(f"File does not exist: {filepath}")
                return None
            
            # Check file size
            file_size = os.path.getsize(filepath)
            max_size = int(os.getenv('MAX_FILE_SIZE_MB', '10')) * 1024 * 1024  # Default 10MB
            
            if file_size > max_size:
                logger.error(f"File too large: {filepath} ({file_size} bytes)")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {filepath}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            return None
    
    @staticmethod
    def safe_write_json(filepath: str, data: Dict, backup: bool = True) -> bool:
        """Safely write JSON file with backup option"""
        try:
            # Create backup if file exists and backup is requested
            if backup and os.path.exists(filepath):
                backup_path = f"{filepath}.backup_{int(time.time())}"
                try:
                    os.rename(filepath, backup_path)
                    logger.info(f"Created backup: {backup_path}")
                except Exception as e:
                    logger.warning(f"Could not create backup: {e}")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Write data
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully wrote file: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing file {filepath}: {e}")
            return False
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """Get safe filename by removing dangerous characters"""
        import re
        
        # Remove or replace dangerous characters
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove any remaining non-printable characters
        safe_filename = ''.join(char for char in safe_filename if char.isprintable())
        
        # Limit length
        max_length = int(os.getenv('MAX_FILENAME_LENGTH', '255'))
        if len(safe_filename) > max_length:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:max_length - len(ext)] + ext
        
        return safe_filename

class LoggingUtilities:
    """Enhanced logging utilities"""
    
    @staticmethod
    def setup_agent_logger(agent_name: str, log_level: str = None) -> logging.Logger:
        """Setup logger for an agent with proper formatting"""
        log_level = log_level or os.getenv('LOG_LEVEL', 'INFO')
        
        logger = logging.getLogger(f"GuardianShield.{agent_name}")
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create console handler if not exists
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @staticmethod
    def log_threat_detection(logger: logging.Logger, threat_data: Dict):
        """Log threat detection with structured format"""
        threat_id = threat_data.get('id', 'unknown')
        threat_type = threat_data.get('threat_type', 'unknown')
        severity = threat_data.get('severity', 'unknown')
        
        logger.warning(f"THREAT DETECTED - ID: {threat_id}, Type: {threat_type}, Severity: {severity}")
    
    @staticmethod
    def log_performance_metrics(logger: logging.Logger, metrics: Dict):
        """Log performance metrics in structured format"""
        logger.info(f"PERFORMANCE METRICS - {json.dumps(metrics, indent=2)}")

class ConfigurationManager:
    """Enhanced configuration management"""
    
    def __init__(self, config_file: str = 'guardian_config.json'):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        config = FileUtilities.safe_read_json(self.config_file)
        if config is None:
            logger.warning(f"Could not load config from {self.config_file}, using defaults")
            return self._get_default_config()
        return config
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'agents': {
                'learning_agent': {
                    'learning_rate': 0.01,
                    'improvement_threshold': 0.8
                },
                'genetic_evolver': {
                    'mutation_rate': 0.1,
                    'population_size': 50
                },
                'behavioral_analytics': {
                    'anomaly_threshold': 2.5,
                    'max_log_size': 10000
                }
            },
            'security': {
                'encryption_enabled': True,
                'rate_limit_delay': 1.0,
                'max_file_size_mb': 10
            },
            'logging': {
                'level': 'INFO',
                'max_log_files': 10
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self._save_config()
    
    def _save_config(self):
        """Save configuration to file"""
        FileUtilities.safe_write_json(self.config_file, self.config)

# Initialize global configuration manager
config_manager = ConfigurationManager()

# Enhanced event logging
def log_event(event: str, level: str = 'INFO', data: Dict = None):
    """Enhanced event logging with structured data"""
    logger = logging.getLogger('GuardianShield.Events')
    
    # Format message
    message = f"[EVENT] {event}"
    if data:
        message += f" - Data: {json.dumps(data, indent=2)}"
    
    # Log at appropriate level
    level = level.upper()
    if level == 'DEBUG':
        logger.debug(message)
    elif level == 'INFO':
        logger.info(message)
    elif level == 'WARNING':
        logger.warning(message)
    elif level == 'ERROR':
        logger.error(message)
    elif level == 'CRITICAL':
        logger.critical(message)
    else:
        logger.info(message)

# Legacy functions for backward compatibility
def hash_data(data: Union[str, Dict]) -> str:
    """Legacy hash function"""
    return HashUtilities.calculate_sha256(data)

def format_timestamp(timestamp: float) -> str:
    """Legacy timestamp formatting"""
    return TimeUtilities.format_timestamp(timestamp)

def load_json_file(filepath: str) -> Optional[Dict]:
    """Legacy JSON loading"""
    return FileUtilities.safe_read_json(filepath)

def save_json_file(filepath: str, data: Dict) -> bool:
    """Legacy JSON saving"""
    return FileUtilities.safe_write_json(filepath, data)

def validate_ethereum_address(address: str) -> bool:
    """Legacy Ethereum address validation"""
    return DataValidator.validate_ethereum_address(address)

def is_recent_timestamp(timestamp: float, max_age_hours: float = 24) -> bool:
    """Legacy timestamp validation"""
    return TimeUtilities.is_recent(timestamp, max_age_hours)
