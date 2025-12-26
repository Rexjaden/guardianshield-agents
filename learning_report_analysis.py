"""
Learning Report Analysis Tool
Analyze learning reports over time to understand AI evolution
"""
import json
import os
from datetime import datetime
import glob

def analyze_learning_reports():
    print("=" * 70)
    print("AI LEARNING REPORT ANALYSIS")
    print("Analyzing AI evolution over time through learning reports")
    print("=" * 70)
    
    # Get all learning reports
    reports_path = "models/threat_detection/learning_report_*.json"
    report_files = sorted(glob.glob(reports_path))
    
    if not report_files:
        print("No learning reports found!")
        return
    
    print(f"\nFound {len(report_files)} learning reports")
    print("-" * 50)
    
    reports_data = []
    
    # Load and analyze each report
    for report_file in report_files:
        try:
            with open(report_file, 'r') as f:
                report = json.load(f)
                
            # Extract timestamp from filename for sorting
            filename = os.path.basename(report_file)
            timestamp_str = filename.replace('learning_report_', '').replace('.json', '')
            
            report['filename'] = filename
            report['file_timestamp'] = timestamp_str
            reports_data.append(report)
            
        except Exception as e:
            print(f"Error loading {report_file}: {e}")
    
    # Sort by timestamp
    reports_data.sort(key=lambda x: x['timestamp'])
    
    print(f"\nCHRONOLOGICAL LEARNING ANALYSIS:")
    print("-" * 50)
    
    for i, report in enumerate(reports_data):
        timestamp = report['timestamp']
        filename = report['filename']
        
        print(f"\n{i+1}. Report: {filename}")
        print(f"   Timestamp: {timestamp}")
        
        # Learning metrics
        metrics = report.get('learning_metrics', {})
        patterns_learned = metrics.get('patterns_learned', 0)
        accuracy_improvements = len(metrics.get('accuracy_improvements', []))
        fp_reductions = len(metrics.get('false_positive_reduction', []))
        speed_improvements = len(metrics.get('detection_speed_improvements', []))
        
        print(f"   Patterns Learned: {patterns_learned}")
        print(f"   Accuracy Improvements: {accuracy_improvements}")
        print(f"   False Positive Reductions: {fp_reductions}")
        print(f"   Speed Improvements: {speed_improvements}")
        
        # Model performance summary
        model_perf = report.get('model_performance', {})
        if model_perf:
            avg_accuracy = sum(model['accuracy'] for model in model_perf.values()) / len(model_perf)
            print(f"   Average Model Accuracy: {avg_accuracy:.1%}")
        
        # Pattern statistics
        pattern_stats = report.get('pattern_statistics', {})
        total_patterns = pattern_stats.get('total_patterns', 0)
        patterns_by_type = pattern_stats.get('patterns_by_type', {})
        
        print(f"   Total Patterns: {total_patterns}")
        if patterns_by_type:
            dominant_type = max(patterns_by_type.items(), key=lambda x: x[1])
            print(f"   Dominant Pattern Type: {dominant_type[0]} ({dominant_type[1]} patterns)")
    
    # Evolution analysis
    print(f"\n" + "=" * 70)
    print("EVOLUTION ANALYSIS")
    print("=" * 70)
    
    if len(reports_data) >= 2:
        first_report = reports_data[0]
        latest_report = reports_data[-1]
        
        # Compare first vs latest
        first_patterns = first_report.get('pattern_statistics', {}).get('total_patterns', 0)
        latest_patterns = latest_report.get('pattern_statistics', {}).get('total_patterns', 0)
        pattern_growth = latest_patterns - first_patterns
        
        print(f"Time Period: {first_report['timestamp']} to {latest_report['timestamp']}")
        print(f"Pattern Growth: {first_patterns} → {latest_patterns} (+{pattern_growth})")
        
        # Model accuracy comparison
        first_models = first_report.get('model_performance', {})
        latest_models = latest_report.get('model_performance', {})
        
        print(f"\nModel Accuracy Changes:")
        for model_name in first_models:
            if model_name in latest_models:
                first_acc = first_models[model_name]['accuracy']
                latest_acc = latest_models[model_name]['accuracy']
                change = latest_acc - first_acc
                change_str = f"+{change:.1%}" if change > 0 else f"{change:.1%}"
                print(f"  {model_name}: {first_acc:.1%} → {latest_acc:.1%} ({change_str})")
        
        # Pattern type evolution
        first_pattern_types = first_report.get('pattern_statistics', {}).get('patterns_by_type', {})
        latest_pattern_types = latest_report.get('pattern_statistics', {}).get('patterns_by_type', {})
        
        print(f"\nPattern Type Evolution:")
        all_types = set(first_pattern_types.keys()) | set(latest_pattern_types.keys())
        for pattern_type in all_types:
            first_count = first_pattern_types.get(pattern_type, 0)
            latest_count = latest_pattern_types.get(pattern_type, 0)
            growth = latest_count - first_count
            print(f"  {pattern_type}: {first_count} → {latest_count} (+{growth})")
    
    # Learning velocity analysis
    print(f"\n" + "=" * 70)
    print("LEARNING VELOCITY ANALYSIS")
    print("=" * 70)
    
    if len(reports_data) >= 3:
        # Calculate learning rate between reports
        for i in range(1, len(reports_data)):
            prev_report = reports_data[i-1]
            curr_report = reports_data[i]
            
            prev_patterns = prev_report.get('pattern_statistics', {}).get('total_patterns', 0)
            curr_patterns = curr_report.get('pattern_statistics', {}).get('total_patterns', 0)
            pattern_diff = curr_patterns - prev_patterns
            
            # Time difference (simplified)
            prev_time = prev_report['timestamp']
            curr_time = curr_report['timestamp']
            
            print(f"Session {i}: +{pattern_diff} patterns learned")
            
            # Check for learning acceleration/deceleration
            if i > 1:
                prev_prev_report = reports_data[i-2]
                prev_prev_patterns = prev_prev_report.get('pattern_statistics', {}).get('total_patterns', 0)
                prev_diff = prev_patterns - prev_prev_patterns
                
                if pattern_diff > prev_diff:
                    print(f"  📈 Learning accelerating (+{pattern_diff - prev_diff} more than previous)")
                elif pattern_diff < prev_diff:
                    print(f"  📉 Learning decelerating ({prev_diff - pattern_diff} fewer than previous)")
                else:
                    print(f"  ➡️  Learning rate stable")
    
    # Anomaly detection in learning
    print(f"\n" + "=" * 70)
    print("LEARNING ANOMALY DETECTION")
    print("=" * 70)
    
    # Check for unusual patterns in learning
    pattern_counts = [r.get('pattern_statistics', {}).get('total_patterns', 0) for r in reports_data]
    if len(pattern_counts) > 1:
        max_patterns = max(pattern_counts)
        min_patterns = min(pattern_counts)
        
        # Check for sudden spikes or drops
        for i, report in enumerate(reports_data):
            patterns = pattern_counts[i]
            if patterns == max_patterns and patterns > min_patterns * 2:
                print(f"🔥 Learning spike detected in {report['filename']}: {patterns} patterns")
            elif patterns == min_patterns and max_patterns > patterns * 2:
                print(f"❄️  Learning valley detected in {report['filename']}: {patterns} patterns")
    
    # Current state assessment
    print(f"\n" + "=" * 70)
    print("CURRENT AI STATE ASSESSMENT")
    print("=" * 70)
    
    if reports_data:
        latest = reports_data[-1]
        latest_patterns = latest.get('pattern_statistics', {}).get('patterns_by_type', {})
        
        # Check for bias toward specific threat types
        if latest_patterns:
            total = sum(latest_patterns.values())
            for threat_type, count in latest_patterns.items():
                percentage = (count / total) * 100
                if percentage > 80:
                    print(f"⚠️  BIAS DETECTED: {percentage:.1f}% of patterns are '{threat_type}'")
                    print(f"   This may indicate overlearning or classification bias")
        
        # Overall assessment
        total_patterns = latest.get('pattern_statistics', {}).get('total_patterns', 0)
        if total_patterns > 20:
            print(f"✅ Rich learning: {total_patterns} patterns accumulated")
        elif total_patterns > 5:
            print(f"🔄 Active learning: {total_patterns} patterns accumulated")
        else:
            print(f"🌱 Early learning: {total_patterns} patterns accumulated")

if __name__ == "__main__":
    analyze_learning_reports()