"""
GuardianShield Threat Filing API Server
REST API for accessing and managing the threat intelligence database
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
from pathlib import Path
import sys

# Add agents directory to path
sys.path.append(str(Path(__file__).parent / "agents"))

try:
    from agents.threat_filing_system import ThreatFilingSystem
    THREAT_FILING_AVAILABLE = True
except ImportError:
    THREAT_FILING_AVAILABLE = False
    print("Warning: ThreatFilingSystem not available")

app = FastAPI(
    title="GuardianShield Threat Filing API",
    description="REST API for managing threat intelligence database",
    version="1.0.0"
)

# Enable CORS for web interfaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize threat filing system
if THREAT_FILING_AVAILABLE:
    threat_filing = ThreatFilingSystem()
else:
    threat_filing = None

# Pydantic models for API requests
class MaliciousWebsite(BaseModel):
    domain: str
    threat_type: str
    severity: Optional[int] = 5
    description: Optional[str] = ""
    url: Optional[str] = None
    tags: Optional[List[str]] = []
    source: Optional[str] = "api"

class MaliciousIndividual(BaseModel):
    name: str
    threat_type: str
    severity: Optional[int] = 5
    description: Optional[str] = ""
    aliases: Optional[List[str]] = []
    wallet_addresses: Optional[List[str]] = []
    social_profiles: Optional[Dict[str, str]] = {}
    tags: Optional[List[str]] = []
    source: Optional[str] = "api"

class FraudulentIPO(BaseModel):
    company_name: str
    project_type: str
    threat_type: str
    severity: Optional[int] = 5
    description: Optional[str] = ""
    ticker_symbol: Optional[str] = None
    exchange: Optional[str] = None
    website: Optional[str] = None
    contract_address: Optional[str] = None
    tags: Optional[List[str]] = []
    source: Optional[str] = "api"

class ThreatUpdate(BaseModel):
    status: str

# Health check endpoint
@app.get("/", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "GuardianShield Threat Filing API",
        "version": "1.0.0",
        "threat_filing_available": THREAT_FILING_AVAILABLE
    }

# Statistics endpoint
@app.get("/api/stats", tags=["Statistics"])
async def get_statistics():
    """Get comprehensive threat database statistics"""
    if not threat_filing:
        raise HTTPException(status_code=503, detail="Threat filing system not available")
    
    try:
        stats = threat_filing.get_threat_statistics()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

# Search endpoints
@app.get("/api/search", tags=["Search"])
async def search_threats(
    query: str = Query(..., description="Search query"),
    categories: Optional[List[str]] = Query(None, description="Threat categories to search")
):
    """Search across all threat categories"""
    if not threat_filing:
        raise HTTPException(status_code=503, detail="Threat filing system not available")
    
    try:
        results = threat_filing.search_threats(query, categories)
        return {
            "success": True,
            "query": query,
            "categories": categories,
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching threats: {str(e)}")

# Website endpoints
@app.post("/api/websites", tags=["Websites"])
async def add_malicious_website(website: MaliciousWebsite):
    """Add a malicious website to the database"""
    if not threat_filing:
        raise HTTPException(status_code=503, detail="Threat filing system not available")
    
    try:
        website_id = threat_filing.add_malicious_website(
            domain=website.domain,
            threat_type=website.threat_type,
            severity=website.severity,
            description=website.description,
            url=website.url,
            tags=website.tags,
            source=website.source
        )
        return {
            "success": True,
            "message": f"Successfully added malicious website: {website.domain}",
            "id": website_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding website: {str(e)}")

@app.get("/api/websites/{website_id}", tags=["Websites"])
async def get_website(website_id: int):
    """Get specific website by ID"""
    if not threat_filing:
        raise HTTPException(status_code=503, detail="Threat filing system not available")
    
    try:
        website = threat_filing.get_threat_by_id("website", website_id)
        if not website:
            raise HTTPException(status_code=404, detail="Website not found")
        
        return {
            "success": True,
            "data": website
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting website: {str(e)}")

# Individual endpoints
@app.post("/api/individuals", tags=["Individuals"])
async def add_malicious_individual(individual: MaliciousIndividual):
    """Add a malicious individual to the database"""
    if not threat_filing:
        raise HTTPException(status_code=503, detail="Threat filing system not available")
    
    try:
        individual_id = threat_filing.add_malicious_individual(
            name=individual.name,
            threat_type=individual.threat_type,
            severity=individual.severity,
            description=individual.description,
            aliases=individual.aliases,
            wallet_addresses=individual.wallet_addresses,
            social_profiles=individual.social_profiles,
            tags=individual.tags,
            source=individual.source
        )
        return {
            "success": True,
            "message": f"Successfully added malicious individual: {individual.name}",
            "id": individual_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding individual: {str(e)}")

@app.get("/api/individuals/{individual_id}", tags=["Individuals"])
async def get_individual(individual_id: int):
    """Get specific individual by ID"""
    if not threat_filing:
        raise HTTPException(status_code=503, detail="Threat filing system not available")
    
    try:
        individual = threat_filing.get_threat_by_id("individual", individual_id)
        if not individual:
            raise HTTPException(status_code=404, detail="Individual not found")
        
        return {
            "success": True,
            "data": individual
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting individual: {str(e)}")

# IPO endpoints
@app.post("/api/ipos", tags=["IPOs"])
async def add_fraudulent_ipo(ipo: FraudulentIPO):
    """Add a fraudulent IPO to the database"""
    if not threat_filing:
        raise HTTPException(status_code=503, detail="Threat filing system not available")
    
    try:
        ipo_id = threat_filing.add_fraudulent_ipo(
            company_name=ipo.company_name,
            project_type=ipo.project_type,
            threat_type=ipo.threat_type,
            severity=ipo.severity,
            description=ipo.description,
            ticker_symbol=ipo.ticker_symbol,
            exchange=ipo.exchange,
            website=ipo.website,
            contract_address=ipo.contract_address,
            tags=ipo.tags,
            source=ipo.source
        )
        return {
            "success": True,
            "message": f"Successfully added fraudulent IPO: {ipo.company_name}",
            "id": ipo_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding IPO: {str(e)}")

@app.get("/api/ipos/{ipo_id}", tags=["IPOs"])
async def get_ipo(ipo_id: int):
    """Get specific IPO by ID"""
    if not threat_filing:
        raise HTTPException(status_code=503, detail="Threat filing system not available")
    
    try:
        ipo = threat_filing.get_threat_by_id("ipo", ipo_id)
        if not ipo:
            raise HTTPException(status_code=404, detail="IPO not found")
        
        return {
            "success": True,
            "data": ipo
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting IPO: {str(e)}")

# Status update endpoints
@app.put("/api/threats/{threat_type}/{threat_id}/status", tags=["Management"])
async def update_threat_status(threat_type: str, threat_id: int, update: ThreatUpdate):
    """Update threat status (active, resolved, monitoring, etc.)"""
    if not threat_filing:
        raise HTTPException(status_code=503, detail="Threat filing system not available")
    
    if threat_type not in ["website", "individual", "ipo"]:
        raise HTTPException(status_code=400, detail="Invalid threat type")
    
    try:
        success = threat_filing.update_threat_status(threat_type, threat_id, update.status)
        if not success:
            raise HTTPException(status_code=404, detail="Threat not found")
        
        return {
            "success": True,
            "message": f"Successfully updated {threat_type} {threat_id} status to {update.status}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating threat status: {str(e)}")

# Export endpoints
@app.get("/api/export", tags=["Export"])
async def export_threats(
    format_type: str = Query("json", description="Export format: json or csv"),
    threat_type: Optional[str] = Query(None, description="Threat type filter")
):
    """Export threat data in various formats"""
    if not threat_filing:
        raise HTTPException(status_code=503, detail="Threat filing system not available")
    
    if format_type not in ["json", "csv"]:
        raise HTTPException(status_code=400, detail="Invalid format type. Use 'json' or 'csv'")
    
    try:
        exported_data = threat_filing.export_threats(format_type, threat_type)
        return {
            "success": True,
            "format": format_type,
            "threat_type": threat_type,
            "data": exported_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting threats: {str(e)}")

# Bulk import endpoint
@app.post("/api/import", tags=["Import"])
async def bulk_import_threats(threat_data: List[Dict[str, Any]]):
    """Import multiple threats from external sources"""
    if not threat_filing:
        raise HTTPException(status_code=503, detail="Threat filing system not available")
    
    try:
        results = threat_filing.bulk_import_threats(threat_data)
        return {
            "success": True,
            "message": "Bulk import completed",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing threats: {str(e)}")

# Recent threats endpoints
@app.get("/api/recent/{threat_category}", tags=["Recent"])
async def get_recent_threats(
    threat_category: str,
    limit: int = Query(10, description="Number of recent threats to return")
):
    """Get recent threats by category"""
    if not threat_filing:
        raise HTTPException(status_code=503, detail="Threat filing system not available")
    
    if threat_category not in ["websites", "individuals", "ipos"]:
        raise HTTPException(status_code=400, detail="Invalid threat category")
    
    try:
        # Use search with empty query to get all recent threats
        results = threat_filing.search_threats("", [threat_category])
        recent_threats = results[threat_category][:limit]
        
        return {
            "success": True,
            "category": threat_category,
            "limit": limit,
            "data": recent_threats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recent threats: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting GuardianShield Threat Filing API Server...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🔍 Alternative Docs: http://localhost:8000/redoc")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )