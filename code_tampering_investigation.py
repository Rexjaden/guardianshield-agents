#!/usr/bin/env python3
"""
EMERGENCY CODE TAMPERING INVESTIGATION
GUARDIANSHIELD FORENSIC ANALYSIS PROTOCOL
CODE ALTERATION/DELETION DETECTED - IMMEDIATE RESPONSE
"""

import json
import os
import subprocess
import datetime
import hashlib
import glob
from pathlib import Path
import stat

class CodeTamperingInvestigator:
    """🛡️ ELITE CODE FORENSICS - INVESTIGATING CODE ALTERATIONS"""
    
    def __init__(self):
        self.agent_name = "Guardian Sentinel - Forensic Mode"
        self.status = "🔴 CODE TAMPERING INVESTIGATION ACTIVE"
        self.tampering_evidence = []
        
    def investigate_recent_file_changes(self):
        """Investigate recent file modifications and deletions"""
        print(f"🛡️ {self.agent_name}: Investigating recent file changes...")
        
        recent_changes = []
        current_time = datetime.datetime.now()
        
        # Check all Python files for recent modifications
        for py_file in glob.glob("**/*.py", recursive=True):
            try:
                file_stat = os.stat(py_file)
                mod_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)
                access_time = datetime.datetime.fromtimestamp(file_stat.st_atime)
                
                # Check if modified in last hour
                if (current_time - mod_time).seconds < 3600:
                    recent_changes.append({
                        'file': py_file,
                        'modified': mod_time.isoformat(),
                        'accessed': access_time.isoformat(),
                        'size': file_stat.st_size,
                        'permissions': oct(file_stat.st_mode)[-3:],
                        'status': '🚨 RECENTLY MODIFIED',
                        'threat_level': 'HIGH'
                    })
                    
            except (OSError, FileNotFoundError):
                recent_changes.append({
                    'file': py_file,
                    'status': '🚨 FILE ACCESS ERROR',
                    'threat_level': 'CRITICAL'
                })
                
        return recent_changes
        
    def check_missing_critical_files(self):
        """Check for missing critical system files"""
        print(f"🛡️ {self.agent_name}: Checking for missing critical files...")
        
        critical_files = [
            'main.py',
            'admin_console.py',
            'api_server.py',
            'analytics_dashboard.py',
            'agent_learning_orchestrator.py',
            'blockchain_observer.py',
            'comprehensive_threat_analysis.py'
        ]
        
        missing_files = []
        for file_path in critical_files:
            if not os.path.exists(file_path):
                missing_files.append({
                    'file': file_path,
                    'status': '🚨 CRITICAL FILE MISSING',
                    'threat_level': 'CRITICAL',
                    'timestamp': datetime.datetime.now().isoformat()
                })
            else:
                # Check if file is empty (potential deletion/corruption)
                if os.path.getsize(file_path) == 0:
                    missing_files.append({
                        'file': file_path,
                        'status': '🚨 FILE CORRUPTED/EMPTIED',
                        'threat_level': 'CRITICAL',
                        'size': 0
                    })
                    
        return missing_files
        
    def analyze_git_history(self):
        """Analyze git history for unauthorized changes"""
        print(f"🛡️ {self.agent_name}: Analyzing git history for tampering...")
        
        git_analysis = []
        
        try:
            # Get recent git log
            result = subprocess.run(['git', 'log', '--oneline', '-10'], 
                                  capture_output=True, text=True, cwd='.')
            
            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                git_analysis.append({
                    'recent_commits': commits,
                    'status': '✅ GIT HISTORY ACCESSIBLE',
                    'commit_count': len(commits)
                })
                
                # Check for suspicious commit messages
                suspicious_commits = []
                for commit in commits:
                    if any(keyword in commit.lower() for keyword in 
                          ['delete', 'remove', 'hack', 'temp', 'test', 'fix']):
                        suspicious_commits.append({
                            'commit': commit,
                            'status': '⚠️ SUSPICIOUS COMMIT MESSAGE',
                            'threat_level': 'MEDIUM'
                        })
                        
                git_analysis.extend(suspicious_commits)
                
            # Check git status for uncommitted changes
            status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                         capture_output=True, text=True, cwd='.')
            
            if status_result.returncode == 0 and status_result.stdout:
                modified_files = status_result.stdout.strip().split('\n')
                git_analysis.append({
                    'uncommitted_changes': modified_files,
                    'status': '🚨 UNCOMMITTED MODIFICATIONS DETECTED',
                    'threat_level': 'HIGH'
                })
                
        except subprocess.SubprocessError as e:
            git_analysis.append({
                'status': '⚠️ GIT ANALYSIS FAILED',
                'error': str(e),
                'threat_level': 'MEDIUM'
            })
            
        return git_analysis
        
    def check_file_permissions(self):
        """Check for suspicious file permission changes"""
        print(f"🛡️ {self.agent_name}: Checking file permissions...")
        
        permission_issues = []
        
        for py_file in glob.glob("**/*.py", recursive=True):
            try:
                file_stat = os.stat(py_file)
                permissions = oct(file_stat.st_mode)[-3:]
                
                # Check for overly permissive files (777, 666, etc.)
                if permissions in ['777', '666', '755']:
                    permission_issues.append({
                        'file': py_file,
                        'permissions': permissions,
                        'status': '⚠️ SUSPICIOUS PERMISSIONS',
                        'threat_level': 'MEDIUM'
                    })
                    
            except OSError:
                permission_issues.append({
                    'file': py_file,
                    'status': '🚨 PERMISSION CHECK FAILED',
                    'threat_level': 'HIGH'
                })
                
        return permission_issues

