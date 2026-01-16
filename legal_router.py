"""
Legal Document Router for GuardianShield
Handles routing and serving of legal documents with proper headers and tracking
"""

from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
import markdown
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router and templates
router = APIRouter(prefix="/legal", tags=["legal"])
templates = Jinja2Templates(directory="legal")

# Legal document paths
LEGAL_DOCS_PATH = Path("legal")
LEGAL_DOCUMENTS = {
    "privacy-policy": "privacy-policy.md",
    "terms-of-service": "terms-of-service.md", 
    "ccpa-compliance": "ccpa-compliance.md",
    "security-policy": "security-policy.md",
    "data-retention-policy": "data-retention-policy.md"
}

class LegalDocumentManager:
    """Manages legal document serving and tracking"""
    
    def __init__(self):
        self.access_log = []
        
    def log_access(self, document: str, user_ip: str, user_agent: str = None):
        """Log legal document access for compliance"""
        access_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "document": document,
            "ip_address": user_ip,
            "user_agent": user_agent,
            "type": "legal_document_access"
        }
        self.access_log.append(access_record)
        logger.info(f"Legal document accessed: {document} from {user_ip}")
        
    def get_document_content(self, doc_name: str) -> str:
        """Get markdown content of legal document"""
        if doc_name not in LEGAL_DOCUMENTS:
            raise HTTPException(status_code=404, detail="Legal document not found")
            
        doc_path = LEGAL_DOCS_PATH / LEGAL_DOCUMENTS[doc_name]
        if not doc_path.exists():
            raise HTTPException(status_code=404, detail="Legal document file not found")
            
        with open(doc_path, 'r', encoding='utf-8') as file:
            return file.read()
            
    def render_document_html(self, content: str, title: str) -> str:
        """Convert markdown to HTML with legal document styling"""
        html_content = markdown.markdown(content, extensions=['toc', 'tables'])
        
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title} - GuardianShield</title>
            <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
            <style>
                .legal-content {{
                    line-height: 1.7;
                }}
                .legal-content h1 {{ @apply text-3xl font-bold text-gray-800 mb-6 border-b pb-4; }}
                .legal-content h2 {{ @apply text-2xl font-semibold text-gray-700 mt-8 mb-4; }}
                .legal-content h3 {{ @apply text-xl font-medium text-gray-600 mt-6 mb-3; }}
                .legal-content p {{ @apply mb-4 text-gray-700; }}
                .legal-content ul {{ @apply list-disc list-inside mb-4 ml-4; }}
                .legal-content li {{ @apply mb-2; }}
                .legal-content strong {{ @apply font-semibold text-gray-800; }}
                .legal-content code {{ @apply bg-gray-100 px-2 py-1 rounded text-sm; }}
                .legal-content blockquote {{ @apply border-l-4 border-blue-500 pl-4 italic text-gray-600; }}
            </style>
        </head>
        <body class="bg-gray-50">
            <!-- Navigation -->
            <nav class="bg-white shadow-sm border-b">
                <div class="container mx-auto px-6 py-4">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-4">
                            <a href="/" class="text-xl font-bold text-gray-800">🛡️ GuardianShield</a>
                            <span class="text-gray-500">></span>
                            <a href="/legal" class="text-blue-600 hover:text-blue-700">Legal</a>
                            <span class="text-gray-500">></span>
                            <span class="text-gray-700">{title}</span>
                        </div>
                        <div class="flex space-x-4">
                            <a href="/legal" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors">
                                Back to Legal Center
                            </a>
                        </div>
                    </div>
                </div>
            </nav>
            
            <!-- Content -->
            <div class="container mx-auto px-6 py-8">
                <div class="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-8">
                    <div class="legal-content">
                        {html_content}
                    </div>
                    
                    <!-- Document Actions -->
                    <div class="mt-12 pt-8 border-t border-gray-200">
                        <div class="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
                            <div>
                                <h4 class="text-lg font-semibold text-gray-800 mb-2">Need Help?</h4>
                                <p class="text-gray-600">Contact our legal team for questions about this policy.</p>
                            </div>
                            <div class="flex flex-col md:flex-row space-y-2 md:space-y-0 md:space-x-4">
                                <a href="mailto:legal@guardian-shield.io" class="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition-colors text-center">
                                    Email Legal Team
                                </a>
                                <button onclick="window.print()" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors">
                                    Print Document
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Footer -->
            <footer class="bg-gray-100 mt-12 py-6">
                <div class="container mx-auto px-6 text-center text-gray-600">
                    <p>Last Updated: January 14, 2026 | Effective Date: January 14, 2026</p>
                    <p class="text-sm mt-2">© 2026 GuardianShield. All rights reserved. US-Only Service.</p>
                </div>
            </footer>
            
            <script>
                // Track document viewing time for compliance
                let viewStartTime = Date.now();
                window.addEventListener('beforeunload', function() {{
                    let viewDuration = Date.now() - viewStartTime;
                    console.log('Legal document view duration:', viewDuration, 'ms');
                }});
            </script>
        </body>
        </html>
        """

# Initialize document manager
doc_manager = LegalDocumentManager()

@router.get("/", response_class=HTMLResponse)
async def legal_center(request: Request):
    """Serve legal center main page"""
    client_ip = request.client.host
    doc_manager.log_access("legal_center", client_ip, request.headers.get("user-agent"))
    
    with open(LEGAL_DOCS_PATH / "index.html", 'r', encoding='utf-8') as file:
        return HTMLResponse(content=file.read())

@router.get("/{document_name}", response_class=HTMLResponse)
async def serve_legal_document(document_name: str, request: Request):
    """Serve individual legal documents"""
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent")
    
    # Log access for compliance
    doc_manager.log_access(document_name, client_ip, user_agent)
    
    # Get document content
    try:
        content = doc_manager.get_document_content(document_name)
        title = document_name.replace("-", " ").title()
        
        # Render as HTML
        html_response = doc_manager.render_document_html(content, title)
        
        return HTMLResponse(
            content=html_response,
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Content-Security-Policy": "default-src 'self' cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; script-src 'self' 'unsafe-inline'",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "SAMEORIGIN"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving legal document {document_name}: {e}")
        raise HTTPException(status_code=500, detail="Error loading legal document")

@router.get("/{document_name}.pdf")
async def serve_legal_document_pdf(document_name: str, request: Request):
    """Serve PDF versions of legal documents (if available)"""
    client_ip = request.client.host
    doc_manager.log_access(f"{document_name}_pdf", client_ip, request.headers.get("user-agent"))
    
    # For now, return a message that PDF generation is available on request
    # In production, you might want to use a library like WeasyPrint to generate PDFs
    raise HTTPException(
        status_code=501, 
        detail="PDF generation available on request. Contact legal@guardian-shield.io"
    )

@router.get("/access/logs")
async def get_access_logs(request: Request):
    """Get legal document access logs (admin only)"""
    # This would typically require admin authentication
    # For demo purposes, returning recent access count
    recent_accesses = len([log for log in doc_manager.access_log 
                          if (datetime.utcnow() - datetime.fromisoformat(log["timestamp"])).days < 7])
    
    return {
        "total_accesses": len(doc_manager.access_log),
        "recent_accesses": recent_accesses,
        "last_updated": "2026-01-14T00:00:00Z"
    }

# Request handlers for specific legal actions
@router.get("/ccpa-request")
async def ccpa_request_form(request: Request):
    """CCPA data request form"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CCPA Data Request - GuardianShield</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-50">
        <div class="container mx-auto px-6 py-12">
            <div class="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-8">
                <h1 class="text-3xl font-bold text-gray-800 mb-6">California Privacy Rights Request</h1>
                <p class="text-gray-600 mb-8">California residents can exercise their CCPA rights using this form.</p>
                
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                    <h3 class="font-semibold text-blue-800 mb-2">Available Request Types:</h3>
                    <ul class="text-blue-700 space-y-1">
                        <li>• Right to Know: Request information about data we collect</li>
                        <li>• Right to Delete: Request deletion of your personal information</li>
                        <li>• Right to Correct: Request correction of inaccurate information</li>
                    </ul>
                </div>
                
                <div class="space-y-4">
                    <p class="text-gray-700">To submit a CCPA request:</p>
                    <div class="bg-gray-50 rounded-lg p-4">
                        <p><strong>Email:</strong> <a href="mailto:ccpa@guardian-shield.io" class="text-blue-600">ccpa@guardian-shield.io</a></p>
                        <p><strong>Phone:</strong> <a href="tel:+15551234567" class="text-blue-600">(555) 123-4567</a></p>
                        <p><strong>Response Time:</strong> 45 days (may extend to 90 days)</p>
                    </div>
                </div>
                
                <div class="mt-8">
                    <a href="/legal/ccpa-compliance" class="bg-blue-500 text-white px-6 py-3 rounded hover:bg-blue-600 transition-colors">
                        View Full CCPA Rights
                    </a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)

# Add router to main FastAPI app
# This would be included in your main api_server.py file:
"""
from legal_router import router as legal_router
app.include_router(legal_router)
"""