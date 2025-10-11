"""
test_agents.py: Comprehensive test suite for GuardianShield agents
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
    """Test suite for LearningAgent"""
    
    def setup_method(self):
        """Setup test environment"""
        self.agent = LearningAgent()
    
    def test_initialization(self):
        """Test agent initialization"""
        assert self.agent.learning_rate == 0.01
        assert len(self.agent.experiences) == 0
        assert len(self.agent.threat_patterns) == 0
    
    def test_learn_from_experience(self):
        """Test learning from experience"""
        experience = {
            'action': 'block_ip',
            'result': 'success',
            'context': {'ip': '192.168.1.100', 'threat_level': 8},
            'timestamp': time.time()
        }
        
        self.agent.learn_from_experience(experience)
        assert len(self.agent.experiences) == 1
        assert self.agent.experiences[0] == experience
    
    def test_analyze_patterns(self):
        """Test pattern analysis"""
        # Add multiple experiences
        for i in range(5):
            self.agent.learn_from_experience({
                'action': 'block_ip',
                'result': 'success',
                'context': {'threat_level': 7 + i},
                'timestamp': time.time()
            })
        
        patterns = self.agent.analyze_patterns()
        assert 'successful_actions' in patterns
        assert 'threat_level_distribution' in patterns
    
    def test_recursive_improvement(self):
        """Test recursive improvement functionality"""
        # Add experiences to trigger improvement
        for i in range(10):
            result = 'success' if i % 2 == 0 else 'failure'
            self.agent.learn_from_experience({
                'action': 'test_action',
                'result': result,
                'context': {},
                'timestamp': time.time()
            })
        
        initial_rate = self.agent.learning_rate
        self.agent.recursive_learn_and_improve()
        
        # Learning rate should adjust based on performance
        assert self.agent.learning_rate != initial_rate

class TestGeneticEvolver:
    """Test suite for GeneticEvolver"""
    
    def setup_method(self):
        """Setup test environment"""
        self.evolver = GeneticEvolver()
    
    def test_initialization(self):
        """Test evolver initialization"""
        assert self.evolver.population_size == 50
        assert self.evolver.mutation_rate == 0.1
        assert len(self.evolver.population) == 0
    
    def test_create_individual(self):
        """Test individual creation"""
        individual = self.evolver.create_individual()
        assert 'detection_threshold' in individual
        assert 'response_aggressiveness' in individual
        assert 'learning_rate' in individual
    
    def test_evolve_population(self):
        """Test population evolution"""
        # Initialize population
        self.evolver.initialize_population()
        assert len(self.evolver.population) == self.evolver.population_size
        
        # Evolve one generation
        initial_generation = self.evolver.generation
        self.evolver.evolve()
        assert self.evolver.generation == initial_generation + 1
    
    def test_recursive_self_improve(self):
        """Test recursive self-improvement"""
        self.evolver.initialize_population()
        
        # Simulate some performance data
        for individual in self.evolver.population[:5]:
            individual['fitness'] = 0.9  # High fitness
        
        initial_generation = self.evolver.generation
        improvement_result = self.evolver.recursive_self_improve()
        
        assert improvement_result is not None
        assert 'improvement_detected' in improvement_result

class TestBehavioralAnalyticsAgent:
    """Test suite for BehavioralAnalyticsAgent"""
    
    def setup_method(self):
        """Setup test environment"""
        self.agent = BehavioralAnalyticsAgent()
    
    def test_initialization(self):
        """Test agent initialization"""
        assert len(self.agent.behavior_log) == 0
        assert self.agent.anomaly_threshold == 2.5
    
    def test_log_behavior(self):
        """Test behavior logging"""
        event = {
            'type': 'access_attempt',
            'value': 5.0,
            'timestamp': time.time()
        }
        
        self.agent.log_behavior(event)
        assert len(self.agent.behavior_log) == 1
        assert 'id' in self.agent.behavior_log[0]
    
    def test_analyze_behavior(self):
        """Test behavior analysis"""
        # Add normal behaviors
        for i in range(10):
            self.agent.log_behavior({
                'type': 'normal',
                'value': 5.0 + (i * 0.1),
                'timestamp': time.time()
            })
        
        # Add anomalous behavior
        self.agent.log_behavior({
            'type': 'anomaly',
            'value': 50.0,  # Much higher than normal
            'timestamp': time.time()
        })
        
        anomalies = self.agent.analyze_behavior()
        assert anomalies is not None
        assert len(anomalies) > 0
    
    def test_recursive_improve(self):
        """Test recursive improvement"""
        # Set up performance metrics
        self.agent.performance_metrics['total_predictions'] = 100
        self.agent.performance_metrics['false_positives'] = 50
        
        initial_threshold = self.agent.anomaly_threshold
        self.agent.recursive_improve()
        
        # Threshold should adjust for high false positive rate
        assert self.agent.anomaly_threshold != initial_threshold

class TestDataIngestionAgent:
    """Test suite for DataIngestionAgent"""
    
    def setup_method(self):
        """Setup test environment"""
        self.agent = DataIngestionAgent()
    
    def test_initialization(self):
        """Test agent initialization"""
        assert len(self.agent.sources) > 0
        assert 'abuseipdb' in self.agent.sources
    
    @patch('requests.get')
    def test_fetch_from_source(self, mock_get):
        """Test fetching from threat intelligence source"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [{'ip': '1.2.3.4', 'threat_type': 'malware'}]
        }
        mock_get.return_value = mock_response
        
        threats = self.agent.fetch_from_source('abuseipdb')
        assert threats is not None
        assert len(threats) > 0
    
    def test_validate_threat_data(self):
        """Test threat data validation"""
        valid_data = {
            'ip': '1.2.3.4',
            'threat_type': 'malware',
            'confidence': 85,
            'timestamp': time.time()
        }
        
        invalid_data = {
            'ip': 'invalid_ip',
            'threat_type': '',
            'confidence': -1
        }
        
        assert self.agent.validate_threat_data(valid_data) == True
        assert self.agent.validate_threat_data(invalid_data) == False

