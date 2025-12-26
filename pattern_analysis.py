"""
Pattern Database Analysis Tool
Analyze what the AI agents have been learning from during their cycles
"""
import sqlite3
import json
from datetime import datetime
import sys
sys.path.append('agents')

def analyze_pattern_database():
    print("=" * 70)
    print("AI PATTERN DATABASE ANALYSIS")
    print("Examining what the agents have learned over time")
    print("=" * 70)
    
    # Connect to the pattern database
    db_path = "models/threat_detection/patterns.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get total pattern count
        cursor.execute("SELECT COUNT(*) FROM threat_patterns")
        total_patterns = cursor.fetchone()[0]
        print(f"\nTotal Patterns Stored: {total_patterns}")
        
        if total_patterns == 0:
            print("No patterns found in database. AI agents may be starting fresh.")
            return
            
        # Get patterns by threat type
        cursor.execute("""
            SELECT threat_type, COUNT(*) as count, AVG(confidence) as avg_confidence, 
                   AVG(accuracy) as avg_accuracy, SUM(occurrences) as total_occurrences
            FROM threat_patterns 
            GROUP BY threat_type 
            ORDER BY count DESC
        """)
        
        patterns_by_type = cursor.fetchall()
        
        print(f"\nPATTERN DISTRIBUTION BY THREAT TYPE:")
        print("-" * 50)
        for threat_type, count, avg_conf, avg_acc, total_occ in patterns_by_type:
            print(f"{threat_type}:")
            print(f"  Patterns: {count}")
            print(f"  Average Confidence: {avg_conf:.3f}")
            print(f"  Average Accuracy: {avg_acc:.3f}")
            print(f"  Total Occurrences: {total_occ}")
            print()
        
        # Get most recent patterns
        cursor.execute("""
            SELECT threat_type, confidence, accuracy, occurrences, first_seen, last_seen, false_positives
            FROM threat_patterns 
            ORDER BY last_seen DESC 
            LIMIT 10
        """)
        
        recent_patterns = cursor.fetchall()
        
        print(f"MOST RECENT PATTERN ACTIVITY (Last 10):")
        print("-" * 50)
        for i, (threat_type, conf, acc, occ, first_seen, last_seen, fps) in enumerate(recent_patterns, 1):
            print(f"{i}. {threat_type}")
            print(f"   Confidence: {conf:.3f}")
            print(f"   Accuracy: {acc:.3f}")
            print(f"   Occurrences: {occ}")
            print(f"   False Positives: {fps}")
            print(f"   Last Seen: {last_seen}")
            print()
        
        # Get high-confidence patterns
        cursor.execute("""
            SELECT threat_type, confidence, accuracy, occurrences, false_positives
            FROM threat_patterns 
            WHERE confidence > 0.8
            ORDER BY confidence DESC
        """)
        
        high_conf_patterns = cursor.fetchall()
        
        print(f"HIGH CONFIDENCE PATTERNS (>80%):")
        print("-" * 50)
        for threat_type, conf, acc, occ, fps in high_conf_patterns:
            fp_rate = (fps / occ * 100) if occ > 0 else 0
            print(f"{threat_type}: {conf:.1%} confidence, {acc:.1%} accuracy")
            print(f"  Occurrences: {occ}, False Positive Rate: {fp_rate:.1f}%")
        
        # Check learning history
        cursor.execute("SELECT COUNT(*) FROM learning_history")
        learning_events = cursor.fetchone()[0]
        
        if learning_events > 0:
            print(f"\nLEARNING HISTORY:")
            print("-" * 50)
            print(f"Total Learning Events: {learning_events}")
            
            cursor.execute("""
                SELECT event_type, COUNT(*) as count, AVG(improvement_score) as avg_improvement
                FROM learning_history 
                GROUP BY event_type 
                ORDER BY count DESC
            """)
            
            learning_by_type = cursor.fetchall()
            for event_type, count, avg_improvement in learning_by_type:
                print(f"{event_type}: {count} events, avg improvement: {avg_improvement:.3f}")
            
            # Get recent learning events
            cursor.execute("""
                SELECT timestamp, event_type, description, improvement_score
                FROM learning_history 
                ORDER BY timestamp DESC 
                LIMIT 5
            """)
            
            recent_learning = cursor.fetchall()
            print(f"\nRecent Learning Events:")
            for timestamp, event_type, description, improvement in recent_learning:
                print(f"  {timestamp}: {event_type} - {description}")
                print(f"    Improvement Score: {improvement}")
        
        # Pattern effectiveness analysis
        cursor.execute("""
            SELECT 
                AVG(CASE WHEN false_positives = 0 THEN 1.0 ELSE 0.0 END) as zero_fp_rate,
                AVG(accuracy) as overall_accuracy,
                AVG(confidence) as overall_confidence,
                AVG(CAST(false_positives AS FLOAT) / CAST(occurrences AS FLOAT)) as avg_fp_rate
            FROM threat_patterns 
            WHERE occurrences > 0
        """)
        
        effectiveness = cursor.fetchone()
        if effectiveness:
            zero_fp_rate, overall_acc, overall_conf, avg_fp_rate = effectiveness
            print(f"\nPATTERN EFFECTIVENESS METRICS:")
            print("-" * 50)
            print(f"Patterns with Zero False Positives: {zero_fp_rate:.1%}")
            print(f"Overall Pattern Accuracy: {overall_acc:.1%}")
            print(f"Overall Pattern Confidence: {overall_conf:.1%}")
            print(f"Average False Positive Rate: {avg_fp_rate:.1%}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error analyzing patterns: {e}")

if __name__ == "__main__":
    analyze_pattern_database()