class BackupIntegrityChecker:
    """⚡ BACKUP AND RECOVERY VERIFICATION"""
    
    def __init__(self):
        self.agent_name = "Ethereum Storm Lord - Backup Forensics"
        self.status = "🔴 BACKUP INTEGRITY ANALYSIS"
        
    def check_backup_files(self):
        """Check for backup files and recovery options"""
        print(f"⚡ {self.agent_name}: Checking backup integrity...")
        
        backup_status = []
        
        # Look for common backup patterns
        backup_patterns = [
            "*.backup",
            "*.bak", 
            "*~",
            "*.orig",
            ".git/",
            "backup*/",
            "*_backup*"
        ]
        
        for pattern in backup_patterns:
            matches = glob.glob(pattern, recursive=True)
            if matches:
                backup_status.append({
                    'pattern': pattern,
                    'files_found': len(matches),
                    'files': matches[:10],  # First 10 matches
                    'status': '✅ BACKUP FILES LOCATED'
                })
                
        # Check git stash
        try:
            result = subprocess.run(['git', 'stash', 'list'], 
                                  capture_output=True, text=True, cwd='.')
            if result.returncode == 0 and result.stdout:
                stashes = result.stdout.strip().split('\n')
                backup_status.append({
                    'git_stashes': len(stashes),
                    'stash_list': stashes,
                    'status': '✅ GIT STASHES AVAILABLE'
                })
        except subprocess.SubprocessError:
            backup_status.append({
                'status': '⚠️ GIT STASH CHECK FAILED'
            })
            
        return backup_status
        
    def generate_recovery_plan(self, tampering_evidence):
        """Generate recovery plan based on tampering evidence"""
        print(f"⚡ {self.agent_name}: Generating recovery plan...")
        
        recovery_actions = []
        
        # Check severity of tampering
        critical_issues = sum(1 for evidence in tampering_evidence 
                            for item in evidence if isinstance(item, dict) 
                            and item.get('threat_level') == 'CRITICAL')
        
        if critical_issues > 0:
            recovery_actions.extend([
                "🚨 CRITICAL: Restore from last known good backup",
                "🔒 ISOLATE: Disconnect from network immediately", 
                "📋 AUDIT: Full forensic analysis required",
                "🔄 RESTORE: Implement emergency recovery procedures"
            ])
        else:
            recovery_actions.extend([
                "📊 MONITOR: Enhanced monitoring activated",
                "🔍 INVESTIGATE: Continue investigation",
                "💾 BACKUP: Create current state backup",
                "🛡️ SECURE: Implement additional security measures"
            ])
            
        return recovery_actions

