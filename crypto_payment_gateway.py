#!/usr/bin/env python3
"""
GuardianShield Crypto Payment Gateway
Multi-cryptocurrency payment processing with automatic GUARD conversion
"""

import uvicorn
import sqlite3
import hashlib
import json
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
from decimal import Decimal

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Supported Cryptocurrencies
class SupportedCrypto(str, Enum):
    BTC = "bitcoin"
    ETH = "ethereum"
    SOL = "solana"
    BNB = "binancecoin"
    ADA = "cardano"
    USDT = "tether"
    USDC = "usd-coin"
    GUARD = "guardianshield"

# Payment Status
class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"

# Pydantic Models
class PaymentRequest(BaseModel):
    amount: float
    currency: SupportedCrypto
    customer_email: str
    customer_address: str
    description: str
    auto_convert_to_guard: bool = True
    webhook_url: Optional[str] = None
    expiry_minutes: int = 30

class PaymentWebhook(BaseModel):
    payment_id: str
    status: PaymentStatus
    transaction_hash: Optional[str]
    timestamp: str

@dataclass
class CryptoPayment:
    payment_id: str
    amount: float
    currency: SupportedCrypto
    guard_equivalent: float
    customer_email: str
    customer_address: str
    payment_address: str
    description: str
    status: PaymentStatus
    created_timestamp: datetime
    expires_timestamp: datetime
    completed_timestamp: Optional[datetime]
    transaction_hash: Optional[str]
    webhook_url: Optional[str]
    auto_convert_to_guard: bool
    conversion_rate: float
    network_fee: float

class CryptoPrice:
    """Real-time cryptocurrency price fetcher"""
    
    @staticmethod
    def get_prices() -> Dict[str, float]:
        """Get current crypto prices in USD"""
        try:
            # Fallback prices (in production, use real API like CoinGecko)
            prices = {
                'bitcoin': 45000.0,
                'ethereum': 3200.0,
                'solana': 85.0,
                'binancecoin': 320.0,
                'cardano': 0.65,
                'tether': 1.0,
                'usd-coin': 1.0,
                'guardianshield': 0.85
            }
            
            # In production, replace with real API call:
            # response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin,cardano,tether,usd-coin&vs_currencies=usd')
            # if response.status_code == 200:
            #     prices.update(response.json())
            
            return prices
        except Exception:
            # Fallback prices
            return {
                'bitcoin': 45000.0,
                'ethereum': 3200.0,
                'solana': 85.0,
                'binancecoin': 320.0,
                'cardano': 0.65,
                'tether': 1.0,
                'usd-coin': 1.0,
                'guardianshield': 0.85
            }

