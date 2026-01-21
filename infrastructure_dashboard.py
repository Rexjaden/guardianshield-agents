#!/usr/bin/env python3
"""
GuardianShield Infrastructure Dashboard
Real-time overview of all deployed services
"""

import subprocess
import json
from datetime import datetime

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
WHITE = "\033[97m"
RESET = "\033[0m"
BOLD = "\033[1m"

def run_cmd(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip()
    except:
        return ""

def get_container_stats():
    """Get all container stats"""
    output = run_cmd('docker ps --format "{{.Names}}|{{.Status}}|{{.Ports}}"')
    containers = []
    for line in output.split('\n'):
        if line and '|' in line:
            parts = line.split('|')
            if len(parts) >= 3:
                containers.append({
                    'name': parts[0],
                    'status': parts[1],
                    'ports': parts[2]
                })
    return containers

def print_header():
    print(f"\n{CYAN}{'='*80}{RESET}")
    print(f"{BOLD}{WHITE}        🛡️  GuardianShield Infrastructure Dashboard  🛡️{RESET}")
    print(f"{CYAN}{'='*80}{RESET}")
    print(f"{YELLOW}Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}\n")

def print_section(title):
    print(f"\n{BLUE}{'─'*40}{RESET}")
    print(f"{BOLD}{WHITE}  {title}{RESET}")
    print(f"{BLUE}{'─'*40}{RESET}")

def main():
    print_header()
    containers = get_container_stats()
    
    # Categorize containers
    core_services = []
    monitoring = []
    validators = []
    databases = []
    infrastructure = []
    ssl_ready = []
    
    for c in containers:
        name = c['name']
        if 'grafana' in name or 'prometheus' in name or 'monitor' in name:
            monitoring.append(c)
        elif 'validator' in name and 'monitor' not in name:
            validators.append(c)
        elif 'db' in name or 'postgres' in name or 'redis' in name or 'etcd' in name:
            databases.append(c)
        elif 'certbot' in name or 'ssl' in name:
            ssl_ready.append(c)
        elif 'guardianshield-main' in name or 'orchestrator' in name or 'key-manager' in name:
            core_services.append(c)
        else:
            infrastructure.append(c)
    
    def print_container(c, indent="  "):
        status = c['status']
        if 'healthy' in status.lower():
            status_icon = f"{GREEN}✓{RESET}"
        elif 'unhealthy' in status.lower():
            status_icon = f"{YELLOW}⚠{RESET}"
        elif 'Up' in status:
            status_icon = f"{GREEN}●{RESET}"
        else:
            status_icon = f"{RED}✗{RESET}"
        
        ports = c['ports'].replace('0.0.0.0:', '').replace('[::]:','')[:50]
        print(f"{indent}{status_icon} {WHITE}{c['name']:<35}{RESET} {ports}")
    
    print_section("🏠 Core Services")
    for c in core_services:
        print_container(c)
    
    print_section("📊 Monitoring Stack")
    for c in monitoring:
        print_container(c)
    
    print_section("🗄️ Databases & Cache")
    for c in databases:
        print_container(c)
    
    print_section("🔒 Validators")
    for c in validators:
        print_container(c)
    
    print_section("🔧 Infrastructure")
    for c in infrastructure:
        print_container(c)
    
    if ssl_ready:
        print_section("🔐 SSL Ready (Standby)")
        for c in ssl_ready:
            print_container(c)
    
    print(f"\n{CYAN}{'─'*40}{RESET}")
    print(f"{BOLD}📈 Summary:{RESET}")
    print(f"   Total Containers: {GREEN}{len(containers)}{RESET}")
    
    # Get memory usage
    mem_output = run_cmd('docker stats --no-stream --format "{{.MemUsage}}" 2>nul')
    if mem_output:
        total_mb = 0
        for line in mem_output.split('\n'):
            if 'MiB' in line:
                try:
                    total_mb += float(line.split('MiB')[0])
                except:
                    pass
            elif 'GiB' in line:
                try:
                    total_mb += float(line.split('GiB')[0]) * 1024
                except:
                    pass
        print(f"   Memory Usage: {GREEN}{total_mb:.0f} MiB{RESET} ({total_mb/15958*100:.1f}% of 15.58GB)")
    
    print(f"\n{CYAN}{'='*80}{RESET}")
    
    # Service URLs
    print(f"\n{BOLD}{WHITE}🌐 Service URLs:{RESET}")
    urls = [
        ("Main API", "http://localhost:8000"),
        ("Grafana Dashboard", "http://localhost:3000 (admin/guardian2026)"),
        ("Prometheus", "http://localhost:9090"),
        ("phpMyAdmin", "http://localhost:8080"),
        ("Envoy Admin", "http://localhost:9901"),
        ("Ollama LLM", "http://localhost:11434"),
        ("CoreDNS Metrics", "http://localhost:9153/metrics"),
    ]
    for name, url in urls:
        print(f"   {CYAN}•{RESET} {name}: {url}")
    
    print(f"\n{YELLOW}SSL containers on standby - ready for website deployment{RESET}")
    print()

if __name__ == "__main__":
    main()
