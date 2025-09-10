"""
behavioral_analytics.py: Real-time behavioral analytics and anomaly detection for GuardianShield agents.
"""
import numpy as np
import json
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

class BehavioralAnalytics:
    def __init__(self):
        self.behavior_log = []

    def log_behavior(self, event):
        self.behavior_log.append(event)
        if len(self.behavior_log) > 1000:
            self.behavior_log.pop(0)

    def analyze_behavior(self):
        # Example: Simple anomaly detection using z-score
        if not self.behavior_log:
            return None
        values = np.array([e['value'] for e in self.behavior_log if 'value' in e])
        if len(values) < 2:
            return None
        mean = np.mean(values)
        std = np.std(values)
        anomalies = []
        for i, v in enumerate(values):
            z = (v - mean) / std if std > 0 else 0
            if abs(z) > 2:
                anomalies.append((i, v, z))
        return anomalies

    def save_log(self, path="behavior_log.json"):
        with open(path, "w") as f:
            json.dump(self.behavior_log, f, indent=2)

    def load_log(self, path="behavior_log.json"):
        try:
            with open(path, "r") as f:
                self.behavior_log = json.load(f)
        except Exception:
            self.behavior_log = []

    def plot_behavior_trends(self):
        if not self.behavior_log:
            print("No behavior data to plot.")
            return
        values = [e['value'] for e in self.behavior_log if 'value' in e]
        plt.figure(figsize=(10, 4))
        plt.plot(values, label='Behavior Value')
        plt.title('Behavioral Trend Over Time')
        plt.xlabel('Event Index')
        plt.ylabel('Value')
        plt.legend()
        plt.tight_layout()
        plt.show()

    def cluster_behavior(self, n_clusters=2):
        values = np.array([[e['value']] for e in self.behavior_log if 'value' in e])
        if len(values) < n_clusters:
            print("Not enough data for clustering.")
            return None
        kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(values)
        print(f"Cluster centers: {kmeans.cluster_centers_}")
        return kmeans.labels_

    def advanced_anomaly_detection(self):
        # Use IQR for robust anomaly detection
        values = np.array([e['value'] for e in self.behavior_log if 'value' in e])
        if len(values) < 2:
            return None
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        anomalies = [(i, v) for i, v in enumerate(values) if v < lower or v > upper]
        return anomalies

if __name__ == "__main__":
    ba = BehavioralAnalytics()
    # Simulate logging behavior
    for i in range(100):
        ba.log_behavior({"user": f"user{i%5}", "value": np.random.normal(0, 1)})
    anomalies = ba.analyze_behavior()
    print("Anomalies:", anomalies)
    ba.save_log()