class TestSecureWeb3Utils:
    """Test suite for SecureWeb3Utils"""
    
    def setup_method(self):
        """Setup test environment"""
        with patch('web3.Web3'):
            self.utils = SecureWeb3Utils('http://localhost:8545')
    
    def test_initialization(self):
        """Test utils initialization"""
        assert self.utils.max_gas_price is not None
        assert self.utils.transaction_timeout > 0
    
    def test_validate_address(self):
        """Test address validation"""
        valid_address = '0x1234567890123456789012345678901234567890'
        invalid_address = 'not_an_address'
        
        assert self.utils.validate_address(valid_address) == True
        assert self.utils.validate_address(invalid_address) == False
    
    def test_estimate_gas_safely(self):
        """Test safe gas estimation"""
        with patch.object(self.utils.web3.eth, 'estimate_gas', return_value=21000):
            gas_estimate = self.utils.estimate_gas_safely({
                'to': '0x1234567890123456789012345678901234567890',
                'value': 1000000000000000000
            })
            assert gas_estimate == 21000

class TestFlareIntegrationAgent:
    """Test suite for FlareIntegrationAgent"""
    
    def setup_method(self):
        """Setup test environment"""
        with patch('web3.Web3'):
            self.agent = FlareIntegrationAgent()
    
    def test_initialization(self):
        """Test agent initialization"""
        assert self.agent.price_feeds is not None
        assert 'ETH' in self.agent.price_feeds
    
    @patch('requests.get')
    def test_get_network_metrics(self, mock_get):
        """Test network metrics retrieval"""
        with patch.object(self.agent.web3.eth, 'get_block') as mock_get_block:
            mock_get_block.return_value = {
                'number': 1000,
                'timestamp': int(time.time()),
                'transactions': ['0x123', '0x456']
            }
            
            with patch.object(self.agent.web3.eth, 'gas_price', 20000000000):
                metrics = self.agent.get_network_metrics()
                assert metrics is not None
                assert 'block_number' in metrics

