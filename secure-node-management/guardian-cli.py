#!/usr/bin/env python3
"""
GuardianShield Node Management CLI
Rex Judon Rogers - Secure Node Communication Tool
"""

import requests
import json
import sys
import os
from datetime import datetime
import argparse

class GuardianNodeCLI:
    def __init__(self):
        self.api_key = "e988169a6a8b0c14504ad7f15833242b874fd8349773f27eddc9b19926dae087"
        self.base_url = "https://api.guardian-shield.network/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "GuardianShield-CLI/1.0"
        }
    
    def authenticate(self):
        """Verify authentication with nodes"""
        try:
            response = requests.get(f"{self.base_url}/auth/verify", headers=self.headers)
            if response.status_code == 200:
                print("[+] Authenticated successfully")
                user_info = response.json()
                print(f"   User: {user_info.get('name', 'Rex Judon Rogers')}")
                print(f"   Role: {user_info.get('role', 'admin')}")
                return True
            else:
                print("[-] Authentication failed")
                return False
        except Exception as e:
            print(f"[-] Connection error: {e}")
            return False
    
    def list_nodes(self):
        """List all sentry nodes"""
        try:
            response = requests.get(f"{self.base_url}/nodes", headers=self.headers)
            if response.status_code == 200:
                nodes = response.json()
                print(f"🛡️  GuardianShield Sentry Nodes ({len(nodes)} total)")
                print("-" * 60)
                
                for node in nodes:
                    status_emoji = "🟢" if node['status'] == 'healthy' else "🔴"
                    print(f"{status_emoji} {node['region']} - {node['city']}")
                    print(f"   IP: {node['public_ip']}")
                    print(f"   API: {node['api_endpoint']}")
                    print(f"   Status: {node['status']} ({node['uptime']})")
                    print()
            else:
                print("❌ Failed to fetch node list")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def node_status(self, region=None):
        """Get detailed status of nodes"""
        endpoint = f"{self.base_url}/nodes/status"
        if region:
            endpoint += f"?region={region}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            if response.status_code == 200:
                status = response.json()
                print(f"📊 Node Status Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 70)
                
                print(f"🌍 Global Status: {status['global']['health']}")
                print(f"📈 Total Requests: {status['global']['total_requests']:,}")
                print(f"⚡ Avg Response Time: {status['global']['avg_response_time']}ms")
                print(f"🛡️  Threats Blocked: {status['global']['threats_blocked']:,}")
                print()
                
                for region, data in status['regions'].items():
                    health_emoji = "🟢" if data['health'] == 'healthy' else "🔴"
                    print(f"{health_emoji} {region}: {data['nodes_active']}/{data['nodes_total']} nodes")
                    print(f"   Requests/sec: {data['requests_per_second']}")
                    print(f"   Response time: {data['response_time']}ms")
                    print()
            else:
                print("❌ Failed to get status")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def restart_node(self, region):
        """Restart specific node by region"""
        confirm = input(f"🚨 Restart node in {region}? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Cancelled")
            return
        
        try:
            response = requests.post(
                f"{self.base_url}/nodes/{region}/restart", 
                headers=self.headers
            )
            if response.status_code == 200:
                print(f"✅ Restart initiated for {region}")
                print("⏱️  Expected downtime: 30-60 seconds")
            else:
                print(f"❌ Failed to restart {region}: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def update_nodes(self):
        """Update all nodes to latest version"""
        confirm = input("🚨 Update all nodes to latest version? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Cancelled")
            return
        
        try:
            response = requests.post(f"{self.base_url}/nodes/update-all", headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                print("✅ Update initiated on all nodes")
                print(f"📊 Updating {result['nodes_count']} nodes")
                print("⏱️  Expected completion: 5-10 minutes")
            else:
                print(f"❌ Update failed: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def node_logs(self, region, lines=50):
        """Get recent logs from specific node"""
        try:
            response = requests.get(
                f"{self.base_url}/nodes/{region}/logs?lines={lines}", 
                headers=self.headers
            )
            if response.status_code == 200:
                logs = response.json()
                print(f"📋 Recent logs from {region} ({lines} lines)")
                print("-" * 60)
                for log in logs['entries']:
                    timestamp = log['timestamp']
                    level = log['level'].upper()
                    message = log['message']
                    print(f"[{timestamp}] {level}: {message}")
            else:
                print(f"❌ Failed to get logs: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def security_report(self):
        """Get security report from all nodes"""
        try:
            response = requests.get(f"{self.base_url}/security/report", headers=self.headers)
            if response.status_code == 200:
                report = response.json()
                print("🛡️  Security Report - Last 24 Hours")
                print("=" * 50)
                print(f"🚨 Total Attacks Blocked: {report['attacks_blocked']:,}")
                print(f"🌍 Attack Sources: {report['unique_sources']:,} countries")
                print(f"⚡ Peak Attack Rate: {report['peak_rate']} req/sec")
                print(f"🛠️  Top Attack Types:")
                for attack_type, count in report['attack_types'].items():
                    print(f"   • {attack_type}: {count:,}")
                print()
                print(f"🎯 Most Targeted Regions:")
                for region, attacks in report['targeted_regions'].items():
                    print(f"   • {region}: {attacks:,} attacks")
            else:
                print("❌ Failed to get security report")
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="GuardianShield Node Management")
    parser.add_argument('command', choices=[
        'auth', 'list', 'status', 'restart', 'update', 'logs', 'security'
    ], help='Command to execute')
    parser.add_argument('--region', help='Specific region for commands')
    parser.add_argument('--lines', type=int, default=50, help='Number of log lines')
    
    args = parser.parse_args()
    
    cli = GuardianNodeCLI()
    
    # Command execution
    if args.command == 'auth':
        cli.authenticate()
    elif args.command == 'list':
        cli.list_nodes()
    elif args.command == 'status':
        cli.node_status(args.region)
    elif args.command == 'restart':
        if not args.region:
            print("❌ --region required for restart command")
            sys.exit(1)
        cli.restart_node(args.region)
    elif args.command == 'update':
        cli.update_nodes()
    elif args.command == 'logs':
        if not args.region:
            print("❌ --region required for logs command")
            sys.exit(1)
        cli.node_logs(args.region, args.lines)
    elif args.command == 'security':
        cli.security_report()

if __name__ == "__main__":
    main()
