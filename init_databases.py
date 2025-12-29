"""
Database initialization script for GuardianShield agents
"""
import sqlite3
import os

def initialize_databases():
    """Initialize all required databases for the GuardianShield system"""
    
    # Create databases directory if not exists
    os.makedirs('./databases', exist_ok=True)
    
    databases = [
        './databases/threat_intelligence.db',
        './databases/analytics.db', 
        './databases/security_orchestration.db',
        './databases/dmer_monitoring.db',
        './databases/behavioral_data.db'
    ]
    
    for db_path in databases:
        try:
            db = sqlite3.connect(db_path)
            db.execute('CREATE TABLE IF NOT EXISTS system_info (id INTEGER PRIMARY KEY, name TEXT, value TEXT)')
            db.execute('INSERT OR REPLACE INTO system_info (id, name, value) VALUES (1, "initialized", "true")')
            db.commit()
            db.close()
            print(f'✅ Database created: {db_path}')
        except Exception as e:
            print(f'❌ Error creating {db_path}: {e}')
    
    print('✅ All databases initialized successfully')

if __name__ == "__main__":
    initialize_databases()