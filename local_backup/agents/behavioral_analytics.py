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
        
        if accuracy < 0.7 and self.performance_metrics['total_predictions'] > 100:
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