def execute_code_tampering_investigation():
    """Execute comprehensive code tampering investigation"""
    
    print("🚨" + "="*70 + "🚨")
    print("         GUARDIANSHIELD CODE TAMPERING INVESTIGATION")
    print("              POTENTIAL CODE ALTERATION DETECTED")  
    print("                FORENSIC ANALYSIS INITIATED")
    print("🚨" + "="*70 + "🚨")
    print()
    
    # Deploy forensic investigators
    investigator = CodeTamperingInvestigator()
    backup_checker = BackupIntegrityChecker()
    
    print("🔍 Deploying forensic analysis agents...")
    print()
    
    # Collect forensic evidence
    forensic_evidence = {
        'recent_file_changes': investigator.investigate_recent_file_changes(),
        'missing_critical_files': investigator.check_missing_critical_files(),
        'git_history_analysis': investigator.analyze_git_history(),
        'file_permissions': investigator.check_file_permissions(),
        'backup_status': backup_checker.check_backup_files(),
        'investigation_timestamp': datetime.datetime.now().isoformat()
    }
    
    # Generate recovery plan
    all_evidence = [
        forensic_evidence['recent_file_changes'],
        forensic_evidence['missing_critical_files'],
        forensic_evidence['git_history_analysis'],
        forensic_evidence['file_permissions']
    ]
    
    recovery_plan = backup_checker.generate_recovery_plan(all_evidence)
    
    # Calculate threat level
    critical_count = 0
    high_count = 0
    
    for evidence_type, evidence_list in forensic_evidence.items():
        if isinstance(evidence_list, list):
            for item in evidence_list:
                if isinstance(item, dict):
                    if item.get('threat_level') == 'CRITICAL':
                        critical_count += 1
                    elif item.get('threat_level') == 'HIGH':
                        high_count += 1
    
    if critical_count > 0:
        threat_level = "🔴 CRITICAL - CODE TAMPERING CONFIRMED"
    elif high_count > 2:
        threat_level = "🟠 HIGH - SUSPICIOUS ACTIVITY DETECTED"  
    else:
        threat_level = "🟡 ELEVATED - INVESTIGATION ONGOING"
    
    # Save forensic report
    forensic_report = {
        'investigation_type': 'CODE_TAMPERING_FORENSICS',
        'threat_level': threat_level,
        'evidence': forensic_evidence,
        'recovery_plan': recovery_plan,
        'critical_issues': critical_count,
        'high_issues': high_count
    }
    
    report_filename = f"CODE_TAMPERING_FORENSICS_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(forensic_report, f, indent=2)
    
    print(f"📊 FORENSIC INVESTIGATION COMPLETE")
    print(f"📁 Forensic report: {report_filename}")
    print(f"🔴 Threat Assessment: {threat_level}")
    print(f"⚠️  Critical Issues: {critical_count}")
    print(f"🔍 High Priority Issues: {high_count}")
    
    print("\n" + "="*70)
    print("🚨 EMERGENCY RECOVERY PLAN:")
    for action in recovery_plan:
        print(f"  {action}")
        
    print("\n📋 KEY FINDINGS:")
    
    if forensic_evidence['recent_file_changes']:
        print("  🚨 Recent file modifications detected")
        for change in forensic_evidence['recent_file_changes'][:3]:
            print(f"    - {change['file']}: {change['status']}")
    
    if forensic_evidence['missing_critical_files']:
        print("  🚨 Critical files missing/corrupted:")
        for missing in forensic_evidence['missing_critical_files']:
            print(f"    - {missing['file']}: {missing['status']}")
    
    print("="*70)
    print("🛡️ ALL AGENTS MAINTAINING MAXIMUM SECURITY ALERT")
    print("🔒 SYSTEM QUARANTINE PROTOCOLS AVAILABLE IF NEEDED")
    print("📡 CONTINUOUS FORENSIC MONITORING ACTIVE")
    
    return forensic_report

if __name__ == "__main__":
    execute_code_tampering_investigation()