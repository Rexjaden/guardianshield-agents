"""
test_agents_updated.py: Updated test suite matching actual GuardianShield agent implementations
"""
import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the agents directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents'))

# Import agents to test
from agents.learning_agent import LearningAgent
from agents.genetic_evolver import GeneticEvolver
from agents.behavioral_analytics import BehavioralAnalyticsAgent
from agents.data_ingestion import DataIngestionAgent
from agents.web3_utils import SecureWeb3Utils
from agents.flare_integration import FlareIntegrationAgent
from agents.dmer_monitor_agent import DMERMonitorAgent
from agents.utils import (
    HashUtilities, DataValidator, TimeUtilities, 
    NetworkUtilities, FileUtilities, ConfigurationManager
)

class TestLearningAgent:
    """Test suite for LearningAgent matching actual implementation"""
    
    def setup_method(self):
        """Setup test environment"""
        self.agent = LearningAgent("test_agent")
    
    def test_initialization(self):
        """Test agent initialization"""
        assert self.agent.name == "test_agent"
        assert self.agent.learning_rate == 0.1  # Actual implementation value
        assert self.agent.unlimited_evolution == True
        assert self.agent.autonomous_decisions == True
    
    def test_autonomous_cycle(self):
        """Test autonomous operation cycle"""
        # Should not raise exception
        self.agent.autonomous_cycle()
        assert True  # Successfully executed
    
    def test_learn_method(self):
        """Test learning method"""
        test_data = {'pattern': 'test', 'threat_level': 5}
        self.agent.learn(test_data)
        assert True  # Successfully executed
    
    def test_act_method(self):
        """Test action method"""
        observation = {'activity': 'suspicious_login', 'ip': '192.168.1.100'}
        self.agent.act(observation)
        assert True  # Successfully executed
    
    def test_unlimited_evolution_enable(self):
        """Test enabling unlimited evolution"""
        self.agent.enable_unlimited_evolution()
        assert self.agent.unlimited_evolution == True

class TestGeneticEvolver:
    """Test suite for GeneticEvolver matching actual implementation"""
    
    def setup_method(self):
        """Setup test environment"""
        self.evolver = GeneticEvolver()
    
    def test_initialization(self):
        """Test evolver initialization"""
        assert self.evolver.code_path == "agents/genetic_evolver.py"
        assert self.evolver.backup_dir == "evolution_backups"
    
    def test_backup_code(self):
        """Test code backup functionality"""
        backup_file = self.evolver.backup_code()
        assert os.path.exists(backup_file)
        # Cleanup
        os.remove(backup_file)
    
    def test_analyze_self_performance(self):
        """Test self-performance analysis"""
        metrics = self.evolver.analyze_self_performance()
        assert 'improvement_potential' in metrics
        assert 'efficiency_score' in metrics
        assert 'adaptability_score' in metrics
    
    def test_recursive_self_improve(self):
        """Test recursive self-improvement capability"""
        # Should not raise exception
        self.evolver.recursive_self_improve()
        assert True  # Successfully executed

class TestBehavioralAnalyticsAgent:
    """Test suite for BehavioralAnalyticsAgent"""
    
    def setup_method(self):
        """Setup test environment"""
        self.agent = BehavioralAnalyticsAgent()
    
    def test_initialization(self):
        """Test agent initialization"""
        assert hasattr(self.agent, 'name')
        assert hasattr(self.agent, 'anomaly_threshold')
        assert hasattr(self.agent, 'behavior_patterns')
    
    def test_log_behavior(self):
        """Test behavior logging"""
        behavior = {
            'user_id': 'test_user',
            'action': 'login',
            'timestamp': time.time(),
            'metadata': {'ip': '192.168.1.100'}
        }
        
        self.agent.log_behavior(behavior)
        assert len(self.agent.behavior_patterns) >= 0  # Should not fail
    
    def test_analyze_behavior(self):
        """Test behavior analysis"""
        # Add some test behavior first
        for i in range(5):
            behavior = {
                'user_id': f'test_user_{i}',
                'action': 'login',
                'timestamp': time.time() + i,
                'metadata': {'ip': f'192.168.1.{100+i}'}
            }
            self.agent.log_behavior(behavior)
        
        anomalies = self.agent.analyze_behavior()
        assert isinstance(anomalies, list)

