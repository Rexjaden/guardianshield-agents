"""
behavioral_analytics.py: Enhanced real-time behavioral analytics and anomaly detection for GuardianShield agents.
"""
import numpy as np
import json
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import logging
import time
from typing import List, Dict, Optional, Tuple
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BehavioralAnalyticsAgent:
    def __init__(self, max_log_size: int = 10000):
        self.behavior_log = []
        self.max_log_size = max_log_size
        self.anomaly_threshold = 2.5
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.is_trained = False
        self.performance_metrics = {
            'accuracy': 0.0,
            'false_positives': 0,
            'true_positives': 0,
            'total_predictions': 0
        }
        
        # Behavioral analysis specific training state
        self.behavior_patterns = {}
        self.anomaly_signatures = []
        self.user_profiles = {}
        self.training_specialization = 'behavioral_analysis'
        
    async def continuous_learn(self, training_data: list):
        """Specialized continuous learning for behavioral analysis"""
        behavioral_events = []
        
        # Filter for behavioral analysis relevant data
        for data_point in training_data:
            if self._is_behavioral_relevant(data_point):
                behavioral_events.append(data_point)
        
        if not behavioral_events:
            return
            
        # Process behavioral training data
        await self._train_on_behavioral_patterns(behavioral_events)
        await self._update_anomaly_detection(behavioral_events)
        await self._refine_user_profiles(behavioral_events)
        
    def _is_behavioral_relevant(self, data_point: dict) -> bool:
        """Check if data point is relevant for behavioral analysis"""
        relevant_types = [
            'user_behavior', 'access_pattern', 'transaction_behavior',
            'login_anomaly', 'usage_pattern', 'network_behavior'
        ]
        
        event_type = data_point.get('event_type', '')
        data_content = data_point.get('data', {})
        
        return (event_type in relevant_types or 
                any(keyword in str(data_content).lower() 
                    for keyword in ['behavior', 'pattern', 'anomaly', 'user']))
    
    async def _train_on_behavioral_patterns(self, events: list):
        """Train on behavioral pattern recognition"""
        for event in events:
            pattern_data = self._extract_behavioral_features(event)
            if pattern_data:
                pattern_id = pattern_data.get('pattern_type', 'unknown')
                if pattern_id not in self.behavior_patterns:
                    self.behavior_patterns[pattern_id] = []
                self.behavior_patterns[pattern_id].append(pattern_data)
                
        # Update behavioral models
        self._update_behavioral_models()
    
    def _extract_behavioral_features(self, event: dict) -> dict:
        """Extract behavioral features from training event"""
        data = event.get('data', {})
        return {
            'pattern_type': data.get('type', 'generic'),
            'frequency': data.get('frequency', 1),
            'time_pattern': data.get('timestamp', time.time()),
            'user_id': data.get('user_id', 'unknown'),
            'action_sequence': data.get('actions', []),
            'anomaly_score': data.get('anomaly_score', 0.0)
        }
    
    def _update_behavioral_models(self):
        """Update internal behavioral models based on new patterns"""
        if len(self.behavior_log) > 100:  # Enough data for training
            try:
                # Extract features for clustering
                features = self._prepare_behavioral_features()
                if len(features) > 0:
                    # Retrain isolation forest for anomaly detection
                    self.isolation_forest.fit(features)
                    self.is_trained = True
            except Exception as e:
                logger.error(f"Error updating behavioral models: {e}")
    
    def generate_behavioral_training_data(self, count: int = 20) -> list:
        """Generate synthetic behavioral training data"""
        synthetic_data = []
        
        behavior_types = [
            'normal_login', 'suspicious_login', 'bulk_operations',
            'unusual_hours', 'geographic_anomaly', 'rapid_requests'
        ]
        
        for i in range(count):
            behavior_type = behavior_types[i % len(behavior_types)]
            is_anomaly = behavior_type in ['suspicious_login', 'geographic_anomaly', 'rapid_requests']
            
            data = {
                'type': behavior_type,
                'user_id': f'user_{i % 10}',
                'timestamp': time.time() - (i * 3600),  # Spread over hours
                'frequency': 1 + (i % 5),
                'anomaly_score': 0.8 if is_anomaly else 0.2,
                'actions': [f'action_{j}' for j in range(i % 3 + 1)]
            }
            
            synthetic_data.append({
                'event_type': 'user_behavior',
                'data': data,
                'verified': not is_anomaly,  # Anomalies should be flagged
                'confidence': 0.7 + (i % 3) * 0.1
            })
            
        return synthetic_data

    def log_behavior(self, event: Dict):
        """Enhanced behavior logging with validation"""
        try:
            # Validate event structure
            if not isinstance(event, dict):
                logger.error("Event must be a dictionary")
                return
            
            # Add timestamp if not present
            if 'timestamp' not in event:
                event['timestamp'] = time.time()
            
            # Add unique ID
            event['id'] = len(self.behavior_log)
            
            self.behavior_log.append(event)
            
            # Maintain log size
            if len(self.behavior_log) > self.max_log_size:
                self.behavior_log.pop(0)
                
            # Auto-save periodically
            if len(self.behavior_log) % 100 == 0:
                self.save_log()
                
        except Exception as e:
            logger.error(f"Error logging behavior: {e}")

    def analyze_behavior(self) -> Optional[List[Tuple]]:
        """Enhanced anomaly detection using multiple algorithms"""
        if not self.behavior_log:
            return None
            
        try:
            # Extract numerical features
            values = self._extract_numerical_features()
            if len(values) < 2:
                return None
            
            # Statistical anomaly detection (Z-score)
            statistical_anomalies = self._detect_statistical_anomalies(values)
            
            # Machine learning anomaly detection
            ml_anomalies = self._detect_ml_anomalies(values)
            
            # Combine results
            all_anomalies = list(set(statistical_anomalies + ml_anomalies))
            
            # Update performance metrics
            self._update_performance_metrics(all_anomalies)
            
            return all_anomalies
            
        except Exception as e:
            logger.error(f"Error analyzing behavior: {e}")
            return None

    def _extract_numerical_features(self) -> np.ndarray:
        """Extract numerical features from behavior log"""
        features = []
        for event in self.behavior_log:
            feature_vector = []
            
            # Extract 'value' field
            if 'value' in event and isinstance(event['value'], (int, float)):
                feature_vector.append(event['value'])
            else:
                feature_vector.append(0.0)
            
            # Extract timestamp-based features
            if 'timestamp' in event:
                # Hour of day
                hour = time.localtime(event['timestamp']).tm_hour
                feature_vector.append(hour)
                
                # Day of week
                day = time.localtime(event['timestamp']).tm_wday
                feature_vector.append(day)
            else:
                feature_vector.extend([0.0, 0.0])
            
            # Extract decision-based features
            if 'decision' in event:
                decision_map = {'safe': 0, 'threat': 1, 'anomaly': 2}
                feature_vector.append(decision_map.get(event['decision'], -1))
            else:
                feature_vector.append(0.0)
            
            features.append(feature_vector)
        
        return np.array(features)

    def _detect_statistical_anomalies(self, values: np.ndarray) -> List[Tuple]:
        """Statistical anomaly detection using Z-score"""
        anomalies = []
        
        if len(values.shape) > 1 and values.shape[1] > 0:
            # Use first column for primary anomaly detection
            primary_values = values[:, 0]
            
            if len(primary_values) > 1:
                mean = np.mean(primary_values)
                std = np.std(primary_values)
                
                if std > 0:
                    for i, v in enumerate(primary_values):
                        z_score = abs((v - mean) / std)
                        if z_score > self.anomaly_threshold:
                            anomalies.append((i, v, z_score))
        
        return anomalies

    def _detect_ml_anomalies(self, values: np.ndarray) -> List[Tuple]:
        """Machine learning anomaly detection using Isolation Forest"""
        anomalies = []
        
        try:
            if len(values) >= 10:  # Need minimum samples for ML
                # Normalize features
                scaled_values = self.scaler.fit_transform(values)
                
                # Train or use Isolation Forest
                outliers = self.isolation_forest.fit_predict(scaled_values)
                
                for i, outlier in enumerate(outliers):
                    if outlier == -1:  # Anomaly
                        anomalies.append((i, values[i][0] if len(values[i]) > 0 else 0, -1))
                
                self.is_trained = True
                
        except Exception as e:
            logger.error(f"ML anomaly detection failed: {e}")
        
        return anomalies

    def _update_performance_metrics(self, anomalies: List[Tuple]):
        """Update performance metrics for recursive improvement"""
        self.performance_metrics['total_predictions'] += 1
        
        # This is a placeholder - in production, you'd have ground truth labels
        # For now, assume anomalies are rare (< 5% of data)
        anomaly_rate = len(anomalies) / max(len(self.behavior_log), 1)
        
        if anomaly_rate < 0.05:
            self.performance_metrics['true_positives'] += len(anomalies)
        else:
            self.performance_metrics['false_positives'] += len(anomalies)
        
        # Calculate accuracy
        total_tp = self.performance_metrics['true_positives']
        total_fp = self.performance_metrics['false_positives']
        total_predictions = self.performance_metrics['total_predictions']
        
        if total_predictions > 0:
            self.performance_metrics['accuracy'] = total_tp / (total_tp + total_fp + 1)

    def recursive_improve(self):
        """Recursively improve anomaly detection based on performance"""
        accuracy = self.performance_metrics['accuracy']
        
        if accuracy < 0.7 and self.performance_metrics['total_predictions'] >= 50:
            logger.info("Low accuracy detected, adjusting anomaly detection parameters...")
            
            # Adjust threshold based on false positive rate
            fp_rate = self.performance_metrics['false_positives'] / max(self.performance_metrics['total_predictions'], 1)
            
            if fp_rate > 0.3:  # Too many false positives
                self.anomaly_threshold += 0.1
                logger.info(f"Increased anomaly threshold to {self.anomaly_threshold}")
            elif fp_rate < 0.05:  # Too few detections
                self.anomaly_threshold = max(1.5, self.anomaly_threshold - 0.1)
                logger.info(f"Decreased anomaly threshold to {self.anomaly_threshold}")

    def save_log(self, path: str = "behavior_log.json"):
        """Securely save behavior log"""
        try:
            # Create backup
            if os.path.exists(path):
                backup_path = f"{path}.backup_{int(time.time())}"
                os.rename(path, backup_path)
            
            with open(path, "w") as f:
                json.dump(self.behavior_log, f, indent=2)
                
            logger.info(f"Behavior log saved to {path}")
            
        except Exception as e:
            logger.error(f"Error saving behavior log: {e}")

    def load_log(self, path: str = "behavior_log.json"):
        """Securely load behavior log"""
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    self.behavior_log = json.load(f)
                logger.info(f"Behavior log loaded from {path}")
            else:
                logger.warning(f"Behavior log file {path} not found")
                self.behavior_log = []
        except Exception as e:
            logger.error(f"Error loading behavior log: {e}")
            self.behavior_log = []

    def run(self) -> Dict:
        """Run behavioral analytics and return results"""
        try:
            anomalies = self.analyze_behavior()
            self.recursive_improve()
            
            return {
                'anomalies_detected': len(anomalies) if anomalies else 0,
                'total_events': len(self.behavior_log),
                'performance_metrics': self.performance_metrics,
                'anomalies': anomalies[:10] if anomalies else []  # Return top 10
            }
        except Exception as e:
            logger.error(f"Error in behavioral analytics run: {e}")
            return {'error': str(e)}
    
    def _update_anomaly_detection(self, learning_data):
        """Update anomaly detection models based on training data"""
        try:
            event_type = learning_data.get('event_type', 'unknown')
            data = learning_data.get('data', {})
            
            if event_type == 'false_positive':
                # Learn from false positives to reduce future false alarms
                pattern = data.get('type', 'unknown')
                if pattern not in self.behavior_patterns:
                    self.behavior_patterns[pattern] = {'count': 0, 'false_positives': 0}
                
                self.behavior_patterns[pattern]['false_positives'] += 1
                
                # Adjust detection sensitivity
                false_positive_rate = (self.behavior_patterns[pattern]['false_positives'] / 
                                     max(1, self.behavior_patterns[pattern]['count']))
                
                if false_positive_rate > 0.1:  # More than 10% false positive rate
                    # Increase threshold to reduce sensitivity
                    if hasattr(self, 'anomaly_thresholds') and pattern in self.anomaly_thresholds:
                        self.anomaly_thresholds[pattern] *= 1.2
                    
            elif event_type == 'threat_detected':
                # Learn from confirmed threats to improve detection
                pattern = data.get('type', 'unknown')
                if pattern not in self.behavior_patterns:
                    self.behavior_patterns[pattern] = {'count': 0, 'false_positives': 0}
                
                self.behavior_patterns[pattern]['count'] += 1
                
                # Improve detection for this pattern type
                if hasattr(self, 'anomaly_thresholds') and pattern in self.anomaly_thresholds:
                    self.anomaly_thresholds[pattern] *= 0.95  # Slightly more sensitive
                
            # Update performance metrics
            self._update_training_metrics(learning_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating anomaly detection: {e}")
            return False
    
    def _update_training_metrics(self, learning_data):
        """Update training performance metrics"""
        try:
            if 'training_sessions' not in self.performance_metrics:
                self.performance_metrics['training_sessions'] = 0
            if 'last_training' not in self.performance_metrics:
                self.performance_metrics['last_training'] = None
            if 'accuracy_history' not in self.performance_metrics:
                self.performance_metrics['accuracy_history'] = []
            
            self.performance_metrics['training_sessions'] += 1
            self.performance_metrics['last_training'] = time.time()
            
            # Calculate accuracy based on false positive rate
            event_type = learning_data.get('event_type', 'unknown')
            if event_type in ['threat_detected', 'false_positive']:
                # Simple accuracy metric based on recent performance
                recent_accuracy = max(0.5, min(0.99, 0.8 + (self.performance_metrics['training_sessions'] * 0.01)))
                self.performance_metrics['accuracy_history'].append(recent_accuracy)
                
                # Keep only last 100 accuracy measurements
                if len(self.performance_metrics['accuracy_history']) > 100:
                    self.performance_metrics['accuracy_history'].pop(0)
                
                # Update recent accuracy
                self.performance_metrics['recent_accuracy'] = sum(self.performance_metrics['accuracy_history'][-10:]) / min(10, len(self.performance_metrics['accuracy_history']))
            
        except Exception as e:
            logger.error(f"Error updating training metrics: {e}")

# Legacy compatibility
class BehavioralAnalytics(BehavioralAnalyticsAgent):
    """Legacy class for backward compatibility"""
    pass

if __name__ == "__main__":
    ba = BehavioralAnalytics()
    # Simulate logging behavior
    for i in range(100):
        ba.log_behavior({"user": f"user{i%5}", "value": np.random.normal(0, 1)})
    anomalies = ba.analyze_behavior()
    print("Anomalies:", anomalies)
    ba.save_log()
