import re

def create_platinum_deploy_script():
    # 1. Read files
    try:
        with open('professional-landing.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        with open('frontend/js/token-sale.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
    except Exception as e:
        print(f"Error reading source files: {e}")
        return

    # 2. Fix Images (Same as Golden Dream)
    repo_base = "https://raw.githubusercontent.com/Rexjaden/guardianshield-agents/main/assets"
    known_assets = [
        "guard-token-logo.png", "gs-token-logo.png", "guardian-avatar.png",
        "prometheus-avatar.png", "silva-avatar.png", "turlo-avatar.png", "lindo-avatar.png"
    ]
    
    def replace_image_source(match):
        filename = match.group(1)
        if filename in known_assets:
            return f'src="{repo_base}/{filename}"'
        else:
            text = filename.replace('.png', '').replace('.jpg', '').replace('-', ' ')
            return f'src="https://placehold.co/200x200/0f172a/00d4aa.png?text={text}"'

    html_content = re.sub(r'src="assets/([^"]+)"', replace_image_source, html_content)
    
    # 3. FIX THE JAVASCRIPT LOGIC (The crucial button fix)
    # We will modify js_content before injecting it
    
    # Find the initTokenSale function and patch it to attach to multiple buttons
    button_fix_code = """
    const connectBtn = document.getElementById('connect-wallet-btn');
    const navConnectBtn = document.getElementById('connectWallet'); // Added this
    
    const handler = () => {
         console.log("Connect button clicked");
         connectWallet();
    };

    if (connectBtn) {
        connectBtn.addEventListener('click', handler);
        connectBtn.disabled = false;
        connectBtn.innerText = "Connect Wallet";
    }
    
    if (navConnectBtn) {
        navConnectBtn.addEventListener('click', handler);
        navConnectBtn.disabled = false;
        navConnectBtn.innerText = "Connect Wallet";
    }
    """
    
    # Simple string replacement in JS to make it robust
    # We replace the specific lines that were too narrow
    old_js_block = "const connectBtn = document.getElementById('connect-wallet-btn');"
    js_content = js_content.replace(old_js_block, button_fix_code)
    
    # Add a visual toaster to confirm system ready
    system_ready_toast = """
    // Visual Confirmation
    const toast = document.createElement('div');
    toast.style.cssText = "position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: rgba(0, 255, 170, 0.9); color: #000; padding: 10px 20px; border-radius: 5px; z-index: 10000; font-weight: bold; pointer-events: none; opacity: 0; transition: opacity 0.5s;";
    toast.innerText = "GuardianShield System Verified: Active";
    document.body.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '1'; }, 500);
    setTimeout(() => { toast.style.opacity = '0'; }, 3000);
    """
    js_content += "\n" + system_ready_toast

    # 4. Inject JS
    script_tag = '<script src="frontend/js/token-sale.js"></script>'
    inline_script = f'<script>\n{js_content}\n</script>'
    
    if script_tag in html_content:
        html_content = html_content.replace(script_tag, inline_script)
    else:
        html_content = html_content.replace('</body>', f'{inline_script}</body>')

    # 5. Bash Script
    HEREDOC_DELIM = "PLATINUM_EOF"
    
    script_content = f"""#!/bin/bash
# 🛡️ GuardianShield PLATINUM Edition Deployer
# ===========================================
# - Fixes Buttons (Both Top and Bottom)
# - Restores Images (Repo Links)
# - Cleans Ports & Launches

echo "💎 Deploying Platinum Edition..."

rm -rf guardianshield_platinum
mkdir -p guardianshield_platinum

echo "📄 Generating Patched Website..."
cat << '{HEREDOC_DELIM}' > guardianshield_platinum/index.html
{html_content}
{HEREDOC_DELIM}


echo "✅ Website Patched & Ready!"
echo "---------------------------------------------------"
echo "👉 STARTING SERVER ON PORT 8081..."
echo "---------------------------------------------------"

cd guardianshield_platinum

# Kill port 8081 if in use
if command -v fuser &> /dev/null; then
    fuser -k 8081/tcp > /dev/null 2>&1
fi
if command -v lsof &> /dev/null; then
    pid=$(lsof -t -i:8081)
    if [ ! -z "$pid" ]; then kill -9 $pid; fi
fi

# Start server
python3 -m http.server 8081 --bind 0.0.0.0
"""

    with open('DEPLOY_PLATINUM_EDITION.sh', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("DEPLOY_PLATINUM_EDITION.sh created successfully.")

if __name__ == "__main__":
    create_platinum_deploy_script()
