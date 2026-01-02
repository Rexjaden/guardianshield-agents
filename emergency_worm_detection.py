#!/usr/bin/env python3
"""
CRITICAL SECURITY RESPONSE: ANTI-WORM & MALWARE DETECTION
Code tampering detected - deploying full containment protocols
PRIORITY: ELIMINATE POTENTIAL WORM/MALWARE THREATS
"""

import json
import os
import sys
import hashlib
import time
import subprocess
import psutil
import datetime
from pathlib import Path
import re

class WormDetectionSystem:
    """🚨 EMERGENCY WORM/MALWARE DETECTION & CONTAINMENT SYSTEM"""
    
    def __init__(self):
        self.alert_level = "🔴 CRITICAL"
        self.threats_found = []
        self.quarantine_list = []
        self.forensics_data = {
            'scan_start': datetime.datetime.now().isoformat(),
            'threat_signatures': [],
            'modified_files': [],
            'suspicious_processes': [],
            'network_anomalies': []
        }
        
    def deep_malware_scan(self):
        """Comprehensive malware signature detection"""
        print("🔍 DEEP MALWARE SCAN - Checking for malicious signatures...")
        
        malicious_patterns = [
            r'eval\s*\(',  # Code execution
            r'exec\s*\(',  # Code execution
            r'__import__\s*\(',  # Dynamic imports
            r'subprocess\.call',  # System calls
            r'os\.system',  # OS commands
            r'socket\.socket',  # Network connections
            r'base64\.decode',  # Encoded payloads
            r'urllib.*request',  # Web requests
            r'requests\.get|requests\.post',  # HTTP requests
            r'threading\.Thread',  # Background threads
            r'multiprocessing',  # Process spawning
            r'tempfile',  # Temporary files
            r'shutil\.rmtree',  # File deletion
            r'os\.remove',  # File deletion
            r'pickle\.loads',  # Deserialization
        ]
        
        suspicious_files = []
        
        for root, dirs, files in os.walk('.'):
            # Skip common directories that shouldn't contain malware
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                if file.endswith(('.py', '.js', '.bat', '.sh', '.ps1')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        # Check for malicious patterns
                        threats_in_file = []
                        for pattern in malicious_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                threats_in_file.append(pattern)
                                
                        if threats_in_file:
                            suspicious_files.append({
                                'file': file_path,
                                'threats': threats_in_file,
                                'size': len(content),
                                'modified': os.path.getmtime(file_path),
                                'threat_level': 'HIGH' if len(threats_in_file) > 3 else 'MEDIUM'
                            })
                            
                    except Exception as e:
                        suspicious_files.append({
                            'file': file_path,
                            'error': str(e),
                            'threat_level': 'UNKNOWN'
                        })
                        
        self.forensics_data['threat_signatures'] = suspicious_files
        return suspicious_files
        
    def detect_file_tampering(self):
        """Detect unauthorized file modifications"""
        print("📁 FILE TAMPERING DETECTION - Analyzing recent modifications...")
        
        recently_modified = []
        current_time = time.time()
        
        # Check for files modified in the last hour
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    mod_time = os.path.getmtime(file_path)
                    if current_time - mod_time < 3600:  # Last hour
                        recently_modified.append({
                            'file': file_path,
                            'modified': datetime.datetime.fromtimestamp(mod_time).isoformat(),
                            'size': os.path.getsize(file_path),
                            'suspicious': file.endswith(('.tmp', '.temp')) or 'temp' in file.lower()
                        })
                except Exception:
                    continue
                    
        # Sort by modification time (most recent first)
        recently_modified.sort(key=lambda x: x['modified'], reverse=True)
        
        self.forensics_data['modified_files'] = recently_modified[:50]  # Top 50
        return recently_modified[:20]  # Return top 20 for display
        
    def detect_worm_behavior(self):
        """Detect worm-like behavior patterns"""
        print("🐛 WORM BEHAVIOR DETECTION - Analyzing process patterns...")
        
        suspicious_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'cpu_percent', 'memory_percent']):
            try:
                proc_info = proc.info
                
                # Check for suspicious process names
                suspicious_names = ['temp', 'svchost', 'explorer', 'winlogon', 'csrss']
                suspicious_behavior = False
                
                # Check for processes with suspicious characteristics
                if any(name in proc_info['name'].lower() for name in suspicious_names):
                    suspicious_behavior = True
                    
                # High resource usage
                if proc_info['cpu_percent'] > 50 or proc_info['memory_percent'] > 30:
                    suspicious_behavior = True
                    
                # Multiple instances of same process
                same_name_count = sum(1 for p in psutil.process_iter() if p.name() == proc_info['name'])
                if same_name_count > 5:
                    suspicious_behavior = True
                    
                if suspicious_behavior:
                    suspicious_processes.append({
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'cmdline': ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else 'N/A',
                        'cpu_usage': proc_info['cpu_percent'],
                        'memory_usage': proc_info['memory_percent'],
                        'create_time': datetime.datetime.fromtimestamp(proc_info['create_time']).isoformat(),
                        'threat_level': 'HIGH'
                    })
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        self.forensics_data['suspicious_processes'] = suspicious_processes
        return suspicious_processes
        
    def check_network_exfiltration(self):
        """Check for potential data exfiltration"""
        print("🌐 NETWORK EXFILTRATION CHECK - Monitoring outbound connections...")
        
        network_anomalies = []
        
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'ESTABLISHED' and conn.raddr:
                try:
                    # Check for connections to suspicious ports
                    suspicious_ports = [21, 22, 23, 80, 443, 8080, 9999, 1337]
                    
                    if conn.raddr.port in suspicious_ports:
                        process_name = "Unknown"
                        if conn.pid:
                            try:
                                process_name = psutil.Process(conn.pid).name()
                            except:
                                pass
                                
                        network_anomalies.append({
                            'local': f"{conn.laddr.ip}:{conn.laddr.port}",
                            'remote': f"{conn.raddr.ip}:{conn.raddr.port}",
                            'process': process_name,
                            'pid': conn.pid,
                            'status': conn.status,
                            'threat_level': 'HIGH' if conn.raddr.port in [21, 22, 23, 9999, 1337] else 'MEDIUM'
                        })
                        
                except Exception:
                    continue
                    
        self.forensics_data['network_anomalies'] = network_anomalies
        return network_anomalies
        
    def quarantine_threats(self, threats):
        """Quarantine identified threats"""
        print("🔒 THREAT QUARANTINE - Isolating suspicious files...")
        
        quarantine_dir = Path("QUARANTINE_" + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
        quarantine_dir.mkdir(exist_ok=True)
        
        quarantined = []
        
        for threat in threats:
            if isinstance(threat, dict) and 'file' in threat:
                try:
                    source_file = Path(threat['file'])
                    if source_file.exists() and threat.get('threat_level') in ['HIGH', 'CRITICAL']:
                        # Move file to quarantine
                        dest_file = quarantine_dir / source_file.name
                        source_file.rename(dest_file)
                        
                        quarantined.append({
                            'original_path': str(source_file),
                            'quarantine_path': str(dest_file),
                            'timestamp': datetime.datetime.now().isoformat(),
                            'reason': 'High threat level detected'
                        })
                        
                except Exception as e:
                    print(f"⚠️ Failed to quarantine {threat['file']}: {e}")
                    
        return quarantined
        
    def generate_forensics_report(self):
        """Generate comprehensive forensics report"""
        self.forensics_data['scan_complete'] = datetime.datetime.now().isoformat()
        self.forensics_data['total_threats'] = len(self.threats_found)
        
        # Calculate risk level
        high_threats = sum(1 for t in self.threats_found if t.get('threat_level') == 'HIGH')
        critical_threats = sum(1 for t in self.threats_found if t.get('threat_level') == 'CRITICAL')
        
        if critical_threats > 0:
            risk_level = "🔴 CRITICAL"
        elif high_threats > 5:
            risk_level = "🟠 HIGH"
        elif high_threats > 0:
            risk_level = "🟡 ELEVATED"
        else:
            risk_level = "🟢 LOW"
            
        self.forensics_data['risk_assessment'] = risk_level
        
        # Save forensics report
        report_file = f"CODE_TAMPERING_FORENSICS_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.forensics_data, f, indent=2)
            
        return report_file, risk_level

def execute_emergency_worm_scan():
    """Execute comprehensive worm/malware detection"""
    
    print("🚨" + "="*70 + "🚨")
    print("     EMERGENCY WORM/MALWARE DETECTION PROTOCOL")
    print("     CODE TAMPERING DETECTED - CONTAINMENT ACTIVE")  
    print("     SCANNING FOR MALICIOUS CODE INJECTION")
    print("🚨" + "="*70 + "🚨")
    print()
    
    detector = WormDetectionSystem()
    
    # Execute all detection protocols
    print("🔍 Phase 1: Deep malware signature scan...")
    malware_threats = detector.deep_malware_scan()
    
    print(f"📁 Phase 2: File tampering detection...")
    modified_files = detector.detect_file_tampering()
    
    print("🐛 Phase 3: Worm behavior analysis...")
    worm_behavior = detector.detect_worm_behavior()
    
    print("🌐 Phase 4: Network exfiltration check...")
    network_threats = detector.check_network_exfiltration()
    
    # Compile all threats
    all_threats = malware_threats + worm_behavior + network_threats
    detector.threats_found = all_threats
    
    # Generate forensics report
    report_file, risk_level = detector.generate_forensics_report()
    
    print("\n" + "="*70)
    print("🚨 WORM/MALWARE SCAN RESULTS:")
    print(f"📊 Risk Level: {risk_level}")
    print(f"🔍 Malware Signatures Found: {len(malware_threats)}")
    print(f"📁 Recently Modified Files: {len(modified_files)}")
    print(f"🐛 Suspicious Processes: {len(worm_behavior)}")
    print(f"🌐 Network Anomalies: {len(network_threats)}")
    print(f"📋 Forensics Report: {report_file}")
    
    if malware_threats:
        print("\n🚨 HIGH-PRIORITY MALWARE THREATS DETECTED:")
        for threat in malware_threats[:5]:
            print(f"  ⚠️ {threat['file']} - {len(threat.get('threats', []))} suspicious patterns")
            
    if modified_files:
        print(f"\n📁 RECENT FILE MODIFICATIONS ({len(modified_files)} files):")
        for mod_file in modified_files[:5]:
            print(f"  📝 {mod_file['file']} - {mod_file['modified']}")
            
    if worm_behavior:
        print(f"\n🐛 SUSPICIOUS PROCESS ACTIVITY:")
        for proc in worm_behavior[:3]:
            print(f"  ⚠️ PID {proc['pid']}: {proc['name']} - CPU: {proc['cpu_usage']}%")
            
    # Quarantine high-risk threats
    if any(t.get('threat_level') in ['HIGH', 'CRITICAL'] for t in all_threats):
        print("\n🔒 QUARANTINING HIGH-RISK THREATS...")
        quarantined = detector.quarantine_threats(all_threats)
        print(f"🔒 {len(quarantined)} files quarantined for analysis")
        
    print("\n" + "="*70)
    print("🛡️ GUARDIANSHIELD RECOMMENDATION:")
    
    if risk_level in ["🔴 CRITICAL", "🟠 HIGH"]:
        print("🚨 IMMEDIATE ACTION REQUIRED:")
        print("  1. DISCONNECT FROM NETWORK IMMEDIATELY")
        print("  2. BACKUP CRITICAL DATA TO ISOLATED STORAGE")
        print("  3. REVIEW QUARANTINED FILES")
        print("  4. CONSIDER FULL SYSTEM RESTORE FROM CLEAN BACKUP")
        print("  5. UPDATE ALL SECURITY SOFTWARE")
    else:
        print("✅ SYSTEM APPEARS SECURE")
        print("  📊 Continue monitoring with enhanced vigilance")
        print("  🔍 Regular scans recommended")
        print("  📋 Review forensics report for details")
        
    return detector.forensics_data

if __name__ == "__main__":
    execute_emergency_worm_scan()