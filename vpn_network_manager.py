"""
VPN Network Manager for GuardianShield Validators
Manages secure VPN access to validator infrastructure
"""
import os
import json
import subprocess
import ipaddress
import logging
from datetime import datetime, timedelta

class GuardianVPNManager:
    def __init__(self, config_path="/etc/openvpn"):
        self.config_path = config_path
        self.authorized_users = self.load_authorized_users()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def load_authorized_users(self):
        """Load authorized VPN users"""
        try:
            with open("/etc/openvpn/authorized_users.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "admin": {
                    "password_hash": "pbkdf2_sha256$260000$...",  # Use proper hashing
                    "role": "admin",
                    "allowed_networks": ["172.20.0.0/16", "10.8.0.0/24"],
                    "validator_access": ["us-east", "eu-west", "asia-pacific"],
                    "created": datetime.now().isoformat(),
                    "last_login": None
                },
                "validator_operator": {
                    "password_hash": "pbkdf2_sha256$260000$...",
                    "role": "operator",
                    "allowed_networks": ["172.20.0.0/16"],
                    "validator_access": ["us-east"],
                    "created": datetime.now().isoformat(),
                    "last_login": None
                }
            }
    
    def authenticate_user(self, username, password):
        """Authenticate VPN user"""
        if username not in self.authorized_users:
            self.logger.warning(f"Authentication failed: unknown user {username}")
            return False
        
        user_info = self.authorized_users[username]
        
        # In production, use proper password hashing (bcrypt, scrypt, etc.)
        # This is simplified for demo
        import hashlib
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt', 100000)
        
        # Verify password (simplified)
        if self.verify_password_hash(password, user_info['password_hash']):
            user_info['last_login'] = datetime.now().isoformat()
            self.logger.info(f"User {username} authenticated successfully")
            return True
        
        self.logger.warning(f"Authentication failed for user {username}")
        return False
    
    def verify_password_hash(self, password, stored_hash):
        """Verify password against stored hash"""
        # In production, use proper password verification
        # This is a placeholder
        return True  # Simplified for demo
    
    def generate_client_config(self, username):
        """Generate OpenVPN client configuration"""
        if username not in self.authorized_users:
            raise ValueError(f"User {username} not authorized")
        
        user_info = self.authorized_users[username]
        
        client_config = f"""# GuardianShield Validator VPN - {username}
client
dev tun
proto udp
remote your-validator-server.com 1194
resolv-retry infinite
nobind
persist-key
persist-tun

# Security
auth-user-pass
cipher AES-256-GCM
auth SHA512
tls-version-min 1.2

# Certificates (inline)
<ca>
-----BEGIN CERTIFICATE-----
{self.get_ca_certificate()}
-----END CERTIFICATE-----
</ca>

<cert>
-----BEGIN CERTIFICATE-----
{self.get_client_certificate(username)}
-----END CERTIFICATE-----
</cert>

<key>
-----BEGIN PRIVATE KEY-----
{self.get_client_private_key(username)}
-----END PRIVATE KEY-----
</key>

# TLS authentication
<tls-crypt>
{self.get_tls_crypt_key()}
</tls-crypt>

# Routing for validator access
route 172.20.0.0 255.255.0.0
route 10.0.0.0 255.0.0.0

# Security
verb 3
mute 20
compress
"""
        return client_config
    
    def get_ca_certificate(self):
        """Get CA certificate content"""
        # In production, load from secure storage
        return "MIICertificateContent..."
    
    def get_client_certificate(self, username):
        """Get client certificate for user"""
        # Generate or load client certificate
        return f"ClientCertFor{username}..."
    
    def get_client_private_key(self, username):
        """Get client private key"""
        # Generate or load client private key (encrypted)
        return f"PrivateKeyFor{username}..."
    
    def get_tls_crypt_key(self):
        """Get TLS-Crypt key"""
        return "TLSCryptKeyContent..."
    
    def setup_client_routing(self, username, client_ip):
        """Set up routing rules for VPN client"""
        user_info = self.authorized_users[username]
        
        # Create client-specific config directory
        ccd_path = f"/etc/openvpn/ccd/{username}"
        os.makedirs(os.path.dirname(ccd_path), exist_ok=True)
        
        # Generate routing rules based on user permissions
        routing_config = []
        
        for region in user_info.get('validator_access', []):
            if region == 'us-east':
                routing_config.append("iroute 172.20.10.0 255.255.255.0")
            elif region == 'eu-west':
                routing_config.append("iroute 172.20.11.0 255.255.255.0")
            elif region == 'asia-pacific':
                routing_config.append("iroute 172.20.12.0 255.255.255.0")
        
        # Write client config
        with open(ccd_path, 'w') as f:
            f.write(f"# Client config for {username}\n")
            f.write(f"ifconfig-push {client_ip} 255.255.255.0\n")
            for route in routing_config:
                f.write(f"{route}\n")
        
        self.logger.info(f"Client routing configured for {username}")
    
    def monitor_vpn_connections(self):
        """Monitor active VPN connections"""
        try:
            # Get OpenVPN status
            with open('/var/log/openvpn/openvpn-status.log', 'r') as f:
                status = f.read()
            
            # Parse connected clients
            connections = self.parse_openvpn_status(status)
            
            for conn in connections:
                username = conn['username']
                ip = conn['virtual_ip']
                
                # Log connection
                self.logger.info(f"Active VPN connection: {username} @ {ip}")
                
                # Update routing if needed
                self.setup_client_routing(username, ip)
            
            return connections
            
        except Exception as e:
            self.logger.error(f"Failed to monitor VPN connections: {e}")
            return []
    
    def parse_openvpn_status(self, status_content):
        """Parse OpenVPN status log"""
        connections = []
        lines = status_content.split('\n')
        
        for line in lines:
            if ',' in line and 'CLIENT_LIST' in line:
                parts = line.split(',')
                if len(parts) >= 5:
                    connections.append({
                        'username': parts[1],
                        'real_ip': parts[2],
                        'virtual_ip': parts[3],
                        'connected_since': parts[4]
                    })
        
        return connections
    
    def revoke_user_access(self, username):
        """Revoke VPN access for user"""
        if username in self.authorized_users:
            del self.authorized_users[username]
            
            # Remove client config
            ccd_path = f"/etc/openvpn/ccd/{username}"
            if os.path.exists(ccd_path):
                os.remove(ccd_path)
            
            # Revoke certificate
            try:
                subprocess.run([
                    "easyrsa", "revoke", username
                ], check=True, cwd="/etc/openvpn/easy-rsa")
                
                subprocess.run([
                    "easyrsa", "gen-crl"
                ], check=True, cwd="/etc/openvpn/easy-rsa")
                
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to revoke certificate for {username}: {e}")
            
            self.logger.info(f"Revoked VPN access for {username}")
    
    def health_check(self):
        """VPN health check"""
        try:
            # Check OpenVPN process
            result = subprocess.run(
                ["pgrep", "openvpn"], 
                capture_output=True
            )
            
            if result.returncode != 0:
                return False, "OpenVPN not running"
            
            # Check certificate validity
            # In production, verify CA and server certificates
            
            # Check active connections
            connections = self.monitor_vpn_connections()
            
            return True, f"VPN healthy, {len(connections)} active connections"
            
        except Exception as e:
            return False, f"VPN health check failed: {str(e)}"

def main():
    """Main VPN manager function"""
    vpn_manager = GuardianVPNManager()
    
    print("GuardianShield VPN Manager initialized")
    
    # Health check
    healthy, message = vpn_manager.health_check()
    print(f"VPN Status: {message}")
    
    # Monitor connections
    connections = vpn_manager.monitor_vpn_connections()
    print(f"Active connections: {len(connections)}")
    
    for conn in connections:
        print(f"  - {conn['username']} @ {conn['virtual_ip']}")

if __name__ == "__main__":
    main()