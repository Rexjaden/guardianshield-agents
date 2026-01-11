#!/usr/bin/env python3
"""
GuardianShield GUARD Token Purchase Platform
Comprehensive token purchase system with fiat and crypto support

LIVE CONTRACT ADDRESSES:
- GuardianTokenSale: 0xC6A4a2591bb0a9d1f45397da616dBc27e4b7BC8d (DEPLOYED)
"""

import uvicorn
import sqlite3
import hashlib
import json
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# LIVE CONTRACT CONFIGURATION
LIVE_CONTRACTS = {
    "GuardianTokenSale": "0xC6A4a2591bb0a9d1f45397da616dBc27e4b7BC8d",
    "network": "ethereum",
    "chainId": 1,
    "rpcUrl": "https://eth-mainnet.alchemyapi.io/v2/YOUR-API-KEY"
}

# Payment Methods
class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    CRYPTO = "crypto"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"

# Purchase Status
class PurchaseStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

# Pydantic Models
class GuardPurchaseRequest(BaseModel):
    guard_amount: float
    payment_method: PaymentMethod
    payment_currency: str  # USD, EUR, BTC, ETH, etc.
    customer_email: str
    customer_wallet: str
    billing_address: Optional[Dict[str, str]] = None
    promo_code: Optional[str] = None

class CreditCardInfo(BaseModel):
    card_number: str
    expiry_month: int
    expiry_year: int
    cvv: str
    holder_name: str

@dataclass
class GuardPurchase:
    purchase_id: str
    guard_amount: float
    payment_amount: float
    payment_currency: str
    payment_method: PaymentMethod
    customer_email: str
    customer_wallet: str
    guard_price_usd: float
    exchange_rate: float
    status: PurchaseStatus
    created_timestamp: datetime
    completed_timestamp: Optional[datetime]
    transaction_hash: Optional[str]
    promo_discount: float
    fees: float
    net_amount: float

