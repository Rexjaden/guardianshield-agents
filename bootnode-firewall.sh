#!/bin/bash
# GuardianShield Bootnode Ultra-Tight Firewall Configuration
# P2P ONLY - NO RPC/API ACCESS

echo "=== GuardianShield Bootnode Firewall Setup ==="
echo "Mode: P2P Discovery Only"
echo "Ports: 26656 (P2P) ONLY"
echo "Status: MAXIMUM SECURITY"

# Flush existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

# Set default policies - DROP EVERYTHING
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# Allow loopback (required for basic system function)
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established and related connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow outgoing DNS (for bootstrap peer resolution)
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

# Allow outgoing NTP (time synchronization)
iptables -A OUTPUT -p udp --dport 123 -j ACCEPT

# Allow outgoing connections to other bootnodes/peers
iptables -A OUTPUT -p tcp --dport 26656 -j ACCEPT

# === CRITICAL: P2P PORT ONLY ===
# Allow incoming P2P connections with rate limiting
iptables -A INPUT -p tcp --dport 26656 -m connlimit --connlimit-above 10 -j REJECT --reject-with tcp-reset
iptables -A INPUT -p tcp --dport 26656 -m recent --set --name p2p_connections
iptables -A INPUT -p tcp --dport 26656 -m recent --update --seconds 60 --hitcount 20 --name p2p_connections -j DROP
iptables -A INPUT -p tcp --dport 26656 -j ACCEPT

# === ABSOLUTELY NO OTHER PORTS ===
# NO SSH (22) - Use console access only
# NO HTTP (80) - No web interface
# NO HTTPS (443) - No API
# NO RPC (26657) - No RPC access
# NO API (8080, 8000, etc) - No API

# DDoS Protection
# SYN flood protection
iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT
iptables -A INPUT -p tcp --syn -j DROP

# Ping flood protection
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s --limit-burst 1 -j ACCEPT
iptables -A INPUT -p icmp --icmp-type echo-request -j DROP

# Port scan protection
iptables -A INPUT -m recent --name portscan --rcheck --seconds 86400 -j DROP
iptables -A INPUT -m recent --name portscan --remove
iptables -A INPUT -p tcp --tcp-flags ALL ALL -m recent --name portscan --set -j LOG --log-prefix "Portscan: "
iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP
iptables -A INPUT -p tcp --tcp-flags ALL NONE -m recent --name portscan --set -j LOG --log-prefix "Portscan: "
iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP

# Block invalid packets
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Log dropped packets (for security monitoring)
iptables -A INPUT -j LOG --log-prefix "BOOTNODE-DROP: " --log-level 4
iptables -A INPUT -j DROP

# Log all other output attempts (security audit)
iptables -A OUTPUT -j LOG --log-prefix "BOOTNODE-OUT: " --log-level 4
iptables -A OUTPUT -j DROP

echo "=== Firewall Rules Applied ==="
echo "ALLOWED:"
echo "  - Loopback traffic"
echo "  - Established connections"
echo "  - DNS queries (outgoing)"
echo "  - NTP sync (outgoing)"
echo "  - P2P connections (port 26656)"
echo ""
echo "BLOCKED:"
echo "  - ALL other incoming traffic"
echo "  - ALL other outgoing traffic"
echo "  - SSH, HTTP, HTTPS, RPC, API"
echo "  - All ports except 26656"
echo ""

# Display current rules
echo "=== Current Firewall Rules ==="
iptables -L -n -v

echo "=== Bootnode Firewall: MAXIMUM SECURITY ENABLED ==="