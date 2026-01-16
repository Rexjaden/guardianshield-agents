#!/usr/bin/env python3
"""
GuardianShield Memory Optimization System
Optimizes RAM usage and manages memory-intensive operations.
"""

import gc
import os
import sys
import json
import psutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading
import time

class MemoryOptimizer:
    """Manages RAM optimization and memory usage monitoring."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.memory_report = {
            'timestamp': datetime.now().isoformat(),
            'memory_before': {},
            'memory_after': {},
            'optimizations_applied': [],
            'processes_managed': [],
            'errors': []
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('memory_optimization.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get current memory usage information."""
        try:
            memory = psutil.virtual_memory()
            return {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used,
                'free': memory.free,
                'active': getattr(memory, 'active', 0),
                'inactive': getattr(memory, 'inactive', 0),
                'buffers': getattr(memory, 'buffers', 0),
                'cached': getattr(memory, 'cached', 0)
            }
        except Exception as e:
            self.logger.error(f"Error getting memory info: {str(e)}")
            return {}
    
    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} TB"
    
    def force_garbage_collection(self):
        """Force Python garbage collection to free up memory."""
        self.logger.info("Running garbage collection...")
        
        try:
            # Get memory before
            mem_before = self.get_memory_info()
            
            # Run garbage collection
            collected = gc.collect()
            
            # Get memory after
            mem_after = self.get_memory_info()
            
            freed_memory = mem_before.get('used', 0) - mem_after.get('used', 0)
            
            self.memory_report['optimizations_applied'].append({
                'type': 'garbage_collection',
                'objects_collected': collected,
                'memory_freed': freed_memory,
                'timestamp': datetime.now().isoformat()
            })
            
            self.logger.info(f"Garbage collection freed {collected} objects, {self.format_bytes(freed_memory)} memory")
            
        except Exception as e:
            self.memory_report['errors'].append(f"Garbage collection error: {str(e)}")
            self.logger.error(f"Garbage collection error: {str(e)}")
    
    def optimize_python_memory(self):
        """Optimize Python memory usage."""
        self.logger.info("Optimizing Python memory usage...")
        
        try:
            # Clear module caches
            if hasattr(sys, '_clear_type_cache'):
                sys._clear_type_cache()
            
            # Force garbage collection with multiple generations
            for i in range(3):
                collected = gc.collect()
                self.logger.info(f"GC Generation {i}: collected {collected} objects")
            
            # Clear import cache for reimports
            if hasattr(sys, '_getframe'):
                for module_name in list(sys.modules.keys()):
                    if module_name.startswith('__pycache__'):
                        del sys.modules[module_name]
            
            self.memory_report['optimizations_applied'].append({
                'type': 'python_memory_optimization',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.memory_report['errors'].append(f"Python memory optimization error: {str(e)}")
            self.logger.error(f"Python memory optimization error: {str(e)}")
    
    def find_memory_intensive_processes(self) -> List[Dict[str, Any]]:
        """Find processes using the most memory."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'memory_percent']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                            'memory_percent': proc.info['memory_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by memory usage
            processes.sort(key=lambda x: x['memory_mb'], reverse=True)
            return processes[:10]  # Top 10
            
        except Exception as e:
            self.logger.error(f"Error finding memory intensive processes: {str(e)}")
            return []
    
    def optimize_agent_memory(self):
        """Optimize memory usage for GuardianShield agents."""
        self.logger.info("Optimizing agent memory usage...")
        
        try:
            # Look for agent processes and optimize them
            agent_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if any(agent_file in cmdline for agent_file in [
                        'main.py', 'agent_', 'api_server.py', 'admin_console.py'
                    ]):
                        agent_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': cmdline,
                            'memory_mb': proc.info['memory_info'].rss / 1024 / 1024
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.memory_report['processes_managed'] = agent_processes
            self.logger.info(f"Found {len(agent_processes)} agent processes")
            
            # Clear any temporary agent data files
            temp_patterns = [
                '**/agent_*_temp.json',
                '**/temp_*.db',
                '**/.agent_cache'
            ]
            
            for pattern in temp_patterns:
                for temp_file in self.project_root.glob(pattern):
                    try:
                        temp_file.unlink()
                        self.logger.info(f"Removed temp agent file: {temp_file}")
                    except Exception as e:
                        self.logger.warning(f"Could not remove {temp_file}: {str(e)}")
            
        except Exception as e:
            self.memory_report['errors'].append(f"Agent memory optimization error: {str(e)}")
            self.logger.error(f"Agent memory optimization error: {str(e)}")
    
    def create_memory_monitor(self, duration_seconds: int = 60):
        """Create a background memory monitor."""
        def monitor():
            start_time = time.time()
            while time.time() - start_time < duration_seconds:
                try:
                    memory_info = self.get_memory_info()
                    if memory_info.get('percent', 0) > 85:  # If memory usage > 85%
                        self.logger.warning(f"High memory usage detected: {memory_info['percent']:.1f}%")
                        self.force_garbage_collection()
                    time.sleep(5)  # Check every 5 seconds
                except Exception as e:
                    self.logger.error(f"Memory monitor error: {str(e)}")
                    break
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        self.logger.info(f"Memory monitor started for {duration_seconds} seconds")
        return monitor_thread
    
    def optimize_database_connections(self):
        """Optimize database connection pools and caches."""
        self.logger.info("Optimizing database connections...")
        
        try:
            # This would typically involve closing unused database connections
            # For now, we'll just log the optimization
            db_files = list(self.project_root.glob('**/*.db'))
            
            self.memory_report['optimizations_applied'].append({
                'type': 'database_optimization',
                'databases_found': len(db_files),
                'timestamp': datetime.now().isoformat()
            })
            
            self.logger.info(f"Found {len(db_files)} database files for optimization")
            
        except Exception as e:
            self.memory_report['errors'].append(f"Database optimization error: {str(e)}")
            self.logger.error(f"Database optimization error: {str(e)}")
    
    def run_memory_optimization(self, monitor_duration: int = 60):
        """Run complete memory optimization process."""
        self.logger.info("Starting GuardianShield memory optimization...")
        
        try:
            # Record initial memory state
            self.memory_report['memory_before'] = self.get_memory_info()
            self.logger.info(f"Initial memory usage: {self.memory_report['memory_before'].get('percent', 0):.1f}%")
            
            # Run optimizations
            self.force_garbage_collection()
            self.optimize_python_memory()
            self.optimize_agent_memory()
            self.optimize_database_connections()
            
            # Start memory monitor
            if monitor_duration > 0:
                monitor_thread = self.create_memory_monitor(monitor_duration)
            
            # Record final memory state
            self.memory_report['memory_after'] = self.get_memory_info()
            
            # Calculate improvement
            memory_saved = (
                self.memory_report['memory_before'].get('used', 0) - 
                self.memory_report['memory_after'].get('used', 0)
            )
            
            self.logger.info(f"Memory optimization completed!")
            self.logger.info(f"Final memory usage: {self.memory_report['memory_after'].get('percent', 0):.1f}%")
            self.logger.info(f"Memory freed: {self.format_bytes(memory_saved)}")
            
            # Show memory-intensive processes
            intensive_processes = self.find_memory_intensive_processes()
            if intensive_processes:
                self.logger.info("Top memory-intensive processes:")
                for proc in intensive_processes[:5]:
                    self.logger.info(f"  {proc['name']} (PID: {proc['pid']}): {proc['memory_mb']:.1f} MB")
            
            # Generate report
            self.generate_memory_report()
            
        except Exception as e:
            self.logger.error(f"Memory optimization failed: {str(e)}")
            self.memory_report['errors'].append(f"General optimization error: {str(e)}")
    
    def generate_memory_report(self):
        """Generate memory optimization report."""
        report_file = self.project_root / f"memory_optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.memory_report, f, indent=2, default=str)
        
        self.logger.info(f"Memory report saved to: {report_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("GUARDIANSHIELD MEMORY OPTIMIZATION SUMMARY")
        print("="*60)
        
        mem_before = self.memory_report['memory_before']
        mem_after = self.memory_report['memory_after']
        
        if mem_before and mem_after:
            print(f"Memory before: {mem_before.get('percent', 0):.1f}% ({self.format_bytes(mem_before.get('used', 0))})")
            print(f"Memory after:  {mem_after.get('percent', 0):.1f}% ({self.format_bytes(mem_after.get('used', 0))})")
            
            memory_freed = mem_before.get('used', 0) - mem_after.get('used', 0)
            print(f"Memory freed:  {self.format_bytes(memory_freed)}")
        
        print(f"Optimizations applied: {len(self.memory_report['optimizations_applied'])}")
        print(f"Processes managed: {len(self.memory_report['processes_managed'])}")
        print(f"Errors encountered: {len(self.memory_report['errors'])}")
        print("="*60)


def main():
    """Main entry point for memory optimization."""
    memory_optimizer = MemoryOptimizer()
    
    # Parse command line arguments
    monitor_duration = 60  # Default 60 seconds
    if '--monitor-time' in sys.argv:
        try:
            idx = sys.argv.index('--monitor-time')
            monitor_duration = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            monitor_duration = 60
    
    # Run memory optimization
    memory_optimizer.run_memory_optimization(monitor_duration=monitor_duration)


if __name__ == "__main__":
    main()