class TokenPurchaseManager:
    """Manages GUARD token purchases and delivery"""
    
    def __init__(self, db_path: str = "guard_purchases.db"):
        self.db_path = db_path
        self.init_database()
        
        # Dynamic GUARD token pricing system
        self.base_price_usd = 0.005  # Starting price: $0.005
        self.total_supply = 5_000_000_000  # 5 billion tokens
        self.circulating_supply = 300_000_000  # Initial 300M in circulation
        self.liquidity_pool_usd = 50_000  # Starting liquidity pool
        self.guard_price_usd = self.calculate_dynamic_price()
        
        # Supported fiat currencies with exchange rates
        self.fiat_rates = {
            'USD': 1.0,
            'EUR': 0.85,
            'GBP': 0.73,
            'JPY': 110.0,
            'CAD': 1.25,
            'AUD': 1.35
        }
        
        # Crypto exchange rates (simplified)
        self.crypto_rates = {
            'BTC': 45000.0,
            'ETH': 3200.0,
            'SOL': 85.0,
            'BNB': 320.0,
            'ADA': 0.65,
            'USDT': 1.0,
            'USDC': 1.0
        }
        
        # Promo codes
        self.promo_codes = {
            'LAUNCH25': 0.25,  # 25% discount
            'EARLY15': 0.15,   # 15% discount
            'SHIELD10': 0.10,  # 10% discount
            'FIRST5': 0.05     # 5% discount
        }
    
    def calculate_dynamic_price(self) -> float:
        """Calculate dynamic GUARD token price based on market conditions"""
        # Get current market data
        market_data = self.get_market_data()
        
        # Base price factors
        base_price = self.base_price_usd
        
        # Liquidity factor (higher liquidity = more stable price)
        liquidity_factor = min(2.0, max(0.5, market_data['liquidity_pool_usd'] / 100_000))
        
        # Supply circulation factor (less circulating = higher price pressure)
        circulation_ratio = self.circulating_supply / self.total_supply
        supply_factor = 1 + (0.5 * (1 - circulation_ratio))  # Price increases as less is circulating
        
        # Market cap factor (simulated market pressure)
        target_market_cap = self.liquidity_pool_usd * 20  # Target 20x liquidity as market cap
        current_market_cap = self.circulating_supply * base_price
        market_cap_factor = min(3.0, max(0.3, target_market_cap / current_market_cap)) if current_market_cap > 0 else 1.0
        
        # Trading volume impact (higher volume = price discovery)
        volume_factor = 1 + (market_data['daily_volume_usd'] / market_data['liquidity_pool_usd'] * 0.1) if market_data['liquidity_pool_usd'] > 0 else 1.0
        volume_factor = min(1.5, max(0.8, volume_factor))
        
        # Calculate final price
        dynamic_price = base_price * liquidity_factor * supply_factor * market_cap_factor * volume_factor
        
        # Apply price bounds (prevent extreme volatility)
        min_price = self.base_price_usd * 0.1  # Never below 10% of base
        max_price = self.base_price_usd * 100  # Never above 100x base
        
        return max(min_price, min(max_price, dynamic_price))
    
    def get_market_data(self) -> Dict:
        """Get current market data for price calculation"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate daily volume
            cursor.execute("""
                SELECT COALESCE(SUM(net_amount), 0) 
                FROM guard_purchases 
                WHERE status = 'completed' 
                AND date(created_timestamp) = date('now')
            """)
            daily_volume = cursor.fetchone()[0] or 0
            
            # Calculate total tokens sold (affects circulating supply)
            cursor.execute("""
                SELECT COALESCE(SUM(guard_amount), 0) 
                FROM guard_purchases 
                WHERE status = 'completed'
            """)
            tokens_sold = cursor.fetchone()[0] or 0
            
            # Update circulating supply
            actual_circulating = 300_000_000 + tokens_sold
            
            # Calculate liquidity pool (starts at 50k, grows with volume)
            actual_liquidity = 50_000 + (daily_volume * 0.1)  # 10% of volume adds to liquidity
            
            conn.close()
            
            return {
                'daily_volume_usd': daily_volume,
                'total_tokens_sold': tokens_sold,
                'circulating_supply': actual_circulating,
                'liquidity_pool_usd': actual_liquidity,
                'market_cap_usd': actual_circulating * self.base_price_usd
            }
        except Exception as e:
            # Return default values if database doesn't exist yet
            return {
                'daily_volume_usd': 0,
                'total_tokens_sold': 0,
                'circulating_supply': 300_000_000,
                'liquidity_pool_usd': 50_000,
                'market_cap_usd': 300_000_000 * self.base_price_usd
            }
    
    def init_database(self):
        """Initialize purchase database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Purchases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guard_purchases (
                purchase_id TEXT PRIMARY KEY,
                guard_amount REAL NOT NULL,
                payment_amount REAL NOT NULL,
                payment_currency TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                customer_wallet TEXT NOT NULL,
                guard_price_usd REAL NOT NULL,
                exchange_rate REAL NOT NULL,
                status TEXT NOT NULL,
                created_timestamp TEXT NOT NULL,
                completed_timestamp TEXT,
                transaction_hash TEXT,
                promo_discount REAL DEFAULT 0,
                fees REAL DEFAULT 0,
                net_amount REAL NOT NULL
            )
        """)
        
        # User wallets and balances
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_wallets (
                wallet_address TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                guard_balance REAL DEFAULT 0,
                total_purchased REAL DEFAULT 0,
                total_spent REAL DEFAULT 0,
                created_timestamp TEXT NOT NULL,
                last_activity TEXT
            )
        """)
        
        # Payment methods
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_methods (
                method_id TEXT PRIMARY KEY,
                user_email TEXT NOT NULL,
                method_type TEXT NOT NULL,
                details TEXT NOT NULL,
                is_default INTEGER DEFAULT 0,
                created_timestamp TEXT NOT NULL
            )
        """)
        
        # Purchase analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_analytics (
                date TEXT PRIMARY KEY,
                total_purchases INTEGER DEFAULT 0,
                total_guard_sold REAL DEFAULT 0,
                total_revenue_usd REAL DEFAULT 0,
                avg_purchase_size REAL DEFAULT 0,
                top_payment_method TEXT,
                unique_buyers INTEGER DEFAULT 0
            )
        """)
        
        # Promo code usage
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promo_usage (
                usage_id TEXT PRIMARY KEY,
                promo_code TEXT NOT NULL,
                user_email TEXT NOT NULL,
                purchase_id TEXT NOT NULL,
                discount_amount REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def generate_purchase_id(self) -> str:
        """Generate unique purchase ID"""
        timestamp = datetime.now().isoformat()
        data = f"guard_purchase_{timestamp}_{random.randint(1000, 9999)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def calculate_purchase_amount(self, guard_amount: float, payment_currency: str, 
                                 promo_code: Optional[str] = None) -> Dict:
        """Calculate total purchase amount with fees and discounts"""
        
        # Base cost in USD
        base_cost_usd = guard_amount * self.guard_price_usd
        
        # Apply promo discount
        discount = 0.0
        if promo_code and promo_code in self.promo_codes:
            discount = self.promo_codes[promo_code]
        
        discounted_cost_usd = base_cost_usd * (1 - discount)
        
        # Calculate payment processing fees
        processing_fee = 0.0
        if payment_currency in self.fiat_rates:
            processing_fee = discounted_cost_usd * 0.029  # 2.9% for credit cards
        elif payment_currency in self.crypto_rates:
            processing_fee = discounted_cost_usd * 0.015  # 1.5% for crypto
        
        # Total cost in USD
        total_cost_usd = discounted_cost_usd + processing_fee
        
        # Convert to payment currency
        if payment_currency in self.fiat_rates:
            exchange_rate = self.fiat_rates[payment_currency]
            payment_amount = total_cost_usd * exchange_rate
        elif payment_currency in self.crypto_rates:
            exchange_rate = self.crypto_rates[payment_currency]
            payment_amount = total_cost_usd / exchange_rate
        else:
            exchange_rate = 1.0
            payment_amount = total_cost_usd
        
        return {
            'guard_amount': guard_amount,
            'base_cost_usd': base_cost_usd,
            'discount_amount': base_cost_usd * discount,
            'discounted_cost': discounted_cost_usd,
            'processing_fee': processing_fee,
            'total_cost_usd': total_cost_usd,
            'payment_amount': payment_amount,
            'payment_currency': payment_currency,
            'exchange_rate': exchange_rate,
            'promo_discount': discount
        }
    
    def create_purchase(self, request: GuardPurchaseRequest) -> GuardPurchase:
        """Create a new GUARD token purchase"""
        
        # Calculate purchase details
        calc = self.calculate_purchase_amount(
            request.guard_amount, 
            request.payment_currency,
            request.promo_code
        )
        
        # Create purchase record
        purchase = GuardPurchase(
            purchase_id=self.generate_purchase_id(),
            guard_amount=request.guard_amount,
            payment_amount=calc['payment_amount'],
            payment_currency=request.payment_currency,
            payment_method=request.payment_method,
            customer_email=request.customer_email,
            customer_wallet=request.customer_wallet,
            guard_price_usd=self.guard_price_usd,
            exchange_rate=calc['exchange_rate'],
            status=PurchaseStatus.PENDING,
            created_timestamp=datetime.now(),
            completed_timestamp=None,
            transaction_hash=None,
            promo_discount=calc['promo_discount'],
            fees=calc['processing_fee'],
            net_amount=calc['total_cost_usd']
        )
        
        # Save to database
        self.save_purchase(purchase)
        
        # Create/update user wallet
        self.create_or_update_wallet(request.customer_wallet, request.customer_email)
        
        return purchase
    
    def save_purchase(self, purchase: GuardPurchase):
        """Save purchase to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO guard_purchases VALUES 
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            purchase.purchase_id, purchase.guard_amount, purchase.payment_amount,
            purchase.payment_currency, purchase.payment_method.value,
            purchase.customer_email, purchase.customer_wallet,
            purchase.guard_price_usd, purchase.exchange_rate, purchase.status.value,
            purchase.created_timestamp.isoformat(),
            purchase.completed_timestamp.isoformat() if purchase.completed_timestamp else None,
            purchase.transaction_hash, purchase.promo_discount, purchase.fees,
            purchase.net_amount
        ))
        
        conn.commit()
        conn.close()
    
    def create_or_update_wallet(self, wallet_address: str, email: str):
        """Create or update user wallet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_wallets 
            (wallet_address, email, guard_balance, total_purchased, total_spent, created_timestamp, last_activity)
            VALUES (?, ?, 
                COALESCE((SELECT guard_balance FROM user_wallets WHERE wallet_address = ?), 0),
                COALESCE((SELECT total_purchased FROM user_wallets WHERE wallet_address = ?), 0),
                COALESCE((SELECT total_spent FROM user_wallets WHERE wallet_address = ?), 0),
                COALESCE((SELECT created_timestamp FROM user_wallets WHERE wallet_address = ?), ?),
                ?
            )
        """, (wallet_address, email, wallet_address, wallet_address, wallet_address,
              wallet_address, datetime.now().isoformat(), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def complete_purchase(self, purchase_id: str, transaction_hash: str = None):
        """Complete a purchase and deliver GUARD tokens"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get purchase details
        cursor.execute("SELECT * FROM guard_purchases WHERE purchase_id = ?", (purchase_id,))
        purchase_data = cursor.fetchone()
        
        if not purchase_data:
            raise ValueError("Purchase not found")
        
        # Update purchase status
        cursor.execute("""
            UPDATE guard_purchases 
            SET status = ?, completed_timestamp = ?, transaction_hash = ?
            WHERE purchase_id = ?
        """, (PurchaseStatus.COMPLETED.value, datetime.now().isoformat(), 
              transaction_hash or f"guard_tx_{purchase_id}", purchase_id))
        
        # Add GUARD tokens to user wallet
        guard_amount = purchase_data[1]  # guard_amount column
        wallet_address = purchase_data[6]  # customer_wallet column
        
        cursor.execute("""
            UPDATE user_wallets 
            SET guard_balance = guard_balance + ?,
                total_purchased = total_purchased + ?,
                last_activity = ?
            WHERE wallet_address = ?
        """, (guard_amount, guard_amount, datetime.now().isoformat(), wallet_address))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_purchase_history(self, email: str = None, wallet: str = None) -> List[Dict]:
        """Get purchase history for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if email:
            cursor.execute("""
                SELECT * FROM guard_purchases 
                WHERE customer_email = ? 
                ORDER BY created_timestamp DESC
            """, (email,))
        elif wallet:
            cursor.execute("""
                SELECT * FROM guard_purchases 
                WHERE customer_wallet = ? 
                ORDER BY created_timestamp DESC
            """, (wallet,))
        else:
            cursor.execute("""
                SELECT * FROM guard_purchases 
                ORDER BY created_timestamp DESC 
                LIMIT 50
            """)
        
        purchases = []
        for row in cursor.fetchall():
            purchase = {
                'purchase_id': row[0],
                'guard_amount': row[1],
                'payment_amount': row[2],
                'payment_currency': row[3],
                'payment_method': row[4],
                'customer_email': row[5],
                'customer_wallet': row[6],
                'guard_price_usd': row[7],
                'exchange_rate': row[8],
                'status': row[9],
                'created_timestamp': row[10],
                'completed_timestamp': row[11],
                'transaction_hash': row[12],
                'promo_discount': row[13],
                'fees': row[14],
                'net_amount': row[15]
            }
            purchases.append(purchase)
        
        conn.close()
        return purchases
    
    def get_wallet_balance(self, wallet_address: str) -> Dict:
        """Get wallet balance and stats"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT guard_balance, total_purchased, total_spent 
            FROM user_wallets 
            WHERE wallet_address = ?
        """, (wallet_address,))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'wallet_address': wallet_address,
                'guard_balance': result[0],
                'total_purchased': result[1],
                'total_spent': result[2]
            }
        
        conn.close()
        return {'wallet_address': wallet_address, 'guard_balance': 0, 'total_purchased': 0, 'total_spent': 0}
    
    def get_purchase_stats(self) -> Dict:
        """Get purchase statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total purchases
        cursor.execute("SELECT COUNT(*) FROM guard_purchases")
        total_purchases = cursor.fetchone()[0]
        
        # Total GUARD sold
        cursor.execute("SELECT SUM(guard_amount) FROM guard_purchases WHERE status = 'completed'")
        total_guard_sold = cursor.fetchone()[0] or 0
        
        # Total revenue
        cursor.execute("SELECT SUM(net_amount) FROM guard_purchases WHERE status = 'completed'")
        total_revenue = cursor.fetchone()[0] or 0
        
        # Average purchase size
        cursor.execute("SELECT AVG(guard_amount) FROM guard_purchases WHERE status = 'completed'")
        avg_purchase = cursor.fetchone()[0] or 0
        
        # Success rate
        cursor.execute("SELECT COUNT(*) FROM guard_purchases WHERE status = 'completed'")
        successful_purchases = cursor.fetchone()[0]
        success_rate = (successful_purchases / total_purchases * 100) if total_purchases > 0 else 0
        
        conn.close()
        
        return {
            'total_purchases': total_purchases,
            'successful_purchases': successful_purchases,
            'total_guard_sold': total_guard_sold,
            'total_revenue_usd': total_revenue,
            'average_purchase_size': avg_purchase,
            'success_rate': success_rate,
            'current_guard_price': self.guard_price_usd
        }

