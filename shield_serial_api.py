#!/usr/bin/env python3
"""
SHIELD Token Serial Number Web API
FastAPI integration for serial number management
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
from shield_token_serial_system import ShieldTokenSerial

app = FastAPI(title="SHIELD Token Serial API", version="1.0.0")
serial_system = ShieldTokenSerial()

class MintTokenRequest(BaseModel):
    wallet_address: str
    batch_id: Optional[str] = None
    metadata: Optional[Dict] = None

class VerifyTokenRequest(BaseModel):
    serial_number: str

class TransferTokenRequest(BaseModel):
    serial_number: str
    new_wallet_address: str
    transaction_hash: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "SHIELD Token Serial Number API", "version": "1.0.0"}

@app.post("/mint-token")
async def mint_token(request: MintTokenRequest):
    """Mint a new SHIELD token with serial number"""
    try:
        result = serial_system.mint_token_serial(
            request.wallet_address,
            request.batch_id,
            request.metadata
        )
        
        if result['success']:
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result['error'])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify-serial")
async def verify_serial(request: VerifyTokenRequest):
    """Verify a SHIELD token serial number"""
    try:
        result = serial_system.verify_serial_number(request.serial_number)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/token/{serial_number}")
async def get_token_info(serial_number: str):
    """Get token information by serial number"""
    try:
        token_info = serial_system.get_token_info(serial_number)
        if not token_info:
            raise HTTPException(status_code=404, detail="Token not found")
        return token_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/wallet/{wallet_address}/tokens")
async def get_wallet_tokens(wallet_address: str):
    """Get all tokens owned by a wallet"""
    try:
        tokens = serial_system.get_wallet_tokens(wallet_address)
        return {
            "wallet_address": wallet_address,
            "token_count": len(tokens),
            "tokens": tokens
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transfer-token")
async def transfer_token(request: TransferTokenRequest):
    """Transfer token to new wallet"""
    try:
        result = serial_system.transfer_token(
            request.serial_number,
            request.new_wallet_address,
            request.transaction_hash
        )
        
        if result['success']:
            return result
        else:
            raise HTTPException(status_code=400, detail=result['error'])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/statistics")
async def get_statistics():
    """Get token minting statistics"""
    try:
        stats = serial_system.get_serial_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/serial-checker", response_class=HTMLResponse)
async def serial_checker_page():
    """Serial number verification web interface"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SHIELD Token Serial Verification</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                min-height: 100vh;
                padding: 40px 20px;
            }
            
            .container {
                max-width: 600px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            
            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 10px;
                background: linear-gradient(135deg, #00d4aa, #fff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #00d4aa;
            }
            
            .form-group input {
                width: 100%;
                padding: 15px;
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.1);
                color: white;
                font-size: 1rem;
                font-family: monospace;
            }
            
            .form-group input:focus {
                outline: none;
                border-color: #00d4aa;
                box-shadow: 0 0 10px rgba(0, 212, 170, 0.3);
            }
            
            .verify-btn {
                width: 100%;
                padding: 15px;
                background: linear-gradient(135deg, #00d4aa, #007a5e);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .verify-btn:hover {
                background: linear-gradient(135deg, #007a5e, #00d4aa);
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(0, 212, 170, 0.3);
            }
            
            .result {
                margin-top: 30px;
                padding: 20px;
                border-radius: 10px;
                display: none;
            }
            
            .result.valid {
                background: rgba(0, 212, 170, 0.2);
                border: 2px solid #00d4aa;
            }
            
            .result.invalid {
                background: rgba(220, 38, 127, 0.2);
                border: 2px solid #dc267f;
            }
            
            .token-info {
                margin-top: 15px;
            }
            
            .token-info div {
                margin-bottom: 8px;
                padding: 8px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 5px;
            }
            
            .example {
                margin-top: 20px;
                text-align: center;
                color: rgba(255, 255, 255, 0.7);
                font-size: 0.9rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ SHIELD Token</h1>
                <p>Serial Number Verification</p>
            </div>
            
            <form id="verifyForm">
                <div class="form-group">
                    <label for="serialNumber">Serial Number:</label>
                    <input 
                        type="text" 
                        id="serialNumber" 
                        name="serialNumber" 
                        placeholder="GST-2026-B1234-123456-ABC"
                        required
                    />
                </div>
                
                <button type="submit" class="verify-btn">
                    🔍 Verify Serial Number
                </button>
            </form>
            
            <div id="result" class="result">
                <div id="resultMessage"></div>
                <div id="tokenInfo" class="token-info"></div>
            </div>
            
            <div class="example">
                <p>Example format: GST-2026-B1234-123456-ABC</p>
            </div>
        </div>
        
        <script>
            document.getElementById('verifyForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const serialNumber = document.getElementById('serialNumber').value;
                const resultDiv = document.getElementById('result');
                const messageDiv = document.getElementById('resultMessage');
                const infoDiv = document.getElementById('tokenInfo');
                
                if (!serialNumber) {
                    alert('Please enter a serial number');
                    return;
                }
                
                try {
                    const response = await fetch('/verify-serial', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ serial_number: serialNumber })
                    });
                    
                    const result = await response.json();
                    
                    resultDiv.style.display = 'block';
                    
                    if (result.valid) {
                        resultDiv.className = 'result valid';
                        messageDiv.innerHTML = '✅ Valid SHIELD Token';
                        
                        if (result.token_info) {
                            const info = result.token_info;
                            infoDiv.innerHTML = `
                                <div><strong>Token ID:</strong> ${info.token_id}</div>
                                <div><strong>Owner:</strong> ${info.wallet_address}</div>
                                <div><strong>Created:</strong> ${new Date(info.creation_date).toLocaleDateString()}</div>
                                <div><strong>Status:</strong> ${info.status}</div>
                            `;
                        }
                    } else {
                        resultDiv.className = 'result invalid';
                        messageDiv.innerHTML = `❌ Invalid Token: ${result.error}`;
                        infoDiv.innerHTML = '';
                    }
                    
                } catch (error) {
                    resultDiv.style.display = 'block';
                    resultDiv.className = 'result invalid';
                    messageDiv.innerHTML = `❌ Verification Error: ${error.message}`;
                    infoDiv.innerHTML = '';
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)