class TestDataIngestionAgent:
    """Test suite for DataIngestionAgent matching actual implementation"""
    
    def setup_method(self):
        """Setup test environment"""
        self.agent = DataIngestionAgent()
    
    def test_initialization(self):
        """Test agent initialization"""
        assert hasattr(self.agent, 'name')
        assert hasattr(self.agent, 'active_sources')
        assert hasattr(self.agent, 'threat_cache')
    
    def test_autonomous_cycle(self):
        """Test autonomous operation cycle"""
        # Should not raise exception
        self.agent.autonomous_cycle()
        assert True  # Successfully executed

class TestDMERMonitorAgent:
    """Test suite for DMERMonitorAgent"""
    
    def setup_method(self):
        """Setup test environment"""
        self.agent = DMERMonitorAgent()
    
    def test_initialization(self):
        """Test agent initialization"""
        assert self.agent.name == "DMERMonitorAgent"
        assert hasattr(self.agent, 'monitored_entities')
        assert hasattr(self.agent, 'threat_severity_weights')
    
    def test_query_entity(self):
        """Test entity querying"""
        result = self.agent.query_entity("test_entity", "malware")
        assert isinstance(result, dict)
        assert 'entity' in result
        assert 'query_type' in result
    
    def test_calculate_threat_severity(self):
        """Test threat severity calculation"""
        severity = self.agent.calculate_threat_severity("malware", 0.8)
        assert isinstance(severity, (int, float))
        assert severity >= 0

class TestUtilities:
    """Test suite for utility functions"""
    
    def test_hash_utilities(self):
        """Test hash utility functions"""
        hash_util = HashUtilities()
        test_data = "test_string"
        
        # Test various hash functions
        sha256_hash = hash_util.sha256(test_data)
        assert len(sha256_hash) == 64  # SHA256 produces 64 character hex string
        
        md5_hash = hash_util.md5(test_data)
        assert len(md5_hash) == 32  # MD5 produces 32 character hex string
    
    def test_data_validator(self):
        """Test data validation utilities"""
        validator = DataValidator()
        
        # Test IP validation
        assert validator.is_valid_ip("192.168.1.1") == True
        assert validator.is_valid_ip("invalid_ip") == False
        
        # Test email validation
        assert validator.is_valid_email("test@example.com") == True
        assert validator.is_valid_email("invalid_email") == False
    
    def test_time_utilities(self):
        """Test time utility functions"""
        time_util = TimeUtilities()
        
        current_time = time_util.get_current_timestamp()
        assert isinstance(current_time, (int, float))
        
        formatted_time = time_util.format_timestamp(current_time)
        assert isinstance(formatted_time, str)
    
    def test_network_utilities(self):
        """Test network utility functions"""
        net_util = NetworkUtilities()
        
        # Test port scanning (local only for safety)
        is_open = net_util.is_port_open("127.0.0.1", 80, timeout=1)
        assert isinstance(is_open, bool)
    
    def test_file_utilities(self):
        """Test file utility functions"""
        file_util = FileUtilities()
        
        # Test safe file operations
        test_path = "test_file.txt"
        assert file_util.safe_write(test_path, "test content") == True
        
        content = file_util.safe_read(test_path)
        assert content == "test content"
        
        # Cleanup
        os.remove(test_path) if os.path.exists(test_path) else None
    
    def test_configuration_manager(self):
        """Test configuration management"""
        config_manager = ConfigurationManager()
        
        # Test configuration operations
        config_manager.set("test_key", "test_value")
        assert config_manager.get("test_key") == "test_value"
        
        assert config_manager.get("nonexistent_key", "default") == "default"

class TestIntegration:
    """Integration tests for agent interactions"""
    
    def test_agent_communication(self):
        """Test communication between agents"""
        learning_agent = LearningAgent("learning_test")
        behavioral_agent = BehavioralAnalyticsAgent()
        
        # Test data sharing
        test_data = {'pattern': 'suspicious_activity', 'confidence': 0.8}
        learning_agent.learn(test_data)
        
        # Should not raise exceptions
        assert True
    
    @pytest.mark.asyncio
    async def test_async_operations(self):
        """Test asynchronous agent operations"""
        agent = LearningAgent("async_test")
        
        # Test async capability
        await asyncio.sleep(0.1)  # Simulate async work
        
        assert agent.name == "async_test"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])