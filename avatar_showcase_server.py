#!/usr/bin/env python3
"""
AI Avatar Showcase Server
Displays integrated AI avatars with animations
"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

def serve_avatars():
    """Serve the AI avatar showcase"""
    
    # Change to ai_avatars directory
    os.chdir("ai_avatars")
    
    PORT = 8090
    Handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("🎭 AI Avatar Showcase Server Started!")
        print(f"🌐 Master Gallery: http://localhost:{PORT}/master_gallery.html")
        print(f"🛡️ Ethereum Guardian: http://localhost:{PORT}/ethereum_guardian/showcase.html")
        print("\n📋 Available Showcases:")
        
        # List all available showcases
        for item in Path(".").iterdir():
            if item.is_dir():
                showcase_file = item / "showcase.html"
                if showcase_file.exists():
                    print(f"   • {item.name.title()}: http://localhost:{PORT}/{item.name}/showcase.html")
        
        print(f"\n🔗 Press Ctrl+C to stop server")
        
        # Auto-open the first showcase
        webbrowser.open(f"http://localhost:{PORT}/ethereum_guardian/showcase.html")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Avatar showcase server stopped!")

if __name__ == "__main__":
    serve_avatars()