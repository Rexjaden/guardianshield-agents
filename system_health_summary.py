#!/usr/bin/env python3
"""
GuardianShield System Optimization Summary
Provides overall system health and optimization status.
"""

import os
import json
import psutil
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class SystemOptimizationSummary:
    """Provides comprehensive system optimization status and recommendations."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.summary = {
            'timestamp': datetime.now().isoformat(),
            'system_status': {},
            'optimization_results': {},
            'recommendations': [],
            'database_status': {},
            'memory_status': {},
            'storage_status': {}
        }
    
    def check_system_resources(self):
        """Check current system resource usage."""
        try:
            # Memory info
            memory = psutil.virtual_memory()
            self.summary['memory_status'] = {
                'total_gb': round(memory.total / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'percent_used': memory.percent,
                'status': 'optimal' if memory.percent < 80 else 'high' if memory.percent < 90 else 'critical'
            }
            
            # Disk info
            disk = psutil.disk_usage(str(self.project_root))
            self.summary['storage_status'] = {
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'percent_used': round((disk.used / disk.total) * 100, 1),
                'status': 'optimal' if (disk.used / disk.total) < 0.8 else 'high' if (disk.used / disk.total) < 0.9 else 'critical'
            }
            
            # CPU info
            cpu_percent = psutil.cpu_percent(interval=1)
            self.summary['system_status'] = {
                'cpu_percent': cpu_percent,
                'cpu_count': psutil.cpu_count(),
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else 'N/A (Windows)',
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
            
        except Exception as e:
            self.summary['recommendations'].append(f"Error checking system resources: {str(e)}")
    
    def check_database_health(self):
        """Check the health of all SQLite databases."""
        db_files = list(self.project_root.glob('**/*.db'))
        database_info = []
        
        for db_file in db_files:
            try:
                size_mb = round(db_file.stat().st_size / (1024*1024), 2)
                
                # Quick integrity check
                conn = sqlite3.connect(str(db_file))
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                integrity = cursor.fetchone()[0]
                
                # Get table count
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                conn.close()
                
                database_info.append({
                    'name': db_file.name,
                    'size_mb': size_mb,
                    'tables': len(tables),
                    'integrity': integrity,
                    'status': 'healthy' if integrity == 'ok' else 'needs_attention'
                })
                
            except Exception as e:
                database_info.append({
                    'name': db_file.name,
                    'size_mb': 0,
                    'tables': 0,
                    'integrity': f'Error: {str(e)}',
                    'status': 'error'
                })
        
        self.summary['database_status'] = {
            'total_databases': len(db_files),
            'total_size_mb': round(sum(db['size_mb'] for db in database_info), 2),
            'healthy_databases': len([db for db in database_info if db['status'] == 'healthy']),
            'databases': database_info
        }
    
    def check_recent_optimizations(self):
        """Check for recent optimization reports."""
        optimization_files = [
            'cache_cleanup_report_*.json',
            'memory_optimization_report_*.json'
        ]
        
        recent_optimizations = []
        
        for pattern in optimization_files:
            for report_file in self.project_root.glob(pattern):
                try:
                    with open(report_file, 'r') as f:
                        report_data = json.load(f)
                    
                    recent_optimizations.append({
                        'type': 'cache_cleanup' if 'cache_cleanup' in report_file.name else 'memory_optimization',
                        'timestamp': report_data.get('timestamp', 'unknown'),
                        'file': report_file.name,
                        'summary': self._extract_optimization_summary(report_data)
                    })
                except Exception as e:
                    continue
        
        # Sort by timestamp (most recent first)
        recent_optimizations.sort(key=lambda x: x['timestamp'], reverse=True)
        self.summary['optimization_results'] = recent_optimizations[:5]  # Keep last 5
    
    def _extract_optimization_summary(self, report_data: Dict) -> Dict:
        """Extract key metrics from optimization report."""
        summary = {}
        
        if 'space_freed' in report_data:
            summary['space_freed_mb'] = round(report_data['space_freed'] / (1024*1024), 2)
            summary['files_cleaned'] = len(report_data.get('files_cleaned', []))
            summary['databases_optimized'] = len(report_data.get('databases_optimized', []))
        
        if 'memory_before' in report_data and 'memory_after' in report_data:
            mem_before = report_data['memory_before']
            mem_after = report_data['memory_after']
            if mem_before and mem_after:
                summary['memory_freed_mb'] = round((mem_before.get('used', 0) - mem_after.get('used', 0)) / (1024*1024), 2)
                summary['memory_improvement'] = f"{mem_before.get('percent', 0):.1f}% -> {mem_after.get('percent', 0):.1f}%"
        
        return summary
    
    def generate_recommendations(self):
        """Generate optimization recommendations based on current status."""
        recommendations = []
        
        # Memory recommendations
        memory_status = self.summary['memory_status']
        if memory_status['status'] == 'critical':
            recommendations.append("🔴 CRITICAL: Memory usage is very high (>90%). Consider running memory optimization or restarting services.")
        elif memory_status['status'] == 'high':
            recommendations.append("🟡 WARNING: Memory usage is high (>80%). Consider running memory optimization.")
        else:
            recommendations.append("✅ Memory usage is optimal.")
        
        # Storage recommendations
        storage_status = self.summary['storage_status']
        if storage_status['status'] == 'critical':
            recommendations.append("🔴 CRITICAL: Disk space is very low (>90%). Run cache cleanup immediately.")
        elif storage_status['status'] == 'high':
            recommendations.append("🟡 WARNING: Disk space is getting low (>80%). Consider running cache cleanup.")
        else:
            recommendations.append("✅ Disk space is adequate.")
        
        # Database recommendations
        db_status = self.summary['database_status']
        unhealthy_dbs = len([db for db in db_status.get('databases', []) if db['status'] != 'healthy'])
        if unhealthy_dbs > 0:
            recommendations.append(f"🔴 {unhealthy_dbs} database(s) need attention. Run database optimization.")
        else:
            recommendations.append("✅ All databases are healthy.")
        
        # Recent optimization check
        recent_opts = self.summary['optimization_results']
        if not recent_opts:
            recommendations.append("💡 No recent optimizations found. Consider running cache cleanup and memory optimization.")
        else:
            last_opt = datetime.fromisoformat(recent_opts[0]['timestamp'].replace('Z', '+00:00').replace('+00:00', ''))
            days_ago = (datetime.now() - last_opt).days
            if days_ago > 7:
                recommendations.append(f"💡 Last optimization was {days_ago} days ago. Consider running maintenance.")
        
        # Agent-specific recommendations
        agent_processes = len([p for p in psutil.process_iter(['name']) if 'python' in p.info['name'].lower()])
        if agent_processes > 5:
            recommendations.append(f"💡 Found {agent_processes} Python processes. Consider reviewing running agents.")
        
        self.summary['recommendations'] = recommendations
    
    def generate_report(self):
        """Generate the complete system optimization summary."""
        print("🛡️ GUARDIANSHIELD SYSTEM OPTIMIZATION SUMMARY")
        print("=" * 60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # System resources
        print("🖥️ SYSTEM RESOURCES")
        print("-" * 30)
        mem = self.summary['memory_status']
        storage = self.summary['storage_status']
        print(f"Memory: {mem['used_gb']:.1f}GB / {mem['total_gb']:.1f}GB ({mem['percent_used']:.1f}%) - {mem['status'].upper()}")
        print(f"Storage: {storage['used_gb']:.1f}GB / {storage['total_gb']:.1f}GB ({storage['percent_used']:.1f}%) - {storage['status'].upper()}")
        print(f"CPU: {self.summary['system_status']['cpu_percent']:.1f}% ({self.summary['system_status']['cpu_count']} cores)")
        print()
        
        # Database status
        print("🗄️ DATABASE STATUS")
        print("-" * 30)
        db = self.summary['database_status']
        print(f"Total databases: {db['total_databases']}")
        print(f"Total size: {db['total_size_mb']:.1f} MB")
        print(f"Healthy: {db['healthy_databases']}/{db['total_databases']}")
        print()
        
        # Recent optimizations
        print("🔧 RECENT OPTIMIZATIONS")
        print("-" * 30)
        if self.summary['optimization_results']:
            for opt in self.summary['optimization_results'][:3]:
                opt_type = opt['type'].replace('_', ' ').title()
                timestamp = datetime.fromisoformat(opt['timestamp'].replace('Z', '+00:00').replace('+00:00', ''))
                days_ago = (datetime.now() - timestamp).days
                print(f"{opt_type}: {days_ago} days ago")
                summary = opt['summary']
                if 'space_freed_mb' in summary:
                    print(f"  • Space freed: {summary['space_freed_mb']:.1f} MB")
                if 'memory_freed_mb' in summary:
                    print(f"  • Memory freed: {summary['memory_freed_mb']:.1f} MB")
        else:
            print("No recent optimizations found")
        print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS")
        print("-" * 30)
        for rec in self.summary['recommendations']:
            print(f"  {rec}")
        print()
        
        print("=" * 60)
        print("💾 For database and storage management preparation, system is optimized!")
        
        # Save detailed report
        report_file = self.project_root / f"system_optimization_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.summary, f, indent=2, default=str)
        print(f"📊 Detailed report saved to: {report_file.name}")
    
    def run_summary(self):
        """Run the complete system optimization summary."""
        self.check_system_resources()
        self.check_database_health()
        self.check_recent_optimizations()
        self.generate_recommendations()
        self.generate_report()


def main():
    """Main entry point for system optimization summary."""
    summary_generator = SystemOptimizationSummary()
    summary_generator.run_summary()


if __name__ == "__main__":
    main()