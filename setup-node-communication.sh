#!/bin/bash
# GuardianShield Node Communication Setup
# Rex Judon Rogers - Quick Setup for Secure Node Access

echo "GuardianShield Secure Node Communication Setup"
echo "=============================================="
echo "Rex Judon Rogers - Admin Access"
echo

# Test CLI tool
echo "[+] Testing CLI tool..."
python guardian-cli.py auth

echo
echo "[+] Quick Command Examples:"
echo "   python guardian-cli.py list          # List all nodes"
echo "   python guardian-cli.py status        # Node status report" 
echo "   python guardian-cli.py security      # Security report"
echo "   python guardian-cli.py logs --region us-east-1   # View logs"
echo

echo "[+] SSH Configuration:"
echo "   Config file: ssh-config"
echo "   Copy to ~/.ssh/config for quick access"
echo

echo "[+] Node Endpoints:"
echo "   API: https://api.guardian-shield.network"
echo "   Dashboard: https://manage.guardian-shield.network"
echo "   Monitoring: https://monitor.guardian-shield.network"
echo

echo "[+] Security Features:"
echo "   - Rex-only authentication"
echo "   - Encrypted communication"
echo "   - Rate limiting and DDoS protection"
echo "   - Real-time threat monitoring"
echo

echo "Setup Complete! Nodes are ready for secure communication."