# Initialize FastAPI app and purchase manager
app = FastAPI(title="GuardianShield Token Purchase Platform", version="1.0.0")
purchase_manager = TokenPurchaseManager()

@app.get("/", response_class=HTMLResponse)
async def token_purchase_platform():
    """Serve the GUARD Token Purchase Platform"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Buy GUARD Tokens - GuardianShield</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #0a0e1a 0%, #1a2332 50%, #2d3e50 100%);
                color: #e0e6ed;
                min-height: 100vh;
                line-height: 1.6;
            }}
            
            .header {{
                background: linear-gradient(135deg, #2c3e50, #34495e);
                padding: 1.5rem 0;
                border-bottom: 3px solid #27ae60;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }}
            
            .header-content {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 2rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}
            
            .logo {{
                display: flex;
                align-items: center;
                gap: 1rem;
            }}
            
            .token-icon {{
                width: 50px;
                height: 50px;
                background: linear-gradient(45deg, #27ae60, #2ecc71);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.5rem;
                font-weight: bold;
                color: white;
                box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);
            }}
            
            .logo h1 {{
                color: #ecf0f1;
                font-size: 1.8rem;
                font-weight: 600;
            }}
            
            .price-ticker {{
                background: rgba(39, 174, 96, 0.2);
                padding: 0.8rem 1.5rem;
                border-radius: 25px;
                border: 1px solid #27ae60;
                text-align: center;
            }}
            
            .current-price {{
                font-size: 1.2rem;
                font-weight: bold;
                color: #27ae60;
            }}
            
            .main-content {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 3rem 2rem;
            }}
            
            .purchase-grid {{
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 3rem;
                margin-bottom: 3rem;
            }}
            
            .purchase-form {{
                background: linear-gradient(135deg, #1e3c72, #2a5298);
                padding: 2.5rem;
                border-radius: 20px;
                border: 2px solid #27ae60;
            }}
            
            .form-title {{
                color: #27ae60;
                font-size: 2rem;
                margin-bottom: 2rem;
                text-align: center;
                font-weight: 600;
            }}
            
            .form-group {{
                margin-bottom: 2rem;
            }}
            
            .form-label {{
                display: block;
                color: #ecf0f1;
                font-weight: 600;
                margin-bottom: 0.8rem;
                font-size: 1rem;
            }}
            
            .form-input, .form-select {{
                width: 100%;
                padding: 15px 20px;
                border: 2px solid #34495e;
                border-radius: 12px;
                background: rgba(52, 73, 94, 0.8);
                color: #ecf0f1;
                font-size: 1.1rem;
                transition: all 0.3s ease;
            }}
            
            .form-input:focus, .form-select:focus {{
                outline: none;
                border-color: #27ae60;
                box-shadow: 0 0 15px rgba(39, 174, 96, 0.3);
            }}
            
            .amount-selector {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 1rem;
                margin-top: 1rem;
            }}
            
            .amount-button {{
                padding: 1rem;
                background: rgba(39, 174, 96, 0.2);
                border: 1px solid #27ae60;
                border-radius: 10px;
                color: #27ae60;
                cursor: pointer;
                transition: all 0.3s ease;
                text-align: center;
                font-weight: 600;
            }}
            
            .amount-button:hover {{
                background: rgba(39, 174, 96, 0.4);
                transform: translateY(-2px);
            }}
            
            .amount-button.selected {{
                background: #27ae60;
                color: white;
                box-shadow: 0 4px 15px rgba(39, 174, 96, 0.4);
            }}
            
            .payment-methods {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 1rem;
                margin-top: 1rem;
            }}
            
            .payment-method {{
                padding: 1rem;
                background: rgba(52, 73, 94, 0.6);
                border: 1px solid #34495e;
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.3s ease;
                text-align: center;
            }}
            
            .payment-method:hover {{
                border-color: #27ae60;
                background: rgba(39, 174, 96, 0.1);
            }}
            
            .payment-method.selected {{
                border-color: #27ae60;
                background: rgba(39, 174, 96, 0.2);
                box-shadow: 0 0 15px rgba(39, 174, 96, 0.3);
            }}
            
            .promo-section {{
                background: rgba(155, 89, 182, 0.1);
                padding: 1.5rem;
                border-radius: 10px;
                border: 1px solid #9b59b6;
                margin-bottom: 2rem;
            }}
            
            .purchase-summary {{
                background: linear-gradient(135deg, #2c3e50, #34495e);
                padding: 2rem;
                border-radius: 20px;
                border: 2px solid #f39c12;
                height: fit-content;
            }}
            
            .summary-title {{
                color: #f39c12;
                font-size: 1.5rem;
                margin-bottom: 1.5rem;
                text-align: center;
                font-weight: 600;
            }}
            
            .summary-line {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 1rem;
                padding: 0.5rem 0;
                border-bottom: 1px solid rgba(244, 184, 228, 0.1);
            }}
            
            .summary-line.total {{
                border-top: 2px solid #f39c12;
                border-bottom: none;
                font-size: 1.2rem;
                font-weight: bold;
                color: #f39c12;
                margin-top: 1rem;
                padding-top: 1rem;
            }}
            
            .purchase-button {{
                width: 100%;
                padding: 18px;
                background: linear-gradient(45deg, #27ae60, #2ecc71);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 1.3rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-top: 2rem;
            }}
            
            .purchase-button:hover {{
                background: linear-gradient(45deg, #2ecc71, #58d68d);
                transform: translateY(-3px);
                box-shadow: 0 8px 25px rgba(39, 174, 96, 0.4);
            }}
            
            .purchase-button:disabled {{
                background: #7f8c8d;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }}
            
            .benefits-section {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 2rem;
                margin-top: 3rem;
            }}
            
            .benefit-card {{
                background: rgba(26, 35, 50, 0.8);
                padding: 2rem;
                border-radius: 15px;
                border: 1px solid rgba(39, 174, 96, 0.3);
                text-align: center;
            }}
            
            .benefit-icon {{
                font-size: 3rem;
                margin-bottom: 1rem;
            }}
            
            .benefit-title {{
                color: #27ae60;
                font-size: 1.3rem;
                font-weight: 600;
                margin-bottom: 1rem;
            }}
            
            .stats-section {{
                background: linear-gradient(135deg, rgba(26, 35, 50, 0.8), rgba(44, 62, 80, 0.6));
                padding: 2rem;
                border-radius: 15px;
                border: 1px solid rgba(39, 174, 96, 0.3);
                margin-bottom: 3rem;
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 2rem;
                text-align: center;
            }}
            
            .stat-item {{
                padding: 1rem;
            }}
            
            .stat-value {{
                font-size: 2rem;
                font-weight: bold;
                color: #27ae60;
                margin-bottom: 0.5rem;
            }}
            
            .stat-label {{
                color: #bdc3c7;
                font-size: 0.9rem;
            }}
            
            @media (max-width: 768px) {{
                .purchase-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .main-content {{
                    padding: 2rem 1rem;
                }}
                
                .amount-selector, .payment-methods {{
                    grid-template-columns: repeat(2, 1fr);
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="logo">
                    <div class="token-icon">🛡️</div>
                    <h1>Buy GUARD Tokens</h1>
                </div>
                <div class="price-ticker">
                    <div style="font-size: 0.9rem; color: #bdc3c7;">Current Price</div>
                    <div class="current-price">$0.85 USD</div>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="stats-section">
                <h2 style="color: #27ae60; text-align: center; margin-bottom: 2rem;">📊 Platform Statistics</h2>
                <div class="stats-grid" id="statsGrid">
                    <!-- Stats will be loaded here -->
                </div>
            </div>
            
            <div class="purchase-grid">
                <div class="purchase-form">
                    <h2 class="form-title">🚀 Purchase GUARD Tokens</h2>
                    
                    <form id="purchaseForm">
                        <div class="form-group">
                            <label class="form-label">How many GUARD tokens do you want?</label>
                            <input type="number" class="form-input" id="guardAmount" placeholder="Enter amount" step="1" min="1" required>
                            
                            <div class="amount-selector">
                                <div class="amount-button" data-amount="100">100 GUARD<br><small>$85</small></div>
                                <div class="amount-button" data-amount="500">500 GUARD<br><small>$425</small></div>
                                <div class="amount-button" data-amount="1000">1,000 GUARD<br><small>$850</small></div>
                                <div class="amount-button" data-amount="5000">5,000 GUARD<br><small>$4,250</small></div>
                                <div class="amount-button" data-amount="10000">10,000 GUARD<br><small>$8,500</small></div>
                                <div class="amount-button" data-amount="25000">25,000 GUARD<br><small>$21,250</small></div>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Payment Method</label>
                            <div class="payment-methods">
                                <div class="payment-method" data-method="credit_card">
                                    💳<br>Credit Card<br><small>2.9% fee</small>
                                </div>
                                <div class="payment-method" data-method="crypto">
                                    ₿<br>Cryptocurrency<br><small>1.5% fee</small>
                                </div>
                                <div class="payment-method" data-method="bank_transfer">
                                    🏦<br>Bank Transfer<br><small>1% fee</small>
                                </div>
                                <div class="payment-method" data-method="paypal">
                                    🅿️<br>PayPal<br><small>3.5% fee</small>
                                </div>
                                <div class="payment-method" data-method="apple_pay">
                                    🍎<br>Apple Pay<br><small>2.9% fee</small>
                                </div>
                                <div class="payment-method" data-method="google_pay">
                                    🔍<br>Google Pay<br><small>2.9% fee</small>
                                </div>
                            </div>
                            <input type="hidden" id="selectedPaymentMethod" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Payment Currency</label>
                            <select class="form-select" id="paymentCurrency" required>
                                <option value="">Select currency...</option>
                                <optgroup label="Fiat Currencies">
                                    <option value="USD">🇺🇸 US Dollar (USD)</option>
                                    <option value="EUR">🇪🇺 Euro (EUR)</option>
                                    <option value="GBP">🇬🇧 British Pound (GBP)</option>
                                    <option value="JPY">🇯🇵 Japanese Yen (JPY)</option>
                                    <option value="CAD">🇨🇦 Canadian Dollar (CAD)</option>
                                    <option value="AUD">🇦🇺 Australian Dollar (AUD)</option>
                                </optgroup>
                                <optgroup label="Cryptocurrencies">
                                    <option value="BTC">₿ Bitcoin (BTC)</option>
                                    <option value="ETH">Ξ Ethereum (ETH)</option>
                                    <option value="SOL">◎ Solana (SOL)</option>
                                    <option value="BNB">🔸 Binance Coin (BNB)</option>
                                    <option value="USDT">₮ Tether (USDT)</option>
                                    <option value="USDC">🔷 USD Coin (USDC)</option>
                                </optgroup>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Email Address</label>
                            <input type="email" class="form-input" id="customerEmail" placeholder="your@email.com" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Your Wallet Address</label>
                            <input type="text" class="form-input" id="walletAddress" placeholder="0x... or your wallet address" required>
                        </div>
                        
                        <div class="promo-section">
                            <label class="form-label">🎁 Promo Code (Optional)</label>
                            <input type="text" class="form-input" id="promoCode" placeholder="Enter promo code">
                            <div style="margin-top: 0.5rem; font-size: 0.9rem; color: #9b59b6;">
                                Available codes: LAUNCH25 (25% off), EARLY15 (15% off), SHIELD10 (10% off)
                            </div>
                        </div>
                        
                        <button type="submit" class="purchase-button" id="purchaseButton">
                            🛒 Purchase GUARD Tokens
                        </button>
                    </form>
                </div>
                
                <div class="purchase-summary">
                    <h3 class="summary-title">💰 Purchase Summary</h3>
                    
                    <div id="summaryContent">
                        <div style="text-align: center; color: #95a5a6; margin: 2rem 0;">
                            Select amount and payment method to see summary
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="benefits-section">
                <div class="benefit-card">
                    <div class="benefit-icon">🛡️</div>
                    <div class="benefit-title">SHIELD Token Minting</div>
                    <div>Pair GUARD with crypto to mint unique SHIELD tokens with high APY</div>
                </div>
                
                <div class="benefit-card">
                    <div class="benefit-icon">🎨</div>
                    <div class="benefit-title">NFT Marketplace</div>
                    <div>Create and trade NFTs using GUARD tokens in our marketplace</div>
                </div>
                
                <div class="benefit-card">
                    <div class="benefit-icon">💰</div>
                    <div class="benefit-title">Staking Rewards</div>
                    <div>Stake GUARD tokens to earn competitive APY and ecosystem rewards</div>
                </div>
                
                <div class="benefit-card">
                    <div class="benefit-icon">🌐</div>
                    <div class="benefit-title">Ecosystem Access</div>
                    <div>Use GUARD across the entire GuardianShield DeFi ecosystem</div>
                </div>
            </div>
        </div>
        
        <script>
            let selectedAmount = 0;
            let selectedPaymentMethod = '';
            let currentFees = {{}};
            
            // Amount selection
            document.querySelectorAll('.amount-button').forEach(button => {{
                button.addEventListener('click', function() {{
                    document.querySelectorAll('.amount-button').forEach(btn => btn.classList.remove('selected'));
                    this.classList.add('selected');
                    selectedAmount = parseInt(this.dataset.amount);
                    document.getElementById('guardAmount').value = selectedAmount;
                    updateSummary();
                }});
            }});
            
            // Payment method selection
            document.querySelectorAll('.payment-method').forEach(method => {{
                method.addEventListener('click', function() {{
                    document.querySelectorAll('.payment-method').forEach(m => m.classList.remove('selected'));
                    this.classList.add('selected');
                    selectedPaymentMethod = this.dataset.method;
                    document.getElementById('selectedPaymentMethod').value = selectedPaymentMethod;
                    updateSummary();
                }});
            }});
            
            // Form inputs
            ['guardAmount', 'paymentCurrency', 'promoCode'].forEach(id => {{
                document.getElementById(id).addEventListener('input', updateSummary);
            }});
            
            async function updateSummary() {{
                const amount = parseFloat(document.getElementById('guardAmount').value) || 0;
                const currency = document.getElementById('paymentCurrency').value;
                const promoCode = document.getElementById('promoCode').value;
                
                if (amount > 0 && currency && selectedPaymentMethod) {{
                    try {{
                        const response = await fetch('/api/purchase/calculate', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{
                                guard_amount: amount,
                                payment_currency: currency,
                                promo_code: promoCode || null
                            }})
                        }});
                        
                        const calc = await response.json();
                        
                        document.getElementById('summaryContent').innerHTML = `
                            <div class="summary-line">
                                <span>GUARD Tokens:</span>
                                <span>${{amount.toLocaleString()}} GUARD</span>
                            </div>
                            <div class="summary-line">
                                <span>Base Cost:</span>
                                <span>$${{calc.base_cost_usd.toFixed(2)}} USD</span>
                            </div>
                            ${{calc.discount_amount > 0 ? `
                                <div class="summary-line" style="color: #27ae60;">
                                    <span>Promo Discount:</span>
                                    <span>-$${{calc.discount_amount.toFixed(2)}}</span>
                                </div>
                            ` : ''}}
                            <div class="summary-line">
                                <span>Processing Fee:</span>
                                <span>$${{calc.processing_fee.toFixed(2)}}</span>
                            </div>
                            <div class="summary-line total">
                                <span>Total Cost:</span>
                                <span>${{calc.payment_amount.toFixed(4)}} ${{currency}}</span>
                            </div>
                            <div style="text-align: center; margin-top: 1rem; color: #bdc3c7; font-size: 0.9rem;">
                                ≈ $${{calc.total_cost_usd.toFixed(2)}} USD
                            </div>
                        `;
                    }} catch (error) {{
                        console.error('Error calculating purchase:', error);
                    }}
                }} else {{
                    document.getElementById('summaryContent').innerHTML = `
                        <div style="text-align: center; color: #95a5a6; margin: 2rem 0;">
                            Select amount and payment method to see summary
                        </div>
                    `;
                }}
            }}
            
            // Form submission
            document.getElementById('purchaseForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                
                if (!selectedPaymentMethod) {{
                    alert('Please select a payment method');
                    return;
                }}
                
                const formData = {{
                    guard_amount: parseFloat(document.getElementById('guardAmount').value),
                    payment_method: selectedPaymentMethod,
                    payment_currency: document.getElementById('paymentCurrency').value,
                    customer_email: document.getElementById('customerEmail').value,
                    customer_wallet: document.getElementById('walletAddress').value,
                    promo_code: document.getElementById('promoCode').value || null
                }};
                
                const button = document.getElementById('purchaseButton');
                button.disabled = true;
                button.textContent = '🔄 Processing Purchase...';
                
                try {{
                    const response = await fetch('/api/purchase/create', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(formData)
                    }});
                    
                    if (response.ok) {{
                        const result = await response.json();
                        alert(`Purchase created successfully!\\nPurchase ID: ${{result.purchase_id}}\\nYou will receive ${{result.guard_amount}} GUARD tokens once payment is confirmed.`);
                        
                        // Simulate payment completion for demo
                        setTimeout(async () => {{
                            await fetch(`/api/purchase/${{result.purchase_id}}/complete`, {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }}
                            }});
                            alert('Payment confirmed! GUARD tokens have been added to your wallet.');
                            loadStats();
                        }}, 3000);
                        
                        document.getElementById('purchaseForm').reset();
                        selectedAmount = 0;
                        selectedPaymentMethod = '';
                        document.querySelectorAll('.amount-button, .payment-method').forEach(btn => btn.classList.remove('selected'));
                        updateSummary();
                    }} else {{
                        const error = await response.json();
                        alert('Error creating purchase: ' + error.detail);
                    }}
                }} catch (error) {{
                    alert('Error creating purchase: ' + error.message);
                }} finally {{
                    button.disabled = false;
                    button.textContent = '🛒 Purchase GUARD Tokens';
                }}
            }});
            
            // Load stats
            async function loadStats() {{
                try {{
                    const response = await fetch('/api/purchase/stats');
                    const stats = await response.json();
                    
                    document.getElementById('statsGrid').innerHTML = `
                        <div class="stat-item">
                            <div class="stat-value">${{stats.total_purchases.toLocaleString()}}</div>
                            <div class="stat-label">Total Purchases</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${{Math.round(stats.total_guard_sold).toLocaleString()}}</div>
                            <div class="stat-label">GUARD Sold</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">$${{Math.round(stats.total_revenue_usd).toLocaleString()}}</div>
                            <div class="stat-label">Total Revenue</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${{stats.success_rate.toFixed(1)}}%</div>
                            <div class="stat-label">Success Rate</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${{Math.round(stats.average_purchase_size).toLocaleString()}}</div>
                            <div class="stat-label">Avg Purchase</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">$${{stats.current_guard_price}}</div>
                            <div class="stat-label">Current Price</div>
                        </div>
                    `;
                }} catch (error) {{
                    console.error('Error loading stats:', error);
                }}
            }}
            
            // Initialize
            loadStats();
            
            // Auto-refresh stats every 30 seconds
            setInterval(loadStats, 30000);
        </script>
    </body>
    </html>
    """