class TestDMERMonitorAgent:
    """Test suite for DMERMonitorAgent"""
    
    def setup_method(self):
        """Setup test environment"""
        self.agent = DMERMonitorAgent()
    
    def test_initialization(self):
        """Test agent initialization"""
        assert self.agent.name is not None
        assert len(self.agent.known_entities) == 0
    
    @patch('requests.get')
    def test_query_entity(self, mock_get):
        """Test entity querying"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'entity_id': 'test_entity',
            'threat_level': 8,
            'description': 'Test threat'
        }
        mock_get.return_value = mock_response
        
        entity_data = self.agent.query_entity('test_entity')
        assert entity_data is not None
        assert entity_data['entity_id'] == 'test_entity'
    
    def test_calculate_threat_severity(self):
        """Test threat severity calculation"""
        threat_data = {
            'techniques': ['phishing', 'malware'],
            'eth_addresses': ['0x123'],
            'ip_addresses': ['1.2.3.4'],
            'title': 'Major rug pull detected',
            'snippet': 'This is a severe threat'
        }
        
        severity = self.agent._calculate_threat_severity(threat_data)
        assert severity >= 1
        assert severity <= 10

class TestUtilities:
    """Test suite for utility functions"""
    
    def test_hash_utilities(self):
        """Test hash utilities"""
        test_data = "test string"
        hash_result = HashUtilities.calculate_sha256(test_data)
        assert len(hash_result) == 64  # SHA256 produces 64-character hex string
        assert hash_result == HashUtilities.calculate_sha256(test_data)  # Consistent
    
    def test_data_validator(self):
        """Test data validation"""
        # Ethereum address validation
        assert DataValidator.validate_ethereum_address('0x1234567890123456789012345678901234567890') == True
        assert DataValidator.validate_ethereum_address('invalid') == False
        
        # IP address validation
        assert DataValidator.validate_ip_address('192.168.1.1') == True
        assert DataValidator.validate_ip_address('999.999.999.999') == False
    
    def test_time_utilities(self):
        """Test time utilities"""
        current_time = TimeUtilities.get_timestamp()
        assert current_time > 0
        
        formatted = TimeUtilities.format_timestamp(current_time)
        assert len(formatted) > 0
        
        assert TimeUtilities.is_recent(current_time, 1) == True
        assert TimeUtilities.is_recent(current_time - 7200, 1) == False  # 2 hours ago
    
    def test_network_utilities(self):
        """Test network utilities"""
        assert NetworkUtilities.is_url_safe('https://example.com') == True
        assert NetworkUtilities.is_url_safe('file:///etc/passwd') == False
        assert NetworkUtilities.is_url_safe('http://localhost') == False
    
    @patch('builtins.open')
    @patch('os.path.exists')
    def test_file_utilities(self, mock_exists, mock_open):
        """Test file utilities"""
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = '{"test": "data"}'
        
        # Test safe filename generation
        safe_name = FileUtilities.get_safe_filename('test<>file|name.txt')
        assert '<' not in safe_name
        assert '>' not in safe_name
        assert '|' not in safe_name
    
    def test_configuration_manager(self):
        """Test configuration manager"""
        with patch.object(FileUtilities, 'safe_read_json', return_value=None):
            config = ConfigurationManager()
            
            # Test default config
            learning_rate = config.get('agents.learning_agent.learning_rate')
            assert learning_rate == 0.01
            
            # Test setting value
            config.set('test.value', 'test_data')
            assert config.get('test.value') == 'test_data'

class TestIntegration:
    """Integration tests for agent interactions"""
    
    def test_agent_communication(self):
        """Test communication between agents"""
        learning_agent = LearningAgent()
        evolver = GeneticEvolver()
        
        # Test data sharing
        experience = {
            'action': 'test',
            'result': 'success',
            'context': {},
            'timestamp': time.time()
        }
        
        learning_agent.learn_from_experience(experience)
        assert len(learning_agent.experiences) == 1
        
        # Test evolution trigger
        evolver.initialize_population()
        assert len(evolver.population) > 0
    
    @pytest.mark.asyncio
    async def test_async_operations(self):
        """Test asynchronous operations"""
        flare_agent = FlareIntegrationAgent()
        
        # Test async methods exist and are callable
        assert hasattr(flare_agent, 'async_get')
        assert hasattr(flare_agent, 'async_post')

if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])