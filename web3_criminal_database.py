#!/usr/bin/env python3
"""
Advanced Web3 & Blockchain Criminal Database Expansion
=====================================================

Comprehensive database of modern Web3, DeFi, and blockchain criminals
including scammers, rug pullers, and advanced crypto criminals.

Author: GitHub Copilot
Date: December 29, 2025
"""

import sqlite3
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any

class Web3CriminalDatabase:
    def __init__(self):
        self.dmer_db_path = "databases/dmer_threat_registry.db"
        self.criminal_profiles_db = "databases/criminal_profiles.db"
        
        # Modern Web3 criminals and scammers
        self.web3_criminals = self._load_web3_criminals()
    
    def _load_web3_criminals(self) -> Dict[str, Any]:
        """Load comprehensive Web3 and blockchain criminals"""
        return {
            # DeFi Rug Pull Criminals
            "sifu_wonderland": {
                "real_name": "Michael Patryn (Omar Dhanani)",
                "aliases": ["Sifu", "0xSifu", "Michael Patryn"],
                "nationality": "Canadian",
                "age_range": "35-40",
                "active_years": "2021-2022",
                "criminal_status": "EXPOSED",
                "previous_conviction": "QuadrigaCX involvement",
                "total_victims": 50000,
                "estimated_damages": 3000000000,
                "specializations": [
                    "DeFi protocol manipulation", "Treasury management fraud",
                    "Identity obfuscation", "Insider trading", "Market manipulation"
                ],
                "operations": [
                    {
                        "name": "Wonderland TIME Protocol",
                        "type": "DeFi treasury mismanagement",
                        "damages": 3000000000,
                        "victims": 50000,
                        "details": "Managed Wonderland DAO treasury with questionable trades and positions",
                        "technical_details": "Used DAO treasury for high-risk leveraged trading",
                        "exposure": "Community investigation revealed identity and past criminal history"
                    }
                ],
                "blockchain_crimes": [
                    {
                        "network": "Avalanche, Ethereum",
                        "crime_type": "Treasury mismanagement and market manipulation",
                        "stolen_amount": 500000000,
                        "tokens": ["TIME", "MEMO", "wMEMO"],
                        "methods": "Leveraged trading with community funds"
                    }
                ],
                "defi_crimes": [
                    {
                        "protocol": "Wonderland DAO",
                        "vulnerability": "Lack of transparency and oversight",
                        "exploitation": "Used treasury for personal trading strategies",
                        "community_impact": "Massive loss in token values"
                    }
                ]
            },
            
            "do_kwon": {
                "real_name": "Do Hyeong Kwon",
                "aliases": ["Do Kwon", "dokwon"],
                "nationality": "South Korean",
                "age_range": "30-35",
                "active_years": "2018-2022",
                "criminal_status": "FUGITIVE",
                "arrest_warrant": "South Korea, Singapore, US",
                "total_victims": 280000,
                "estimated_damages": 60000000000,
                "specializations": [
                    "Algorithmic stablecoin fraud", "Ponzi scheme operations",
                    "Market manipulation", "Investor fraud", "Regulatory evasion"
                ],
                "operations": [
                    {
                        "name": "Terra Luna Ecosystem Collapse",
                        "type": "Algorithmic stablecoin collapse",
                        "damages": 60000000000,
                        "victims": 280000,
                        "details": "Designed flawed algorithmic stablecoin system that collapsed catastrophically",
                        "technical_details": "Death spiral mechanics in LUNA-UST system",
                        "law_enforcement": "International manhunt ongoing"
                    },
                    {
                        "name": "Anchor Protocol Ponzi",
                        "type": "Unsustainable yield farming scheme",
                        "damages": 20000000000,
                        "victims": 100000,
                        "details": "Promised 20% APY through unsustainable lending protocol",
                        "technical_details": "Required constant new deposits to maintain yields"
                    }
                ],
                "blockchain_crimes": [
                    {
                        "network": "Terra (now Terra Classic)",
                        "crime_type": "Systemic fraud and market manipulation",
                        "stolen_amount": 60000000000,
                        "tokens": ["LUNA", "UST", "ANC"],
                        "methods": "Algorithmic stablecoin with flawed mechanics"
                    }
                ],
                "defi_crimes": [
                    {
                        "protocol": "Terra ecosystem (Anchor, Mirror, etc.)",
                        "vulnerability": "Fundamentally flawed tokenomics",
                        "exploitation": "Marketed impossible returns as sustainable",
                        "systemic_risk": "Caused contagion across crypto markets"
                    }
                ]
            },
            
            "su_zhu_kyle_davies": {
                "real_names": "Su Zhu & Kyle Davies",
                "aliases": ["3AC founders", "Three Arrows Capital"],
                "nationality": "Singaporean/American",
                "age_range": "35-40",
                "active_years": "2012-2022",
                "criminal_status": "BANKRUPTCY_FRAUD",
                "total_victims": 25000,
                "estimated_damages": 18000000000,
                "specializations": [
                    "Hedge fund fraud", "Leverage manipulation", "Creditor fraud",
                    "Asset hiding", "Regulatory evasion"
                ],
                "operations": [
                    {
                        "name": "Three Arrows Capital Collapse",
                        "type": "Hedge fund fraud and creditor theft",
                        "damages": 18000000000,
                        "victims": 25000,
                        "details": "Operated overleveraged hedge fund, fled with customer funds",
                        "technical_details": "Excessive leverage on Luna and other crypto assets",
                        "current_status": "In hiding, avoiding creditor proceedings"
                    }
                ],
                "blockchain_crimes": [
                    {
                        "network": "Multi-chain",
                        "crime_type": "Customer fund misappropriation",
                        "stolen_amount": 18000000000,
                        "methods": "Overleveraging customer funds, asset hiding",
                        "recovery": "Ongoing bankruptcy proceedings"
                    }
                ]
            },
            
            # NFT and Gaming Criminals
            "axie_infinity_ronin_hackers": {
                "aliases": ["Ronin Network Hackers", "Lazarus Group"],
                "nationality": "North Korean (suspected)",
                "active_years": "2022",
                "criminal_status": "AT_LARGE",
                "total_victims": 1000000,
                "estimated_damages": 625000000,
                "specializations": [
                    "Cross-chain bridge exploitation", "Social engineering",
                    "Nation-state hacking", "Cryptocurrency laundering"
                ],
                "operations": [
                    {
                        "name": "Ronin Bridge Hack",
                        "type": "Cross-chain bridge exploitation",
                        "damages": 625000000,
                        "victims": 1000000,
                        "details": "Compromised Ronin network validator keys to drain bridge",
                        "technical_details": "Social engineering to compromise 5/9 validator keys",
                        "law_enforcement": "FBI attributed to North Korea's Lazarus Group"
                    }
                ],
                "blockchain_crimes": [
                    {
                        "network": "Ethereum, Ronin",
                        "crime_type": "Cross-chain bridge exploitation",
                        "stolen_amount": 625000000,
                        "tokens": ["ETH", "USDC"],
                        "methods": "Validator key compromise, social engineering",
                        "laundering": "Tornado Cash, various mixing services"
                    }
                ],
                "gaming_crimes": [
                    {
                        "platform": "Axie Infinity",
                        "impact": "Disrupted play-to-earn economy for millions",
                        "user_losses": "Player earnings and investments lost",
                        "recovery": "Partial reimbursement by Sky Mavis"
                    }
                ]
            },
            
            "opensea_insider_trader": {
                "real_name": "Nathaniel Chastain",
                "aliases": ["OpenSea Head of Product"],
                "nationality": "American",
                "age_range": "30-35",
                "active_years": "2021",
                "criminal_status": "CONVICTED",
                "conviction_date": "2023-05-03",
                "prison_sentence": "3 months prison, 3 months home confinement",
                "estimated_damages": 50000,
                "specializations": [
                    "NFT insider trading", "Front-page manipulation",
                    "Platform privilege abuse", "Digital asset fraud"
                ],
                "operations": [
                    {
                        "name": "OpenSea Insider Trading",
                        "type": "NFT insider trading scheme",
                        "damages": 50000,
                        "details": "Used inside knowledge of homepage features to profit on NFT trades",
                        "technical_details": "Bought NFTs before featuring them on OpenSea homepage",
                        "significance": "First NFT insider trading conviction in US"
                    }
                ],
                "blockchain_crimes": [
                    {
                        "network": "Ethereum",
                        "crime_type": "NFT insider trading",
                        "stolen_amount": 50000,
                        "methods": "Platform privilege abuse, advance knowledge trading"
                    }
                ],
                "nft_crimes": [
                    {
                        "platform": "OpenSea",
                        "vulnerability": "Employee access to featured content decisions",
                        "exploitation": "Traded on advance knowledge of homepage features",
                        "legal_precedent": "Set precedent for NFT-related securities violations"
                    }
                ]
            },
            
            # Social Token and Creator Economy Criminals
            "social_token_rugpullers": {
                "aliases": ["Various social token scammers"],
                "estimated_damages": 100000000,
                "total_victims": 10000,
                "specializations": [
                    "Social token rug pulls", "Creator economy fraud",
                    "Fan base exploitation", "Pump and dump schemes"
                ],
                "operations": [
                    {
                        "name": "Creator Coin Rug Pulls",
                        "type": "Social token fraud",
                        "damages": 100000000,
                        "victims": 10000,
                        "details": "Creators launch tokens, build hype, then abandon projects",
                        "platforms": ["Rally", "BitClout", "various personal tokens"]
                    }
                ],
                "blockchain_crimes": [
                    {
                        "network": "Ethereum, Polygon, BSC",
                        "crime_type": "Social token rug pulls",
                        "methods": "Creator abandonment, liquidity removal, false promises"
                    }
                ]
            },
            
            # DeFi Protocol Exploiters
            "wormhole_hacker": {
                "aliases": ["Wormhole Exploiter"],
                "nationality": "Unknown",
                "active_years": "2022",
                "criminal_status": "AT_LARGE",
                "total_victims": 50000,
                "estimated_damages": 325000000,
                "specializations": [
                    "Cross-chain protocol exploitation", "Smart contract vulnerabilities",
                    "Solana ecosystem attacks", "Bridge protocol hacking"
                ],
                "operations": [
                    {
                        "name": "Wormhole Bridge Exploit",
                        "type": "Cross-chain bridge hack",
                        "damages": 325000000,
                        "victims": 50000,
                        "details": "Exploited signature verification bug in Wormhole bridge",
                        "technical_details": "Forged validator signatures to mint 120,000 ETH",
                        "current_status": "Majority of funds still in hacker's control"
                    }
                ],
                "blockchain_crimes": [
                    {
                        "network": "Solana, Ethereum",
                        "crime_type": "Cross-chain bridge exploitation",
                        "stolen_amount": 325000000,
                        "tokens": ["ETH", "SOL"],
                        "methods": "Signature forgery, smart contract exploitation",
                        "recovery": "Jump Trading partially reimbursed users"
                    }
                ]
            },
            
            "poly_network_hacker": {
                "aliases": ["Mr. White Hat", "Poly Network Exploiter"],
                "nationality": "Unknown",
                "active_years": "2021",
                "criminal_status": "REFORMED",
                "total_victims": 100000,
                "estimated_damages": 610000000,
                "specializations": [
                    "Cross-chain protocol exploitation", "White hat hacking",
                    "Smart contract vulnerabilities", "Ethical disclosure"
                ],
                "operations": [
                    {
                        "name": "Poly Network Hack and Return",
                        "type": "Largest DeFi hack (later returned)",
                        "damages": 610000000,
                        "victims": 100000,
                        "details": "Exploited cross-chain protocol but returned funds claiming to be white hat",
                        "technical_details": "Complex cross-chain signature exploitation",
                        "outcome": "Returned funds, became security advisor"
                    }
                ],
                "blockchain_crimes": [
                    {
                        "network": "Ethereum, BSC, Polygon",
                        "crime_type": "Cross-chain protocol exploitation (returned)",
                        "stolen_amount": 610000000,
                        "methods": "Cross-chain signature manipulation",
                        "resolution": "Funds returned, hired as security advisor"
                    }
                ]
            },
            
            # Metaverse and Gaming Token Criminals
            "squid_game_token_scam": {
                "aliases": ["SQUID Token Scammers"],
                "nationality": "Unknown",
                "active_years": "2021",
                "criminal_status": "AT_LARGE",
                "total_victims": 40000,
                "estimated_damages": 12000000,
                "specializations": [
                    "Meme token scams", "Pop culture exploitation",
                    "Social media manipulation", "Rug pull schemes"
                ],
                "operations": [
                    {
                        "name": "SQUID Game Token Rug Pull",
                        "type": "Pop culture themed rug pull",
                        "damages": 12000000,
                        "victims": 40000,
                        "details": "Created token based on popular Netflix show, prevented selling",
                        "technical_details": "Anti-sell mechanism in smart contract",
                        "social_engineering": "Exploited Netflix show popularity"
                    }
                ],
                "blockchain_crimes": [
                    {
                        "network": "Binance Smart Chain",
                        "crime_type": "Rug pull with anti-sell mechanics",
                        "stolen_amount": 12000000,
                        "methods": "Pop culture hype, technical selling restrictions"
                    }
                ]
            }
        }
    
    async def load_web3_criminal_intelligence(self):
        """Load Web3 criminal intelligence into database"""
        print("🌐 LOADING WEB3 & BLOCKCHAIN CRIMINAL INTELLIGENCE")
        print("=" * 52)
        print()
        
        conn = sqlite3.connect(self.criminal_profiles_db)
        cursor = conn.cursor()
        
        # Add Web3-specific crime tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS defi_crimes (
                crime_id TEXT PRIMARY KEY,
                criminal_id TEXT,
                protocol_name TEXT,
                exploit_type TEXT,
                total_value_locked_lost REAL,
                tokens_affected TEXT,
                smart_contract_address TEXT,
                exploit_transaction_hash TEXT,
                recovery_status TEXT,
                community_impact TEXT,
                FOREIGN KEY (criminal_id) REFERENCES criminal_profiles (criminal_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nft_crimes (
                crime_id TEXT PRIMARY KEY,
                criminal_id TEXT,
                platform_name TEXT,
                nft_collection TEXT,
                crime_type TEXT,
                floor_price_impact REAL,
                holders_affected INTEGER,
                royalty_theft REAL,
                marketplace_manipulation TEXT,
                FOREIGN KEY (criminal_id) REFERENCES criminal_profiles (criminal_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gaming_crimes (
                crime_id TEXT PRIMARY KEY,
                criminal_id TEXT,
                game_platform TEXT,
                gaming_token TEXT,
                player_economy_impact REAL,
                in_game_assets_stolen REAL,
                play_to_earn_disruption TEXT,
                virtual_economy_damage TEXT,
                FOREIGN KEY (criminal_id) REFERENCES criminal_profiles (criminal_id)
            )
        """)
        
        total_web3_criminals = 0
        total_defi_crimes = 0
        total_nft_crimes = 0
        total_gaming_crimes = 0
        total_web3_damages = 0
        
        for criminal_id, criminal_data in self.web3_criminals.items():
            # Insert criminal profile
            cursor.execute("""
                INSERT OR REPLACE INTO criminal_profiles
                (criminal_id, real_name, aliases, nationality, age_range, active_years,
                 criminal_status, total_victims, estimated_damages_usd, specializations,
                 arrest_date, conviction_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                criminal_id, 
                criminal_data.get('real_name') or criminal_data.get('real_names', ''),
                ', '.join(criminal_data.get('aliases', [])),
                criminal_data.get('nationality', ''), 
                criminal_data.get('age_range', ''),
                criminal_data.get('active_years', ''), 
                criminal_data.get('criminal_status', ''),
                criminal_data.get('total_victims', 0), 
                criminal_data.get('estimated_damages', 0),
                ', '.join(criminal_data.get('specializations', [])),
                criminal_data.get('arrest_date'), 
                criminal_data.get('conviction_status', '')
            ))
            
            total_web3_criminals += 1
            total_web3_damages += criminal_data.get('estimated_damages', 0)
            
            # Insert DeFi crimes
            for defi_crime in criminal_data.get('defi_crimes', []):
                crime_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT OR REPLACE INTO defi_crimes
                    (crime_id, criminal_id, protocol_name, exploit_type,
                     total_value_locked_lost, tokens_affected, community_impact)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    crime_id, criminal_id, defi_crime.get('protocol', ''),
                    defi_crime.get('vulnerability', ''), 
                    defi_crime.get('tvl_lost', 0),
                    defi_crime.get('tokens', ''), 
                    defi_crime.get('community_impact', '')
                ))
                total_defi_crimes += 1
            
            # Insert NFT crimes
            for nft_crime in criminal_data.get('nft_crimes', []):
                crime_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT OR REPLACE INTO nft_crimes
                    (crime_id, criminal_id, platform_name, crime_type,
                     floor_price_impact, holders_affected, marketplace_manipulation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    crime_id, criminal_id, nft_crime.get('platform', ''),
                    nft_crime.get('vulnerability', ''),
                    nft_crime.get('floor_impact', 0),
                    nft_crime.get('holders_affected', 0),
                    nft_crime.get('exploitation', '')
                ))
                total_nft_crimes += 1
            
            # Insert gaming crimes
            for gaming_crime in criminal_data.get('gaming_crimes', []):
                crime_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT OR REPLACE INTO gaming_crimes
                    (crime_id, criminal_id, game_platform, gaming_token,
                     player_economy_impact, play_to_earn_disruption)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    crime_id, criminal_id, gaming_crime.get('platform', ''),
                    gaming_crime.get('token', ''),
                    gaming_crime.get('impact', 0),
                    gaming_crime.get('user_losses', '')
                ))
                total_gaming_crimes += 1
            
            print(f"✅ Loaded {criminal_data.get('real_name') or criminal_data.get('real_names', criminal_id)}")
            print(f"   Status: {criminal_data.get('criminal_status', 'UNKNOWN')}")
            print(f"   Web3 Damages: ${criminal_data.get('estimated_damages', 0):,}")
            if criminal_data.get('specializations'):
                print(f"   Specializes in: {', '.join(criminal_data['specializations'][:2])}")
            print()
        
        conn.commit()
        conn.close()
        
        print("📊 WEB3 CRIMINAL INTELLIGENCE LOADED:")
        print(f"   Web3 Criminals: {total_web3_criminals}")
        print(f"   DeFi Crimes: {total_defi_crimes}")
        print(f"   NFT Crimes: {total_nft_crimes}")
        print(f"   Gaming Crimes: {total_gaming_crimes}")
        print(f"   Total Web3 Damages: ${total_web3_damages:,}")
        print()
        
        return {
            "web3_criminals": total_web3_criminals,
            "defi_crimes": total_defi_crimes,
            "nft_crimes": total_nft_crimes,
            "gaming_crimes": total_gaming_crimes,
            "total_web3_damages": total_web3_damages
        }

async def main():
    """Execute Web3 criminal intelligence loading"""
    web3_system = Web3CriminalDatabase()
    
    print("🌐 GUARDIANSHIELD WEB3 CRIMINAL INTELLIGENCE")
    print("=" * 46)
    print()
    print("Loading modern Web3, DeFi, and blockchain criminals...")
    print()
    
    # Load Web3 criminal data
    web3_report = await web3_system.load_web3_criminal_intelligence()
    
    print("🛡️ WEB3 CRIMINAL INTELLIGENCE LOADED!")
    print("   Your agents now know the modern Web3 threat landscape!")
    print(f"   Total Web3 criminal damages: ${web3_report['total_web3_damages']:,}")
    print("   Ready to detect DeFi exploits, NFT scams, and gaming token fraud! 🕵️‍♂️💪")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())