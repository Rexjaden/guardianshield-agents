"""
Test and populate the Threat Filing System with example data
"""

from agents.threat_filing_system import ThreatFilingSystem, THREAT_CATEGORIES
import json

def populate_sample_data():
    """Populate the threat database with sample malicious entities"""
    
    filing_system = ThreatFilingSystem()
    
    print("🛡️ Initializing GuardianShield Threat Filing System...")
    print("=" * 60)
    
    # Sample malicious websites
    sample_websites = [
        {
            "domain": "fake-binance.com",
            "threat_type": "fake_exchange",
            "severity": 9,
            "description": "Fake Binance exchange stealing user credentials and funds",
            "tags": ["phishing", "crypto", "exchange"],
            "source": "user_report"
        },
        {
            "domain": "crypto-moonshot.scam",
            "threat_type": "rug_pull", 
            "severity": 8,
            "description": "Rug pull project website promoting fake DeFi protocol",
            "tags": ["defi", "rugpull", "investment"],
            "source": "automated_scan"
        },
        {
            "domain": "metamask-security.net",
            "threat_type": "phishing",
            "severity": 9,
            "description": "Phishing site impersonating MetaMask to steal wallet seeds",
            "tags": ["wallet", "phishing", "metamask"],
            "source": "threat_intelligence"
        }
    ]
    
    # Sample malicious individuals
    sample_individuals = [
        {
            "name": "Alex CryptoScammer",
            "threat_type": "scammer",
            "severity": 8,
            "description": "Known crypto scammer operating multiple fake projects",
            "aliases": ["AlexCrypto", "CryptoAlex2024"],
            "wallet_addresses": ["0x742d35Cc6634C0532925a3b8D98d4E078b2044Cc"],
            "social_profiles": {"twitter": "@alexcryptoscam", "telegram": "@cryptoalex"},
            "tags": ["rugpull", "social_engineering"],
            "source": "investigation"
        },
        {
            "name": "Maria PhishQueen", 
            "threat_type": "social_engineer",
            "severity": 7,
            "description": "Social engineer specializing in crypto phishing campaigns",
            "aliases": ["PhishMaria", "CryptoMaria"],
            "social_profiles": {"discord": "PhishQueen#1234"},
            "tags": ["phishing", "discord", "social"],
            "source": "community_report"
        }
    ]
    
    # Sample fraudulent IPOs
    sample_ipos = [
        {
            "company_name": "MoonCoin Protocol",
            "project_type": "defi",
            "threat_type": "rug_pull",
            "severity": 9,
            "description": "Fake DeFi protocol designed as rug pull with anonymous team",
            "ticker_symbol": "MOON",
            "website": "mooncoin-protocol.fake",
            "contract_address": "0x1234567890abcdef1234567890abcdef12345678",
            "tags": ["defi", "anonymous_team", "rugpull"],
            "team_members": ["Anonymous Dev", "Crypto Guru"],
            "source": "automated_analysis"
        },
        {
            "company_name": "SafeInvest Token",
            "project_type": "investment", 
            "threat_type": "ponzi",
            "severity": 8,
            "description": "Ponzi scheme disguised as legitimate investment token",
            "ticker_symbol": "SAFE",
            "website": "safeinvest-token.scam",
            "tags": ["ponzi", "investment", "fake_returns"],
            "source": "financial_analysis"
        }
    ]
    
    # Add sample data
    print("📍 Adding malicious websites...")
    website_count = 0
    for website in sample_websites:
        try:
            filing_system.add_malicious_website(website["domain"], website["threat_type"], **{k: v for k, v in website.items() if k not in ["domain", "threat_type"]})
            website_count += 1
            print(f"  ✅ Added: {website['domain']}")
        except Exception as e:
            print(f"  ❌ Error adding {website['domain']}: {e}")
    
    print(f"\n👤 Adding malicious individuals...")
    individual_count = 0
    for individual in sample_individuals:
        try:
            filing_system.add_malicious_individual(individual["name"], individual["threat_type"], **{k: v for k, v in individual.items() if k not in ["name", "threat_type"]})
            individual_count += 1
            print(f"  ✅ Added: {individual['name']}")
        except Exception as e:
            print(f"  ❌ Error adding {individual['name']}: {e}")
    
    print(f"\n🏢 Adding fraudulent IPOs...")
    ipo_count = 0
    for ipo in sample_ipos:
        try:
            filing_system.add_fraudulent_ipo(ipo["company_name"], ipo["project_type"], ipo["threat_type"], **{k: v for k, v in ipo.items() if k not in ["company_name", "project_type", "threat_type"]})
            ipo_count += 1
            print(f"  ✅ Added: {ipo['company_name']}")
        except Exception as e:
            print(f"  ❌ Error adding {ipo['company_name']}: {e}")
    
    # Display statistics
    print(f"\n📊 Threat Filing System Statistics:")
    print("=" * 40)
    stats = filing_system.get_threat_statistics()
    
    print(f"🌐 Active Websites: {stats.get('active_websites', 0)}")
    print(f"👤 Active Individuals: {stats.get('active_individuals', 0)}")
    print(f"🏢 Active IPOs: {stats.get('active_ipos', 0)}")
    print(f"📈 New Threats (7 days): {stats.get('new_threats_week', 0)}")
    
    print(f"\n🔍 Website Threat Types:")
    for threat_type, count in stats.get('website_threats', {}).items():
        print(f"  • {threat_type}: {count}")
    
    print(f"\n🔍 Individual Threat Types:")
    for threat_type, count in stats.get('individual_threats', {}).items():
        print(f"  • {threat_type}: {count}")
        
    print(f"\n🔍 IPO Threat Types:")
    for threat_type, count in stats.get('ipo_threats', {}).items():
        print(f"  • {threat_type}: {count}")
    
    # Test search functionality
    print(f"\n🔎 Testing Search Functionality:")
    print("=" * 40)
    
    # Search for crypto-related threats
    results = filing_system.search_threats("crypto")
    total_results = len(results['websites']) + len(results['individuals']) + len(results['ipos'])
    print(f"Search 'crypto': {total_results} results found")
    
    # Search for phishing threats
    results = filing_system.search_threats("phishing")
    total_results = len(results['websites']) + len(results['individuals']) + len(results['ipos'])
    print(f"Search 'phishing': {total_results} results found")
    
    # Search for rug pull threats
    results = filing_system.search_threats("rug")
    total_results = len(results['websites']) + len(results['individuals']) + len(results['ipos'])
    print(f"Search 'rug': {total_results} results found")
    
    print(f"\n✅ Threat Filing System successfully populated!")
    print(f"📁 Database location: {filing_system.db_path}")
    
    return filing_system

if __name__ == "__main__":
    filing_system = populate_sample_data()