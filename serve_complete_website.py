#!/usr/bin/env python3
"""
Complete Guardian Website Server
Showcase all 5 AI guardians with full animations
"""

import http.server
import socketserver
import webbrowser
import os

def serve_complete_website():
    """Serve the complete guardian website"""
    
    PORT = 8095
    Handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("🛡️ GuardianShield Complete Website Launched!")
        print(f"🌐 Complete Guardian Collective: http://localhost:{PORT}/complete_guardian_website.html")
        print(f"🎭 Individual Showcases: http://localhost:{PORT}/ai_avatars/")
        print(f"🗺️ Interactive Roadmap: http://localhost:{PORT}/GuardianShield_Roadmap_Interactive.html")
        
        print("\n🎮 Features:")
        print("   ⚡ Ethereum Guardian - Lightning & Ethereal Energy")
        print("   🌿 Forest Guardian - Mystical Nature & Ancient Wisdom")
        print("   👼 Divine Messenger - Angelic Wings & Sacred Fire")
        print("   🔥 Fire Guardian - Volcanic Power & Thermal Mastery")
        print("   ⚔️ Shadow Sentinel - Dark Armor & Stealth Operations")
        
        print("\n🚀 Interactive Elements:")
        print("   • Cosmic background with starfield")
        print("   • Unique animations for each guardian")
        print("   • Hover effects and click interactions")
        print("   • Master deployment controls")
        print("   • Keyboard shortcuts (Alt+1-5 for guardians, Alt+A for all)")
        
        print(f"\n🔗 Press Ctrl+C to stop server")
        
        # Auto-open the complete website
        webbrowser.open(f"http://localhost:{PORT}/complete_guardian_website.html")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Guardian website server stopped!")

if __name__ == "__main__":
    serve_complete_website()