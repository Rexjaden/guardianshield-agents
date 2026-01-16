#!/usr/bin/env python3
"""
GuardianShield IP Protection Management Script
Manage IP protection settings and view security status
"""

import sys
import os
import json
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

def main():
    print("🛡️ GuardianShield IP Protection Management")
    print("=" * 50)
    
    while True:
        print(f"\n🔒 IP Protection Options:")
        print("1. 📊 View Protection Status")
        print("2. ➕ Add Admin IP Address")
        print("3. ➖ Remove Admin IP Address")
        print("4. 📋 List Admin IP Addresses")
        print("5. 📈 View IP Access Logs")
        print("6. ⚙️ Configure Protection Settings")
        print("7. 🎯 Test IP Access")
        print("8. 🌍 Configure Geographic Blocking")
        print("9. 📊 Generate IP Security Report")
        print("0. Exit")
        
        choice = input("\nSelect option (0-9): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            view_protection_status()
        elif choice == "2":
            add_admin_ip()
        elif choice == "3":
            remove_admin_ip()
        elif choice == "4":
            list_admin_ips()
        elif choice == "5":
            view_access_logs()
        elif choice == "6":
            configure_settings()
        elif choice == "7":
            test_ip_access()
        elif choice == "8":
            configure_geo_blocking()
        elif choice == "9":
            generate_security_report()
        else:
            print("❌ Invalid option")
    
    print("\n✅ IP Protection management session completed!")

def view_protection_status():
    """View current IP protection status"""
    print("\n📊 IP Protection Status")
    print("-" * 30)
    
    try:
        from ip_protection_manager import ip_protection
        
        status = ip_protection.get_protection_status()
        
        print(f"🛡️ Protection Enabled: {'✅' if status['protection_enabled'] else '❌'}")
        print(f"🌐 Server IP: {status['server_ip']}")
        print(f"🔓 Website Accessible: {'✅' if status['website_accessible'] else '❌'}")
        print(f"🔑 Admin IPs Configured: {status['admin_ips_configured']}")
        print(f"⚠️ Threat Cache Entries: {status['threat_cache_entries']}")
        print(f"🚨 High Threat IPs: {status['high_threat_ips']}")
        print(f"⏰ Active Rate Limits: {status['active_rate_limits']}")
        print(f"🌍 Geo Blocking: {'✅' if status['geo_blocking_enabled'] else '❌'}")
        print(f"🔒 Privacy Protection: {'✅' if status['privacy_protection'] else '❌'}")
        print(f"📅 Last Updated: {status['last_updated'][:19]}")
        
    except Exception as e:
        print(f"❌ Failed to get status: {e}")

def add_admin_ip():
    """Add IP address to admin whitelist"""
    print("\n➕ Add Admin IP Address")
    print("-" * 25)
    
    try:
        from ip_protection_manager import ip_protection
        
        # Show current IP for convenience
        import requests
        try:
            current_ip = requests.get("https://ipinfo.io/ip", timeout=5).text.strip()
            print(f"💡 Your current IP: {current_ip}")
        except:
            print("💡 Could not detect your current IP")
        
        ip_address = input("Enter IP address to add: ").strip()
        
        if not ip_address:
            print("❌ IP address is required")
            return
        
        result = ip_protection.add_admin_ip(ip_address)
        
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
    
    except Exception as e:
        print(f"❌ Failed to add admin IP: {e}")

def remove_admin_ip():
    """Remove IP address from admin whitelist"""
    print("\n➖ Remove Admin IP Address")
    print("-" * 28)
    
    try:
        from ip_protection_manager import ip_protection
        
        # Show current admin IPs
        admin_ips = ip_protection.config['admin_access']['allowed_admin_ips']
        
        if not admin_ips:
            print("📝 No admin IP addresses configured")
            return
        
        print("Current admin IPs:")
        for i, ip in enumerate(admin_ips, 1):
            print(f"  {i}. {ip}")
        
        selection = input("\nEnter IP address or number to remove: ").strip()
        
        if selection.isdigit():
            idx = int(selection) - 1
            if 0 <= idx < len(admin_ips):
                ip_address = admin_ips[idx]
            else:
                print("❌ Invalid selection")
                return
        else:
            ip_address = selection
        
        if not ip_address:
            print("❌ IP address is required")
            return
        
        result = ip_protection.remove_admin_ip(ip_address)
        
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
    
    except Exception as e:
        print(f"❌ Failed to remove admin IP: {e}")

def list_admin_ips():
    """List all admin IP addresses"""
    print("\n📋 Admin IP Addresses")
    print("-" * 21)
    
    try:
        from ip_protection_manager import ip_protection
        
        config = ip_protection.config
        admin_ips = config['admin_access']['allowed_admin_ips']
        ip_ranges = config['admin_access']['allowed_ip_ranges']
        
        print(f"🔑 Individual Admin IPs ({len(admin_ips)}):")
        if admin_ips:
            for i, ip in enumerate(admin_ips, 1):
                print(f"  {i}. {ip}")
        else:
            print("  None configured")
        
        print(f"\n🌐 IP Ranges ({len(ip_ranges)}):")
        if ip_ranges:
            for i, ip_range in enumerate(ip_ranges, 1):
                print(f"  {i}. {ip_range}")
        else:
            print("  None configured")
        
        print(f"\n⚙️ Whitelist Enabled: {'✅' if config['admin_access']['ip_whitelist_enabled'] else '❌'}")
    
    except Exception as e:
        print(f"❌ Failed to list admin IPs: {e}")

def view_access_logs():
    """View recent IP access logs"""
    print("\n📈 IP Access Logs")
    print("-" * 17)
    
    try:
        log_file = "ip_access_log.jsonl"
        
        if not os.path.exists(log_file):
            print("📝 No access logs found yet")
            return
        
        limit = input("Number of recent entries to show (default: 20): ").strip()
        limit = int(limit) if limit.isdigit() else 20
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        print(f"\n📊 Recent {min(limit, len(lines))} Access Events:")
        print("-" * 60)
        
        for line in lines[-limit:]:
            try:
                entry = json.loads(line.strip())
                timestamp = entry['timestamp'][:19]
                client_ip = entry.get('client_ip', 'unknown')
                event_type = entry.get('event_type', 'unknown')
                
                print(f"{timestamp} | {client_ip:<20} | {event_type}")
                
                # Show details for important events
                if event_type in ['admin_access_denied', 'rate_limit_exceeded']:
                    details = entry.get('details', {})
                    reason = details.get('reason', 'No reason provided')
                    print(f"                     └─ {reason}")
            
            except Exception:
                continue
        
        print(f"\n📈 Total log entries: {len(lines)}")
    
    except Exception as e:
        print(f"❌ Failed to view access logs: {e}")

def configure_settings():
    """Configure IP protection settings"""
    print("\n⚙️ Configure Protection Settings")
    print("-" * 32)
    
    try:
        from ip_protection_manager import ip_protection
        
        config = ip_protection.config
        
        print("Current Settings:")
        print(f"  Rate Limiting: {config['rate_limiting']['enabled']}")
        print(f"  Requests/Minute: {config['rate_limiting']['requests_per_minute']}")
        print(f"  Temp Ban (mins): {config['rate_limiting']['temporary_ban_minutes']}")
        print(f"  Anonymize Logs: {config['privacy_protection']['anonymize_logs']}")
        print(f"  DDoS Protection: {config['ddos_protection']['enabled']}")
        
        print("\n🔧 What would you like to configure?")
        print("1. Rate Limiting")
        print("2. Privacy Protection")
        print("3. DDoS Protection")
        print("4. Back to main menu")
        
        choice = input("Select option (1-4): ").strip()
        
        if choice == "1":
            configure_rate_limiting(config)
        elif choice == "2":
            configure_privacy_protection(config)
        elif choice == "3":
            configure_ddos_protection(config)
        elif choice == "4":
            return
        else:
            print("❌ Invalid option")
    
    except Exception as e:
        print(f"❌ Failed to configure settings: {e}")

def configure_rate_limiting(config):
    """Configure rate limiting settings"""
    print("\n⚡ Rate Limiting Configuration")
    
    current_rpm = config['rate_limiting']['requests_per_minute']
    new_rpm = input(f"Requests per minute (current: {current_rpm}): ").strip()
    if new_rpm.isdigit():
        config['rate_limiting']['requests_per_minute'] = int(new_rpm)
    
    current_ban = config['rate_limiting']['temporary_ban_minutes']
    new_ban = input(f"Temporary ban duration in minutes (current: {current_ban}): ").strip()
    if new_ban.isdigit():
        config['rate_limiting']['temporary_ban_minutes'] = int(new_ban)
    
    # Save configuration
    with open("ip_protection_config.json", 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Rate limiting settings updated")

def configure_privacy_protection(config):
    """Configure privacy protection settings"""
    print("\n🔒 Privacy Protection Configuration")
    
    current_anon = config['privacy_protection']['anonymize_logs']
    toggle = input(f"Anonymize logs (current: {current_anon}, toggle? y/n): ").strip().lower()
    if toggle == 'y':
        config['privacy_protection']['anonymize_logs'] = not current_anon
    
    current_hash = config['privacy_protection']['hash_client_ips']
    toggle = input(f"Hash client IPs (current: {current_hash}, toggle? y/n): ").strip().lower()
    if toggle == 'y':
        config['privacy_protection']['hash_client_ips'] = not current_hash
    
    # Save configuration
    with open("ip_protection_config.json", 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Privacy protection settings updated")

def configure_ddos_protection(config):
    """Configure DDoS protection settings"""
    print("\n🛡️ DDoS Protection Configuration")
    
    current_threshold = config['ddos_protection']['connection_threshold']
    new_threshold = input(f"Connection threshold per IP (current: {current_threshold}): ").strip()
    if new_threshold.isdigit():
        config['ddos_protection']['connection_threshold'] = int(new_threshold)
    
    # Save configuration
    with open("ip_protection_config.json", 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ DDoS protection settings updated")

def test_ip_access():
    """Test IP access validation"""
    print("\n🎯 Test IP Access")
    print("-" * 16)
    
    try:
        from ip_protection_manager import ip_protection
        
        test_ip = input("Enter IP address to test: ").strip()
        if not test_ip:
            print("❌ IP address is required")
            return
        
        access_type = input("Access type (general/admin) [general]: ").strip() or "general"
        
        result = ip_protection.validate_ip_access(test_ip, access_type)
        
        print(f"\n📊 Test Results for {test_ip}:")
        print(f"  Access Allowed: {'✅' if result['allowed'] else '❌'}")
        print(f"  Anonymized IP: {result['anonymized_ip']}")
        print(f"  Access Type: {result['access_type']}")
        
        if not result['allowed']:
            print(f"  Primary Reason: {result.get('primary_reason', 'Unknown')}")
        
        if 'checks' in result:
            print(f"\n🔍 Individual Checks:")
            for check_name, check_result in result['checks'].items():
                status = "✅" if check_result.get('allowed', True) else "❌"
                print(f"  {check_name}: {status} - {check_result.get('reason', 'No reason')}")
    
    except Exception as e:
        print(f"❌ Failed to test IP access: {e}")

def configure_geo_blocking():
    """Configure geographic IP blocking"""
    print("\n🌍 Geographic IP Blocking")
    print("-" * 25)
    
    try:
        from ip_protection_manager import ip_protection
        
        config = ip_protection.config
        geo_config = config['geo_blocking']
        
        print(f"Current Status: {'✅' if geo_config['enabled'] else '❌'}")
        print(f"Blocked Countries: {', '.join(geo_config['blocked_countries']) if geo_config['blocked_countries'] else 'None'}")
        print(f"Allowed Countries: {', '.join(geo_config['allowed_countries']) if geo_config['allowed_countries'] else 'All'}")
        
        print(f"\n⚠️ Note: Geographic blocking requires IP geolocation services")
        print(f"Current implementation is a placeholder for demonstration")
        
        enable = input("Enable geographic blocking? (y/n): ").strip().lower()
        if enable == 'y':
            config['geo_blocking']['enabled'] = True
            print("✅ Geographic blocking enabled (requires implementation)")
        elif enable == 'n':
            config['geo_blocking']['enabled'] = False
            print("❌ Geographic blocking disabled")
        
        # Save configuration
        with open("ip_protection_config.json", 'w') as f:
            json.dump(config, f, indent=2)
    
    except Exception as e:
        print(f"❌ Failed to configure geo blocking: {e}")

def generate_security_report():
    """Generate comprehensive IP security report"""
    print("\n📊 Generating IP Security Report...")
    print("-" * 35)
    
    try:
        from ip_protection_manager import ip_protection
        
        # Get protection status
        status = ip_protection.get_protection_status()
        
        # Analyze logs
        log_stats = {"total_events": 0, "denied_access": 0, "rate_limited": 0}
        
        log_file = "ip_access_log.jsonl"
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        log_stats["total_events"] += 1
                        
                        event_type = entry.get('event_type', '')
                        if 'denied' in event_type:
                            log_stats["denied_access"] += 1
                        elif 'rate_limit' in event_type:
                            log_stats["rate_limited"] += 1
                    except:
                        continue
        
        # Generate report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "protection_status": status,
            "access_statistics": log_stats,
            "security_recommendations": []
        }
        
        # Add recommendations
        if status["high_threat_ips"] > 0:
            report["security_recommendations"].append("Review high-threat IP addresses")
        
        if status["admin_ips_configured"] == 0:
            report["security_recommendations"].append("Configure admin IP whitelist")
        
        if not status["privacy_protection"]:
            report["security_recommendations"].append("Enable IP anonymization for privacy")
        
        if log_stats["denied_access"] > 100:
            report["security_recommendations"].append("High number of access denials - investigate potential attacks")
        
        # Save report
        report_file = f"ip_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 IP Security Report")
        print(f"📅 Generated: {report['timestamp'][:19]}")
        print(f"🛡️ Protection Status: {'ACTIVE' if status['protection_enabled'] else 'INACTIVE'}")
        print(f"🔑 Admin IPs: {status['admin_ips_configured']}")
        print(f"⚠️ High Threat IPs: {status['high_threat_ips']}")
        print(f"📈 Total Events: {log_stats['total_events']}")
        print(f"❌ Denied Access: {log_stats['denied_access']}")
        print(f"⏰ Rate Limited: {log_stats['rate_limited']}")
        
        if report["security_recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in report["security_recommendations"]:
                print(f"  • {rec}")
        
        print(f"\n💾 Full report saved: {report_file}")
    
    except Exception as e:
        print(f"❌ Failed to generate security report: {e}")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")