class PaymentGateway:
    """Manages cryptocurrency payments and conversions"""
    
    def __init__(self, db_path: str = "payment_gateway.db"):
        self.db_path = db_path
        self.init_database()
        self.crypto_prices = CryptoPrice()
    
    def init_database(self):
        """Initialize payment database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Payments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                guard_equivalent REAL NOT NULL,
                customer_email TEXT NOT NULL,
                customer_address TEXT NOT NULL,
                payment_address TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                created_timestamp TEXT NOT NULL,
                expires_timestamp TEXT NOT NULL,
                completed_timestamp TEXT,
                transaction_hash TEXT,
                webhook_url TEXT,
                auto_convert_to_guard INTEGER DEFAULT 1,
                conversion_rate REAL NOT NULL,
                network_fee REAL DEFAULT 0
            )
        """)
        
        # Conversion history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversions (
                conversion_id TEXT PRIMARY KEY,
                payment_id TEXT NOT NULL,
                from_currency TEXT NOT NULL,
                to_currency TEXT NOT NULL,
                from_amount REAL NOT NULL,
                to_amount REAL NOT NULL,
                exchange_rate REAL NOT NULL,
                fee_amount REAL DEFAULT 0,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (payment_id) REFERENCES payments (payment_id)
            )
        """)
        
        # Wallet addresses (for receiving payments)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallet_addresses (
                currency TEXT PRIMARY KEY,
                address TEXT NOT NULL,
                private_key_encrypted TEXT,
                created_timestamp TEXT NOT NULL,
                last_used_timestamp TEXT
            )
        """)
        
        # Payment analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_analytics (
                date TEXT PRIMARY KEY,
                total_payments INTEGER DEFAULT 0,
                total_volume_usd REAL DEFAULT 0,
                successful_payments INTEGER DEFAULT 0,
                failed_payments INTEGER DEFAULT 0,
                top_currency TEXT,
                avg_payment_amount REAL DEFAULT 0
            )
        """)
        
        # Initialize wallet addresses (demo addresses)
        cursor.execute("""
            INSERT OR REPLACE INTO wallet_addresses VALUES 
            ('bitcoin', '1GuardianShieldBTCAddress123456789', 'encrypted_key_btc', ?, ?),
            ('ethereum', '0xGuardianShieldETHAddress123456789abcdef', 'encrypted_key_eth', ?, ?),
            ('solana', 'GuardianShieldSOLAddress123456789abcdefghij', 'encrypted_key_sol', ?, ?),
            ('binancecoin', '0xGuardianShieldBNBAddress123456789abcdef', 'encrypted_key_bnb', ?, ?),
            ('cardano', 'addr1GuardianShieldADAAddress123456789abcdef', 'encrypted_key_ada', ?, ?)
        """, tuple([datetime.now().isoformat(), None] * 5))
        
        conn.commit()
        conn.close()
    
    def generate_payment_id(self) -> str:
        """Generate unique payment ID"""
        timestamp = datetime.now().isoformat()
        data = f"payment_{timestamp}_{hash(timestamp)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def get_payment_address(self, currency: SupportedCrypto) -> str:
        """Get wallet address for receiving payments"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT address FROM wallet_addresses WHERE currency = ?", (currency.value,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return result[0]
        else:
            # Generate new address for unknown currency
            return f"GuardianShield{currency.value.upper()}Address123456789"
    
    def calculate_guard_equivalent(self, amount: float, currency: SupportedCrypto) -> tuple[float, float]:
        """Calculate GUARD token equivalent and conversion rate"""
        prices = self.crypto_prices.get_prices()
        
        crypto_price_usd = prices.get(currency.value, 1.0)
        guard_price_usd = prices.get('guardianshield', 0.85)
        
        # Calculate USD value
        usd_value = amount * crypto_price_usd
        
        # Calculate GUARD equivalent
        guard_equivalent = usd_value / guard_price_usd
        
        # Conversion rate (crypto to GUARD)
        conversion_rate = guard_equivalent / amount if amount > 0 else 0
        
        return guard_equivalent, conversion_rate
    
    def create_payment(self, request: PaymentRequest) -> CryptoPayment:
        """Create a new crypto payment"""
        payment_id = self.generate_payment_id()
        payment_address = self.get_payment_address(request.currency)
        
        # Calculate GUARD equivalent
        guard_equivalent, conversion_rate = self.calculate_guard_equivalent(
            request.amount, request.currency
        )
        
        # Calculate network fee (1% of transaction)
        network_fee = request.amount * 0.01
        
        # Create payment object
        payment = CryptoPayment(
            payment_id=payment_id,
            amount=request.amount,
            currency=request.currency,
            guard_equivalent=guard_equivalent,
            customer_email=request.customer_email,
            customer_address=request.customer_address,
            payment_address=payment_address,
            description=request.description,
            status=PaymentStatus.PENDING,
            created_timestamp=datetime.now(),
            expires_timestamp=datetime.now() + timedelta(minutes=request.expiry_minutes),
            completed_timestamp=None,
            transaction_hash=None,
            webhook_url=request.webhook_url,
            auto_convert_to_guard=request.auto_convert_to_guard,
            conversion_rate=conversion_rate,
            network_fee=network_fee
        )
        
        # Save to database
        self.save_payment(payment)
        
        return payment
    
    def save_payment(self, payment: CryptoPayment):
        """Save payment to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO payments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            payment.payment_id, payment.amount, payment.currency.value,
            payment.guard_equivalent, payment.customer_email, payment.customer_address,
            payment.payment_address, payment.description, payment.status.value,
            payment.created_timestamp.isoformat(), payment.expires_timestamp.isoformat(),
            payment.completed_timestamp.isoformat() if payment.completed_timestamp else None,
            payment.transaction_hash, payment.webhook_url,
            int(payment.auto_convert_to_guard), payment.conversion_rate, payment.network_fee
        ))
        
        conn.commit()
        conn.close()
    
    def get_payment(self, payment_id: str) -> Optional[Dict]:
        """Get payment by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
        row = cursor.fetchone()
        
        if row:
            payment = {
                'payment_id': row[0],
                'amount': row[1],
                'currency': row[2],
                'guard_equivalent': row[3],
                'customer_email': row[4],
                'customer_address': row[5],
                'payment_address': row[6],
                'description': row[7],
                'status': row[8],
                'created_timestamp': row[9],
                'expires_timestamp': row[10],
                'completed_timestamp': row[11],
                'transaction_hash': row[12],
                'webhook_url': row[13],
                'auto_convert_to_guard': bool(row[14]),
                'conversion_rate': row[15],
                'network_fee': row[16]
            }
            conn.close()
            return payment
        
        conn.close()
        return None
    
    def get_all_payments(self) -> List[Dict]:
        """Get all payments"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM payments ORDER BY created_timestamp DESC")
        
        payments = []
        for row in cursor.fetchall():
            payment = {
                'payment_id': row[0],
                'amount': row[1],
                'currency': row[2],
                'guard_equivalent': row[3],
                'customer_email': row[4],
                'customer_address': row[5],
                'payment_address': row[6],
                'description': row[7],
                'status': row[8],
                'created_timestamp': row[9],
                'expires_timestamp': row[10],
                'completed_timestamp': row[11],
                'transaction_hash': row[12],
                'webhook_url': row[13],
                'auto_convert_to_guard': bool(row[14]),
                'conversion_rate': row[15],
                'network_fee': row[16]
            }
            payments.append(payment)
        
        conn.close()
        return payments
    
    def confirm_payment(self, payment_id: str, transaction_hash: str):
        """Confirm payment completion"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE payments 
            SET status = ?, completed_timestamp = ?, transaction_hash = ?
            WHERE payment_id = ?
        """, (PaymentStatus.COMPLETED.value, datetime.now().isoformat(), transaction_hash, payment_id))
        
        conn.commit()
        conn.close()
    
    def get_payment_stats(self) -> Dict:
        """Get payment gateway statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total payments
        cursor.execute("SELECT COUNT(*) FROM payments")
        total_payments = cursor.fetchone()[0]
        
        # Successful payments
        cursor.execute("SELECT COUNT(*) FROM payments WHERE status = 'completed'")
        successful_payments = cursor.fetchone()[0]
        
        # Total volume in USD
        cursor.execute("""
            SELECT SUM(amount * conversion_rate * 0.85) 
            FROM payments 
            WHERE status = 'completed'
        """)
        total_volume = cursor.fetchone()[0] or 0
        
        # Success rate
        success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
        
        # Top currency
        cursor.execute("""
            SELECT currency, COUNT(*) as count 
            FROM payments 
            GROUP BY currency 
            ORDER BY count DESC 
            LIMIT 1
        """)
        top_currency_result = cursor.fetchone()
        top_currency = top_currency_result[0] if top_currency_result else "N/A"
        
        conn.close()
        
        return {
            'total_payments': total_payments,
            'successful_payments': successful_payments,
            'total_volume_usd': total_volume,
            'success_rate': success_rate,
            'top_currency': top_currency
        }

# Initialize FastAPI app and payment gateway
app = FastAPI(title="GuardianShield Payment Gateway", version="2.0.0")
payment_gateway = PaymentGateway()

@app.get("/", response_class=HTMLResponse)
async def payment_gateway_interface():
    """Serve the Payment Gateway interface"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GuardianShield Payment Gateway</title>
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
                border-bottom: 3px solid #f39c12;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }}
            
            .header-content {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 2rem;
                display: flex;
                align-items: center;
                gap: 1rem;
            }}
            
            .logo {{
                display: flex;
                align-items: center;
                gap: 1rem;
            }}
            
            .payment-icon {{
                width: 50px;
                height: 50px;
                background: linear-gradient(45deg, #f39c12, #e67e22);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.5rem;
                font-weight: bold;
                color: white;
                box-shadow: 0 4px 15px rgba(243, 156, 18, 0.3);
            }}
            
            .logo h1 {{
                color: #ecf0f1;
                font-size: 1.8rem;
                font-weight: 600;
            }}
            
            .main-content {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 3rem 2rem;
            }}
            
            .gateway-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 3rem;
                margin-bottom: 3rem;
            }}
            
            .gateway-section {{
                background: linear-gradient(135deg, #1e3c72, #2a5298);
                padding: 2rem;
                border-radius: 15px;
                border: 2px solid #f39c12;
            }}
            
            .section-title {{
                color: #f39c12;
                font-size: 1.5rem;
                margin-bottom: 1.5rem;
                text-align: center;
                font-weight: 600;
            }}
            
            .form-group {{
                margin-bottom: 1.5rem;
            }}
            
            .form-label {{
                display: block;
                color: #ecf0f1;
                font-weight: 600;
                margin-bottom: 0.5rem;
                font-size: 0.9rem;
            }}
            
            .form-input, .form-select {{
                width: 100%;
                padding: 12px 15px;
                border: 1px solid #34495e;
                border-radius: 8px;
                background: rgba(52, 73, 94, 0.8);
                color: #ecf0f1;
                font-size: 1rem;
            }}
            
            .form-input:focus, .form-select:focus {{
                outline: none;
                border-color: #f39c12;
                box-shadow: 0 0 10px rgba(243, 156, 18, 0.3);
            }}
            
            .crypto-selector {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 0.5rem;
                margin-top: 0.5rem;
            }}
            
            .crypto-option {{
                padding: 0.8rem;
                border: 1px solid #34495e;
                border-radius: 6px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 0.85rem;
                background: rgba(52, 73, 94, 0.6);
            }}
            
            .crypto-option:hover {{
                border-color: #f39c12;
                background: rgba(243, 156, 18, 0.1);
            }}
            
            .crypto-option.selected {{
                border-color: #f39c12;
                background: rgba(243, 156, 18, 0.3);
                box-shadow: 0 0 15px rgba(243, 156, 18, 0.5);
            }}
            
            .create-payment-button {{
                width: 100%;
                padding: 15px;
                background: linear-gradient(45deg, #f39c12, #e67e22);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-top: 1rem;
            }}
            
            .create-payment-button:hover {{
                background: linear-gradient(45deg, #e67e22, #d35400);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(243, 156, 18, 0.4);
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1.5rem;
                margin-bottom: 2rem;
            }}
            
            .stat-card {{
                background: rgba(26, 35, 50, 0.6);
                padding: 1.5rem;
                border-radius: 10px;
                text-align: center;
                border: 1px solid rgba(243, 156, 18, 0.3);
            }}
            
            .stat-value {{
                font-size: 2rem;
                font-weight: bold;
                color: #f39c12;
                margin-bottom: 0.5rem;
            }}
            
            .stat-label {{
                color: #bdc3c7;
                font-size: 0.9rem;
            }}
            
            .payments-section {{
                background: linear-gradient(135deg, #2c3e50, #34495e);
                padding: 2rem;
                border-radius: 15px;
                border: 2px solid #27ae60;
            }}
            
            .payments-grid {{
                display: grid;
                gap: 1rem;
                margin-top: 2rem;
            }}
            
            .payment-card {{
                background: rgba(26, 35, 50, 0.8);
                border-radius: 10px;
                padding: 1.5rem;
                border: 1px solid rgba(39, 174, 96, 0.3);
                transition: all 0.3s ease;
            }}
            
            .payment-card:hover {{
                border-color: #27ae60;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(39, 174, 96, 0.3);
            }}
            
            .payment-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1rem;
            }}
            
            .payment-id {{
                font-weight: 600;
                color: #27ae60;
            }}
            
            .payment-status {{
                padding: 0.3rem 0.8rem;
                border-radius: 15px;
                font-size: 0.8rem;
                font-weight: 600;
            }}
            
            .status-pending {{ background: #f39c12; color: white; }}
            .status-completed {{ background: #27ae60; color: white; }}
            .status-failed {{ background: #e74c3c; color: white; }}
            
            .payment-details {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
            }}
            
            .payment-amount {{
                font-size: 1.2rem;
                font-weight: bold;
                color: #ecf0f1;
            }}
            
            .guard-equivalent {{
                color: #f39c12;
                font-weight: 600;
            }}
            
            @media (max-width: 768px) {{
                .gateway-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .main-content {{
                    padding: 2rem 1rem;
                }}
                
                .crypto-selector {{
                    grid-template-columns: repeat(2, 1fr);
                }}
                
                .stats-grid {{
                    grid-template-columns: repeat(2, 1fr);
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="logo">
                    <div class="payment-icon">💳</div>
                    <h1>Crypto Payment Gateway</h1>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="gateway-grid">
                <div class="gateway-section">
                    <h2 class="section-title">🚀 Create Payment</h2>
                    
                    <form id="paymentForm">
                        <div class="form-group">
                            <label class="form-label">Payment Amount</label>
                            <input type="number" class="form-input" id="paymentAmount" placeholder="Enter amount" step="0.001" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Cryptocurrency</label>
                            <div class="crypto-selector">
                                <div class="crypto-option" data-crypto="bitcoin">
                                    ₿ BTC
                                </div>
                                <div class="crypto-option" data-crypto="ethereum">
                                    Ξ ETH
                                </div>
                                <div class="crypto-option" data-crypto="solana">
                                    ◎ SOL
                                </div>
                                <div class="crypto-option" data-crypto="binancecoin">
                                    🔸 BNB
                                </div>
                                <div class="crypto-option" data-crypto="cardano">
                                    ₳ ADA
                                </div>
                                <div class="crypto-option" data-crypto="tether">
                                    ₮ USDT
                                </div>
                                <div class="crypto-option" data-crypto="usd-coin">
                                    🔷 USDC
                                </div>
                                <div class="crypto-option" data-crypto="guardianshield">
                                    🛡️ GUARD
                                </div>
                            </div>
                            <input type="hidden" id="selectedCrypto" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Customer Email</label>
                            <input type="email" class="form-input" id="customerEmail" placeholder="customer@example.com" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Customer Wallet Address</label>
                            <input type="text" class="form-input" id="customerAddress" placeholder="Customer's wallet address" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Description</label>
                            <input type="text" class="form-input" id="paymentDescription" placeholder="Payment description" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">
                                <input type="checkbox" id="autoConvert" checked> 
                                Auto-convert to GUARD tokens
                            </label>
                        </div>
                        
                        <div class="form-group" id="conversionPreview" style="display: none;">
                            <div style="background: rgba(39, 174, 96, 0.2); padding: 1rem; border-radius: 8px;">
                                <div style="color: #27ae60; font-weight: 600;">Conversion Preview:</div>
                                <div id="guardEquivalent">0 GUARD tokens</div>
                                <div style="font-size: 0.9rem; color: #bdc3c7;" id="conversionRate">Rate: 1 BTC = 0 GUARD</div>
                            </div>
                        </div>
                        
                        <button type="submit" class="create-payment-button" id="createPaymentButton">
                            💳 Create Payment
                        </button>
                    </form>
                </div>
                
                <div class="gateway-section">
                    <h2 class="section-title">📊 Gateway Statistics</h2>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value" id="totalPayments">-</div>
                            <div class="stat-label">Total Payments</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="successfulPayments">-</div>
                            <div class="stat-label">Successful</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="totalVolume">-</div>
                            <div class="stat-label">Volume (USD)</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="successRate">-</div>
                            <div class="stat-label">Success Rate</div>
                        </div>
                    </div>
                    
                    <div style="margin-top: 2rem;">
                        <h3 style="color: #f39c12; margin-bottom: 1rem;">💱 Current Exchange Rates</h3>
                        <div id="exchangeRates" style="background: rgba(52, 73, 94, 0.6); padding: 1rem; border-radius: 8px;">
                            Loading rates...
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="payments-section">
                <h2 class="section-title">📋 Recent Payments</h2>
                <div class="payments-grid" id="paymentsGrid">
                    <!-- Payments will be loaded here -->
                </div>
            </div>
        </div>
        
        <script>
            let selectedCrypto = null;
            let currentRates = {{}};
            
            // Crypto selection
            document.querySelectorAll('.crypto-option').forEach(option => {{
                option.addEventListener('click', function() {{
                    document.querySelectorAll('.crypto-option').forEach(opt => opt.classList.remove('selected'));
                    this.classList.add('selected');
                    selectedCrypto = this.dataset.crypto;
                    document.getElementById('selectedCrypto').value = selectedCrypto;
                    updateConversionPreview();
                }});
            }});
            
            // Amount input
            document.getElementById('paymentAmount').addEventListener('input', updateConversionPreview);
            
            function updateConversionPreview() {{
                const amount = parseFloat(document.getElementById('paymentAmount').value) || 0;
                
                if (amount > 0 && selectedCrypto) {{
                    // Calculate GUARD equivalent
                    const cryptoPrice = currentRates[selectedCrypto] || 1;
                    const guardPrice = currentRates['guardianshield'] || 0.85;
                    const usdValue = amount * cryptoPrice;
                    const guardEquivalent = usdValue / guardPrice;
                    const conversionRate = guardEquivalent / amount;
                    
                    document.getElementById('conversionPreview').style.display = 'block';
                    document.getElementById('guardEquivalent').textContent = guardEquivalent.toFixed(2) + ' GUARD tokens';
                    document.getElementById('conversionRate').textContent = `Rate: 1 ${{selectedCrypto.toUpperCase()}} = ${{conversionRate.toFixed(4)}} GUARD`;
                }} else {{
                    document.getElementById('conversionPreview').style.display = 'none';
                }}
            }}
            
            // Form submission
            document.getElementById('paymentForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                
                if (!selectedCrypto) {{
                    alert('Please select a cryptocurrency');
                    return;
                }}
                
                const requestData = {{
                    amount: parseFloat(document.getElementById('paymentAmount').value),
                    currency: selectedCrypto,
                    customer_email: document.getElementById('customerEmail').value,
                    customer_address: document.getElementById('customerAddress').value,
                    description: document.getElementById('paymentDescription').value,
                    auto_convert_to_guard: document.getElementById('autoConvert').checked
                }};
                
                const button = document.getElementById('createPaymentButton');
                button.disabled = true;
                button.textContent = '🔄 Creating Payment...';
                
                try {{
                    const response = await fetch('/api/payment/create', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(requestData)
                    }});
                    
                    if (response.ok) {{
                        const result = await response.json();
                        alert(`Payment created successfully!\\nPayment ID: ${{result.payment_id}}\\nSend ${{result.amount}} ${{result.currency.toUpperCase()}} to: ${{result.payment_address}}`);
                        document.getElementById('paymentForm').reset();
                        selectedCrypto = null;
                        document.querySelectorAll('.crypto-option').forEach(opt => opt.classList.remove('selected'));
                        document.getElementById('conversionPreview').style.display = 'none';
                        loadPayments();
                        loadStats();
                    }} else {{
                        const error = await response.json();
                        alert('Error creating payment: ' + error.detail);
                    }}
                }} catch (error) {{
                    alert('Error creating payment: ' + error.message);
                }} finally {{
                    button.disabled = false;
                    button.textContent = '💳 Create Payment';
                }}
            }});
            
            // Load exchange rates
            async function loadExchangeRates() {{
                try {{
                    const response = await fetch('/api/payment/rates');
                    const rates = await response.json();
                    currentRates = rates;
                    
                    const ratesHTML = Object.entries(rates).map(([currency, price]) => {{
                        const symbol = currency === 'bitcoin' ? '₿' : 
                                     currency === 'ethereum' ? 'Ξ' :
                                     currency === 'solana' ? '◎' :
                                     currency === 'guardianshield' ? '🛡️' : '💱';
                        return `<div style="display: flex; justify-content: space-between; margin: 0.5rem 0;">
                            <span>${{symbol}} ${{currency.toUpperCase()}}</span>
                            <span style="color: #f39c12;">${{price.toLocaleString()}} USD</span>
                        </div>`;
                    }}).join('');
                    
                    document.getElementById('exchangeRates').innerHTML = ratesHTML;
                }} catch (error) {{
                    console.error('Error loading rates:', error);
                }}
            }}
            
            // Load payments
            async function loadPayments() {{
                try {{
                    const response = await fetch('/api/payment/all');
                    const payments = await response.json();
                    
                    const grid = document.getElementById('paymentsGrid');
                    grid.innerHTML = payments.slice(0, 10).map(payment => `
                        <div class="payment-card">
                            <div class="payment-header">
                                <div class="payment-id">${{payment.payment_id}}</div>
                                <div class="payment-status status-${{payment.status}}">${{payment.status.toUpperCase()}}</div>
                            </div>
                            <div class="payment-details">
                                <div>
                                    <div class="payment-amount">${{payment.amount}} ${{payment.currency.toUpperCase()}}</div>
                                    <div style="font-size: 0.9rem; color: #bdc3c7;">${{payment.customer_email}}</div>
                                </div>
                                <div>
                                    <div class="guard-equivalent">${{payment.guard_equivalent.toFixed(2)}} GUARD</div>
                                    <div style="font-size: 0.9rem; color: #bdc3c7;">${{new Date(payment.created_timestamp).toLocaleDateString()}}</div>
                                </div>
                            </div>
                            <div style="margin-top: 1rem; font-size: 0.9rem; color: #95a5a6;">
                                ${{payment.description}}
                            </div>
                        </div>
                    `).join('');
                }} catch (error) {{
                    console.error('Error loading payments:', error);
                }}
            }}
            
            // Load statistics
            async function loadStats() {{
                try {{
                    const response = await fetch('/api/payment/stats');
                    const stats = await response.json();
                    
                    document.getElementById('totalPayments').textContent = stats.total_payments;
                    document.getElementById('successfulPayments').textContent = stats.successful_payments;
                    document.getElementById('totalVolume').textContent = '$' + stats.total_volume_usd.toLocaleString();
                    document.getElementById('successRate').textContent = stats.success_rate.toFixed(1) + '%';
                }} catch (error) {{
                    console.error('Error loading stats:', error);
                }}
            }}
            
            // Initialize
            loadExchangeRates();
            loadPayments();
            loadStats();
            
            // Auto-refresh every 30 seconds
            setInterval(() => {{
                loadExchangeRates();
                loadPayments();
                loadStats();
            }}, 30000);
        </script>
    </body>
    </html>
    """

@app.post("/api/payment/create")
async def create_payment(request: PaymentRequest):
    """Create a new crypto payment"""
    try:
        payment = payment_gateway.create_payment(request)
        
        return {
            "success": True,
            "payment_id": payment.payment_id,
            "amount": payment.amount,
            "currency": payment.currency.value,
            "guard_equivalent": payment.guard_equivalent,
            "payment_address": payment.payment_address,
            "expires_at": payment.expires_timestamp.isoformat(),
            "conversion_rate": payment.conversion_rate
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment creation failed: {str(e)}")

@app.get("/api/payment/{payment_id}")
async def get_payment(payment_id: str):
    """Get payment by ID"""
    try:
        payment = payment_gateway.get_payment(payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        return payment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/payment/all")
async def get_all_payments():
    """Get all payments"""
    try:
        payments = payment_gateway.get_all_payments()
        return payments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/payment/{payment_id}/confirm")
async def confirm_payment(payment_id: str, transaction_hash: str):
    """Confirm payment completion"""
    try:
        payment_gateway.confirm_payment(payment_id, transaction_hash)
        return {"success": True, "message": "Payment confirmed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/payment/rates")
async def get_exchange_rates():
    """Get current cryptocurrency exchange rates"""
    try:
        prices = payment_gateway.crypto_prices.get_prices()
        return prices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/payment/stats")
async def get_payment_stats():
    """Get payment gateway statistics"""
    try:
        stats = payment_gateway.get_payment_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("💳 Starting GuardianShield Crypto Payment Gateway...")
    print("🚀 Gateway available at: http://localhost:8008")
    print("📈 API documentation at: http://localhost:8008/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=8008,
        log_level="info"
    )