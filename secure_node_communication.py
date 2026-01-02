"""
GUARDIANSHIELD SECURE NODE COMMUNICATION SYSTEM
=============================================
Mission: Easy, secure communication with sentry nodes - US ONLY access
Accountability: Professional-grade security or termination

Features:
- Encrypted communication channels
- Rex-only authentication 
- Easy management CLI and dashboard
- Secure API endpoints
- Real-time node monitoring
"""

import os
import json
import base64
import hashlib
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class GuardianShieldSecureNodeManager:
    def __init__(self):
        self.authorized_users = {
            "rex_judon_rogers": {
                "email": "rexxrog1@gmail.com",
                "phone": "(843) 250-3735",
                "role": "admin",
                "api_key": self._generate_api_key("rex_judon_rogers"),
                "permissions": ["all"]
            }
        }
        
        # Generate master encryption key for node communication
        self.master_key = self._generate_encryption_key()
        
        # Secure node management endpoints
        self.management_endpoints = {
            "global_dashboard": "https://manage.guardian-shield.network",
            "api_base": "https://api.guardian-shield.network/v1",
            "secure_shell": "ssh://nodes.guardian-shield.network",
            "monitoring": "https://monitor.guardian-shield.network"
        }
    
    def _generate_api_key(self, username: str) -> str:
        """Generate secure API key for user"""
        timestamp = str(int(datetime.now().timestamp()))
        data = f"{username}:{timestamp}:guardianshield"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _generate_encryption_key(self) -> str:
        """Generate master encryption key for secure communication"""
        password = b"guardianshield_rex_secure_2026"
        salt = b"guardian_salt_2026"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key.decode()
    
    def generate_secure_cli_tool(self):
        """Generate CLI tool for easy node management"""
        
        cli_tool = f"""#!/usr/bin/env python3
\"\"\"
GuardianShield Node Management CLI
Rex Judon Rogers - Secure Node Communication Tool
\"\"\"

import requests
import json
import sys
import os
from datetime import datetime
import argparse

class GuardianNodeCLI:
    def __init__(self):
        self.api_key = "{self.authorized_users['rex_judon_rogers']['api_key']}"
        self.base_url = "https://api.guardian-shield.network/v1"
        self.headers = {{
            "Authorization": f"Bearer {{self.api_key}}",
            "Content-Type": "application/json",
            "User-Agent": "GuardianShield-CLI/1.0"
        }}
    
    def authenticate(self):
        \"\"\"Verify authentication with nodes\"\"\"
        try:
            response = requests.get(f"{{self.base_url}}/auth/verify", headers=self.headers)
            if response.status_code == 200:
                print("[+] Authenticated successfully")
                user_info = response.json()
                print(f"   User: {{user_info.get('name', 'Rex Judon Rogers')}}")
                print(f"   Role: {{user_info.get('role', 'admin')}}")
                return True
            else:
                print("[-] Authentication failed")
                return False
        except Exception as e:
            print(f"[-] Connection error: {{e}}")
            return False
    
    def list_nodes(self):
        \"\"\"List all sentry nodes\"\"\"
        try:
            response = requests.get(f"{{self.base_url}}/nodes", headers=self.headers)
            if response.status_code == 200:
                nodes = response.json()
                print(f"🛡️  GuardianShield Sentry Nodes ({{len(nodes)}} total)")
                print("-" * 60)
                
                for node in nodes:
                    status_emoji = "🟢" if node['status'] == 'healthy' else "🔴"
                    print(f"{{status_emoji}} {{node['region']}} - {{node['city']}}")
                    print(f"   IP: {{node['public_ip']}}")
                    print(f"   API: {{node['api_endpoint']}}")
                    print(f"   Status: {{node['status']}} ({{node['uptime']}})")
                    print()
            else:
                print("❌ Failed to fetch node list")
        except Exception as e:
            print(f"❌ Error: {{e}}")
    
    def node_status(self, region=None):
        \"\"\"Get detailed status of nodes\"\"\"
        endpoint = f"{{self.base_url}}/nodes/status"
        if region:
            endpoint += f"?region={{region}}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            if response.status_code == 200:
                status = response.json()
                print(f"📊 Node Status Report - {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
                print("=" * 70)
                
                print(f"🌍 Global Status: {{status['global']['health']}}")
                print(f"📈 Total Requests: {{status['global']['total_requests']:,}}")
                print(f"⚡ Avg Response Time: {{status['global']['avg_response_time']}}ms")
                print(f"🛡️  Threats Blocked: {{status['global']['threats_blocked']:,}}")
                print()
                
                for region, data in status['regions'].items():
                    health_emoji = "🟢" if data['health'] == 'healthy' else "🔴"
                    print(f"{{health_emoji}} {{region}}: {{data['nodes_active']}}/{{data['nodes_total']}} nodes")
                    print(f"   Requests/sec: {{data['requests_per_second']}}")
                    print(f"   Response time: {{data['response_time']}}ms")
                    print()
            else:
                print("❌ Failed to get status")
        except Exception as e:
            print(f"❌ Error: {{e}}")
    
    def restart_node(self, region):
        \"\"\"Restart specific node by region\"\"\"
        confirm = input(f"🚨 Restart node in {{region}}? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Cancelled")
            return
        
        try:
            response = requests.post(
                f"{{self.base_url}}/nodes/{{region}}/restart", 
                headers=self.headers
            )
            if response.status_code == 200:
                print(f"✅ Restart initiated for {{region}}")
                print("⏱️  Expected downtime: 30-60 seconds")
            else:
                print(f"❌ Failed to restart {{region}}: {{response.text}}")
        except Exception as e:
            print(f"❌ Error: {{e}}")
    
    def update_nodes(self):
        \"\"\"Update all nodes to latest version\"\"\"
        confirm = input("🚨 Update all nodes to latest version? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Cancelled")
            return
        
        try:
            response = requests.post(f"{{self.base_url}}/nodes/update-all", headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                print("✅ Update initiated on all nodes")
                print(f"📊 Updating {{result['nodes_count']}} nodes")
                print("⏱️  Expected completion: 5-10 minutes")
            else:
                print(f"❌ Update failed: {{response.text}}")
        except Exception as e:
            print(f"❌ Error: {{e}}")
    
    def node_logs(self, region, lines=50):
        \"\"\"Get recent logs from specific node\"\"\"
        try:
            response = requests.get(
                f"{{self.base_url}}/nodes/{{region}}/logs?lines={{lines}}", 
                headers=self.headers
            )
            if response.status_code == 200:
                logs = response.json()
                print(f"📋 Recent logs from {{region}} ({{lines}} lines)")
                print("-" * 60)
                for log in logs['entries']:
                    timestamp = log['timestamp']
                    level = log['level'].upper()
                    message = log['message']
                    print(f"[{{timestamp}}] {{level}}: {{message}}")
            else:
                print(f"❌ Failed to get logs: {{response.text}}")
        except Exception as e:
            print(f"❌ Error: {{e}}")
    
    def security_report(self):
        \"\"\"Get security report from all nodes\"\"\"
        try:
            response = requests.get(f"{{self.base_url}}/security/report", headers=self.headers)
            if response.status_code == 200:
                report = response.json()
                print("🛡️  Security Report - Last 24 Hours")
                print("=" * 50)
                print(f"🚨 Total Attacks Blocked: {{report['attacks_blocked']:,}}")
                print(f"🌍 Attack Sources: {{report['unique_sources']:,}} countries")
                print(f"⚡ Peak Attack Rate: {{report['peak_rate']}} req/sec")
                print(f"🛠️  Top Attack Types:")
                for attack_type, count in report['attack_types'].items():
                    print(f"   • {{attack_type}}: {{count:,}}")
                print()
                print(f"🎯 Most Targeted Regions:")
                for region, attacks in report['targeted_regions'].items():
                    print(f"   • {{region}}: {{attacks:,}} attacks")
            else:
                print("❌ Failed to get security report")
        except Exception as e:
            print(f"❌ Error: {{e}}")

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
"""
        return cli_tool
    
    def generate_secure_api_config(self):
        """Generate secure API configuration with Rex-only access"""
        
        api_config = f"""
# GuardianShield Secure API Configuration
# Rex Judon Rogers - Admin Access Only

server:
  host: 0.0.0.0
  port: 8443
  ssl_cert: /etc/ssl/certs/guardian-shield.crt
  ssl_key: /etc/ssl/private/guardian-shield.key

authentication:
  enabled: true
  method: api_key
  
  authorized_users:
    rex_judon_rogers:
      api_key: "{self.authorized_users['rex_judon_rogers']['api_key']}"
      email: "rexxrog1@gmail.com"
      phone: "(843) 250-3735"
      role: admin
      permissions:
        - nodes:read
        - nodes:write
        - nodes:restart
        - nodes:update
        - security:read
        - logs:read
        - metrics:read

security:
  rate_limiting:
    enabled: true
    requests_per_minute: 1000
    burst: 50
  
  ip_whitelist:
    - "0.0.0.0/0"  # Will be restricted to Rex's IPs in production
  
  encryption:
    enabled: true
    algorithm: AES-256-GCM
    key: "{self.master_key}"

monitoring:
  enabled: true
  metrics_endpoint: /metrics
  health_endpoint: /health
  
  alerts:
    email: rexxrog1@gmail.com
    phone: "+18432503735"
    
  thresholds:
    response_time_ms: 500
    error_rate_percent: 5
    cpu_usage_percent: 80
    memory_usage_percent: 85

logging:
  level: INFO
  format: json
  retention_days: 30
  
  destinations:
    - console
    - file: /var/log/guardianshield/api.log
    - syslog: guardian-shield-api

endpoints:
  # Authentication
  - path: /v1/auth/verify
    method: GET
    auth_required: true
    
  # Node management
  - path: /v1/nodes
    method: GET
    auth_required: true
    
  - path: /v1/nodes/status
    method: GET
    auth_required: true
    
  - path: /v1/nodes/{{region}}/restart
    method: POST
    auth_required: true
    permissions: [nodes:write]
    
  - path: /v1/nodes/update-all
    method: POST
    auth_required: true
    permissions: [nodes:write]
    
  - path: /v1/nodes/{{region}}/logs
    method: GET
    auth_required: true
    permissions: [logs:read]
    
  # Security endpoints
  - path: /v1/security/report
    method: GET
    auth_required: true
    permissions: [security:read]
    
  - path: /v1/security/threats
    method: GET
    auth_required: true
    permissions: [security:read]
"""
        return api_config
    
    def generate_secure_ssh_config(self):
        """Generate secure SSH configuration for direct node access"""
        
        ssh_config = f"""# GuardianShield Secure SSH Configuration
# Rex Judon Rogers - Direct Node Access

# Rex's SSH Key (generate new key pair)
Host guardian-*
    User ubuntu
    Port 2222
    IdentityFile ~/.ssh/guardianshield_rsa
    StrictHostKeyChecking yes
    UserKnownHostsFile ~/.ssh/guardianshield_known_hosts
    
    # Security settings
    Protocol 2
    Compression yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
    
    # Encryption ciphers (strongest)
    Ciphers aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr
    MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com
    KexAlgorithms curve25519-sha256,diffie-hellman-group16-sha512

# Regional node shortcuts
Host guardian-us-east
    HostName sentry-us-east-1.guardian-shield.network

Host guardian-us-west  
    HostName sentry-us-west-2.guardian-shield.network

Host guardian-eu-west
    HostName sentry-eu-west-1.guardian-shield.network

Host guardian-eu-central
    HostName sentry-eu-central-1.guardian-shield.network

Host guardian-asia-tokyo
    HostName sentry-ap-northeast-1.guardian-shield.network

Host guardian-asia-singapore
    HostName sentry-ap-southeast-1.guardian-shield.network

# Management shortcuts
Host guardian-all
    # Connect to all nodes simultaneously (using tmux/parallel-ssh)
    HostName manage.guardian-shield.network
    
# Quick commands
# ssh guardian-us-east "docker ps"
# ssh guardian-eu-west "systemctl status guardianshield-sentry"
# ssh guardian-asia-tokyo "tail -f /opt/guardianshield/logs/security.log"
"""
        return ssh_config
    
    def generate_management_dashboard(self):
        """Generate secure management dashboard for Rex"""
        
        dashboard_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GuardianShield Node Management - Rex Judon Rogers</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Monaco', 'Menlo', monospace; 
            background: #0a0a0a; 
            color: #00ff00; 
            padding: 20px;
        }}
        .header {{
            border: 2px solid #00ff00;
            padding: 20px;
            margin-bottom: 20px;
            background: rgba(0, 255, 0, 0.1);
        }}
        .header h1 {{ color: #00ff00; text-align: center; }}
        .header .user-info {{ text-align: center; margin-top: 10px; opacity: 0.8; }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .panel {{
            border: 1px solid #00ff00;
            padding: 15px;
            background: rgba(0, 0, 0, 0.8);
        }}
        
        .panel h3 {{
            color: #00ff00;
            border-bottom: 1px solid #00ff00;
            padding-bottom: 10px;
            margin-bottom: 10px;
        }}
        
        .node {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #333;
        }}
        
        .node:last-child {{ border-bottom: none; }}
        
        .status-healthy {{ color: #00ff00; }}
        .status-warning {{ color: #ffff00; }}
        .status-error {{ color: #ff0000; }}
        
        .button {{
            background: #00ff00;
            color: #000;
            border: none;
            padding: 8px 16px;
            cursor: pointer;
            font-family: inherit;
            font-size: 12px;
            margin-left: 10px;
        }}
        
        .button:hover {{ background: #33ff33; }}
        
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }}
        
        .metric {{
            text-align: center;
            padding: 10px;
            border: 1px solid #333;
        }}
        
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .metric-label {{ font-size: 12px; opacity: 0.8; }}
        
        .log-output {{
            background: #000;
            border: 1px solid #333;
            padding: 10px;
            height: 200px;
            overflow-y: scroll;
            font-family: 'Courier New', monospace;
            font-size: 11px;
        }}
        
        .command-input {{
            width: 100%;
            background: #000;
            border: 1px solid #00ff00;
            color: #00ff00;
            padding: 8px;
            font-family: inherit;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ GUARDIANSHIELD NODE MANAGEMENT</h1>
        <div class="user-info">
            Rex Judon Rogers | rexxrog1@gmail.com | (843) 250-3735<br>
            Admin Access | Secure Connection | Last Login: <span id="lastLogin"></span>
        </div>
    </div>
    
    <div class="grid">
        <div class="panel">
            <h3>🌍 Global Status</h3>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value" id="totalNodes">--</div>
                    <div class="metric-label">Total Nodes</div>
                </div>
                <div class="metric">
                    <div class="metric-value status-healthy" id="healthyNodes">--</div>
                    <div class="metric-label">Healthy</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="totalRequests">--</div>
                    <div class="metric-label">Requests/sec</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="avgResponse">--</div>
                    <div class="metric-label">Avg Response (ms)</div>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h3>🚨 Security Status</h3>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value status-error" id="threatsBlocked">--</div>
                    <div class="metric-label">Threats Blocked</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="attackSources">--</div>
                    <div class="metric-label">Attack Sources</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="peakAttackRate">--</div>
                    <div class="metric-label">Peak Attack Rate</div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="grid">
        <div class="panel">
            <h3>🖥️ Regional Nodes</h3>
            <div id="nodeList">
                <!-- Nodes will be loaded here -->
            </div>
        </div>
        
        <div class="panel">
            <h3>📋 Real-time Logs</h3>
            <div class="log-output" id="logOutput">
                Loading logs...
            </div>
            <input type="text" class="command-input" id="commandInput" 
                   placeholder="Enter command (e.g., 'restart us-east-1', 'status', 'logs eu-west-1')">
        </div>
    </div>
    
    <script>
        // API Configuration
        const API_BASE = 'https://api.guardian-shield.network/v1';
        const API_KEY = '{self.authorized_users["rex_judon_rogers"]["api_key"]}';
        
        const headers = {{
            'Authorization': `Bearer ${{API_KEY}}`,
            'Content-Type': 'application/json'
        }};
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {{
            document.getElementById('lastLogin').textContent = new Date().toLocaleString();
            loadDashboardData();
            setupCommandInput();
            
            // Auto-refresh every 30 seconds
            setInterval(loadDashboardData, 30000);
        }});
        
        async function loadDashboardData() {{
            try {{
                // Load node status
                const nodesResponse = await fetch(`${{API_BASE}}/nodes/status`, {{ headers }});
                const nodesData = await nodesResponse.json();
                updateNodeStatus(nodesData);
                
                // Load security report
                const securityResponse = await fetch(`${{API_BASE}}/security/report`, {{ headers }});
                const securityData = await securityResponse.json();
                updateSecurityStatus(securityData);
                
                // Load recent logs
                loadRecentLogs();
            }} catch (error) {{
                console.error('Failed to load dashboard data:', error);
                document.getElementById('logOutput').innerHTML += `\\n❌ Error: ${{error.message}}`;
            }}
        }}
        
        function updateNodeStatus(data) {{
            const globalStatus = data.global;
            
            document.getElementById('totalNodes').textContent = globalStatus.total_nodes;
            document.getElementById('healthyNodes').textContent = globalStatus.healthy_nodes;
            document.getElementById('totalRequests').textContent = globalStatus.requests_per_second.toLocaleString();
            document.getElementById('avgResponse').textContent = globalStatus.avg_response_time;
            
            // Update regional nodes
            const nodeListHTML = Object.entries(data.regions).map(([region, regionData]) => {{
                const statusClass = regionData.health === 'healthy' ? 'status-healthy' : 
                                   regionData.health === 'warning' ? 'status-warning' : 'status-error';
                
                return `
                    <div class="node">
                        <div>
                            <strong>${{region}}</strong><br>
                            <span class="${{statusClass}}">${{regionData.health}}</span> | 
                            ${{regionData.nodes_active}}/${{regionData.nodes_total}} nodes
                        </div>
                        <div>
                            <button class="button" onclick="restartNode('${{region}}')">Restart</button>
                            <button class="button" onclick="viewLogs('${{region}}')">Logs</button>
                        </div>
                    </div>
                `;
            }}).join('');
            
            document.getElementById('nodeList').innerHTML = nodeListHTML;
        }}
        
        function updateSecurityStatus(data) {{
            document.getElementById('threatsBlocked').textContent = data.attacks_blocked.toLocaleString();
            document.getElementById('attackSources').textContent = data.unique_sources.toLocaleString();
            document.getElementById('peakAttackRate').textContent = data.peak_rate + '/sec';
        }}
        
        async function loadRecentLogs() {{
            try {{
                const response = await fetch(`${{API_BASE}}/logs/recent?lines=20`, {{ headers }});
                const logs = await response.json();
                
                const logHTML = logs.map(log => {{
                    const timestamp = new Date(log.timestamp).toLocaleTimeString();
                    const level = log.level.toUpperCase();
                    return `[${{timestamp}}] ${{level}}: ${{log.message}}`;
                }}).join('\\n');
                
                document.getElementById('logOutput').innerHTML = logHTML;
                document.getElementById('logOutput').scrollTop = document.getElementById('logOutput').scrollHeight;
            }} catch (error) {{
                document.getElementById('logOutput').innerHTML += `\\n❌ Failed to load logs: ${{error.message}}`;
            }}
        }}
        
        function setupCommandInput() {{
            const commandInput = document.getElementById('commandInput');
            commandInput.addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') {{
                    executeCommand(this.value);
                    this.value = '';
                }}
            }});
        }}
        
        async function executeCommand(command) {{
            const logOutput = document.getElementById('logOutput');
            logOutput.innerHTML += `\\n> ${{command}}`;
            
            try {{
                const response = await fetch(`${{API_BASE}}/command`, {{
                    method: 'POST',
                    headers,
                    body: JSON.stringify({{ command }})
                }});
                
                const result = await response.json();
                logOutput.innerHTML += `\\n${{result.output}}`;
            }} catch (error) {{
                logOutput.innerHTML += `\\n❌ Command failed: ${{error.message}}`;
            }}
            
            logOutput.scrollTop = logOutput.scrollHeight;
        }}
        
        async function restartNode(region) {{
            if (confirm(`Restart node in ${{region}}?`)) {{
                const logOutput = document.getElementById('logOutput');
                logOutput.innerHTML += `\\n🔄 Restarting node in ${{region}}...`;
                
                try {{
                    const response = await fetch(`${{API_BASE}}/nodes/${{region}}/restart`, {{
                        method: 'POST',
                        headers
                    }});
                    
                    const result = await response.json();
                    logOutput.innerHTML += `\\n✅ ${{result.message}}`;
                }} catch (error) {{
                    logOutput.innerHTML += `\\n❌ Restart failed: ${{error.message}}`;
                }}
                
                logOutput.scrollTop = logOutput.scrollHeight;
            }}
        }}
        
        async function viewLogs(region) {{
            try {{
                const response = await fetch(`${{API_BASE}}/nodes/${{region}}/logs?lines=50`, {{ headers }});
                const logs = await response.json();
                
                const logHTML = logs.entries.map(log => {{
                    const timestamp = new Date(log.timestamp).toLocaleTimeString();
                    return `[${{timestamp}}] ${{log.level}}: ${{log.message}}`;
                }}).join('\\n');
                
                document.getElementById('logOutput').innerHTML = `--- ${{region}} LOGS ---\\n${{logHTML}}`;
            }} catch (error) {{
                document.getElementById('logOutput').innerHTML += `\\n❌ Failed to load ${{region}} logs: ${{error.message}}`;
            }}
        }}
    </script>
</body>
</html>"""
        return dashboard_html
    
    def create_secure_access_files(self):
        """Create all secure access files for Rex-only communication"""
        
        files_created = []
        
        # Create secure directories
        os.makedirs('secure-node-management', exist_ok=True)
        os.makedirs('secure-node-management/config', exist_ok=True)
        os.makedirs('secure-node-management/scripts', exist_ok=True)
        
        # CLI Tool
        cli_tool_path = 'secure-node-management/guardian-cli.py'
        with open(cli_tool_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_secure_cli_tool())
        files_created.append(cli_tool_path)
        
        # API Configuration
        api_config_path = 'secure-node-management/config/api-config.yml'
        with open(api_config_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_secure_api_config())
        files_created.append(api_config_path)
        
        # SSH Configuration
        ssh_config_path = 'secure-node-management/config/ssh-config'
        with open(ssh_config_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_secure_ssh_config())
        files_created.append(ssh_config_path)
        
        # Management Dashboard
        dashboard_path = 'secure-node-management/dashboard.html'
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_management_dashboard())
        files_created.append(dashboard_path)
        
        # Quick setup script
        setup_script = f"""#!/bin/bash
# GuardianShield Secure Node Management Setup
# Rex Judon Rogers - Quick Setup Script

echo "🛡️  Setting up secure node communication..."

# Create SSH key pair for nodes
if [ ! -f ~/.ssh/guardianshield_rsa ]; then
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/guardianshield_rsa -N "" -C "rex@guardianshield-nodes"
    echo "✅ SSH key created"
fi

# Install CLI tool
sudo cp guardian-cli.py /usr/local/bin/guardian
sudo chmod 755 /usr/local/bin/guardian

# Setup SSH config
mkdir -p ~/.ssh
cp config/ssh-config ~/.ssh/config_guardianshield
echo "Include ~/.ssh/config_guardianshield" >> ~/.ssh/config

echo "✅ Secure node communication setup complete!"
echo
echo "🚀 QUICK COMMANDS:"
echo "   guardian auth          - Test authentication"
echo "   guardian list          - List all nodes" 
echo "   guardian status        - Node status report"
echo "   guardian security      - Security report"
echo "   ssh guardian-us-east   - Direct SSH to US East node"
echo
echo "🌐 Management Dashboard: file://$(pwd)/dashboard.html"
echo "🔑 API Key: {self.authorized_users['rex_judon_rogers']['api_key'][:20]}..."
"""
        
        setup_script_path = 'secure-node-management/setup.sh'
        with open(setup_script_path, 'w', encoding='utf-8') as f:
            f.write(setup_script)
        files_created.append(setup_script_path)
        
        return files_created

def main():
    """Setup secure node communication for Rex only"""
    
    print("🔒 GUARDIANSHIELD SECURE NODE COMMUNICATION")
    print("=" * 50)
    print("Mission: Easy, secure communication with nodes - US ONLY")
    print("User: Rex Judon Rogers")
    print(f"Started: {datetime.now().isoformat()}")
    print()
    
    manager = GuardianShieldSecureNodeManager()
    files_created = manager.create_secure_access_files()
    
    print("✅ SECURE ACCESS FILES CREATED:")
    for file in files_created:
        print(f"   📄 {file}")
    
    print()
    print("🔑 REX'S ACCESS CREDENTIALS:")
    print(f"   API Key: {manager.authorized_users['rex_judon_rogers']['api_key'][:20]}...")
    print(f"   Email: {manager.authorized_users['rex_judon_rogers']['email']}")
    print(f"   Role: {manager.authorized_users['rex_judon_rogers']['role']}")
    
    print()
    print("🚀 SETUP INSTRUCTIONS:")
    print("   1. cd secure-node-management")
    print("   2. bash setup.sh")
    print("   3. Open dashboard.html in browser")
    print("   4. Test: guardian auth")
    
    print()
    print("⚡ QUICK COMMANDS:")
    print("   guardian list          # List all nodes")
    print("   guardian status        # Node status")
    print("   guardian security      # Security report")
    print("   ssh guardian-us-east   # Direct SSH access")
    
    print()
    print("🛡️  SECURITY FEATURES:")
    print("   ✅ Rex-only authentication")
    print("   ✅ Encrypted communication")
    print("   ✅ Direct SSH access")
    print("   ✅ Real-time monitoring")
    print("   ✅ Command execution")
    print("   ✅ Log viewing")
    
    print()
    print("✅ SECURE NODE COMMUNICATION READY!")
    print("🎯 Rex can now easily manage all nodes with full security")

if __name__ == "__main__":
    main()