@app.post("/api/purchase/calculate")
async def calculate_purchase(request: dict):
    """Calculate purchase amount with fees and discounts"""
    try:
        calc = purchase_manager.calculate_purchase_amount(
            request.get('guard_amount'),
            request.get('payment_currency'),
            request.get('promo_code')
        )
        return calc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/purchase/create")
async def create_purchase(request: GuardPurchaseRequest):
    """Create a new GUARD token purchase"""
    try:
        purchase = purchase_manager.create_purchase(request)
        
        return {
            "success": True,
            "purchase_id": purchase.purchase_id,
            "guard_amount": purchase.guard_amount,
            "payment_amount": purchase.payment_amount,
            "payment_currency": purchase.payment_currency,
            "status": purchase.status.value,
            "created_at": purchase.created_timestamp.isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Purchase creation failed: {str(e)}")

@app.post("/api/purchase/{purchase_id}/complete")
async def complete_purchase(purchase_id: str):
    """Complete a purchase and deliver tokens"""
    try:
        result = purchase_manager.complete_purchase(purchase_id)
        return {"success": True, "message": "Purchase completed and tokens delivered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/purchase/history/{email}")
async def get_purchase_history(email: str):
    """Get purchase history for user"""
    try:
        history = purchase_manager.get_purchase_history(email=email)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/wallet/{wallet_address}")
async def get_wallet_balance(wallet_address: str):
    """Get wallet balance"""
    try:
        balance = purchase_manager.get_wallet_balance(wallet_address)
        return balance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/purchase/stats")
async def get_purchase_stats():
    """Get purchase platform statistics"""
    try:
        stats = purchase_manager.get_purchase_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🛡️ Starting GuardianShield GUARD Token Purchase Platform...")
    print("🚀 Platform available at: http://localhost:8010")
    print("📈 API documentation at: http://localhost:8010/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=8010,
        log_level="info"
    )