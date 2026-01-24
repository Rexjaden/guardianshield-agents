import re

def create_diamond_deploy_script():
    # 1. Read the SOURCE files
    # We are going to use the 'web3-integration.js' logic if possible, OR fix 'token-sale.js' perfectly.
    # The user implies 'token-sale.js' is the one used in the HTML.
    # Let's stick to 'token-sale.js' but patch it aggressively.
    
    try:
        with open('professional-landing.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        with open('frontend/js/token-sale.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
    except Exception as e:
        print(f"Error reading source files: {e}")
        return

    # 2. IMAGE FIX (Golden Logic)
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

    # 3. UNIVERSAL BUTTON FIX
    # Note: connectWallet function needs to be globally accessible
    
    universal_fix = """
    // --- DIAMOND FIX START ---
    function attachUniversalListeners() {
        console.log("💎 Applying universal button fix...");
        const connectors = document.querySelectorAll('#connectWallet, #connect-wallet-btn, .connect-wallet-btn');
        console.log("Found connect buttons:", connectors.length);
        
        connectors.forEach(btn => {
            // Remove old listeners by cloning
            const newBtn = btn.cloneNode(true);
            if(btn.parentNode) {
                btn.parentNode.replaceChild(newBtn, btn);
            }
            
            // Attach new listener
            newBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log("Connect clicked!");
                if (typeof connectWallet === 'function') {
                    connectWallet(); 
                } else {
                    alert("Wallet logic loading... please wait.");
                    // Retry
                    if (window.initTokenSale) initTokenSale();
                }
            });
            
            // Visual feedback
            newBtn.style.border = "2px solid #00ff00";
            newBtn.setAttribute('title', 'Active (Diamond Fix)');
        });
        
        // Also fix Buy Button
        const buyBtn = document.getElementById('buy-tokens-btn');
        if (buyBtn) {
            const newBuy = buyBtn.cloneNode(true);
            buyBtn.parentNode.replaceChild(newBuy, buyBtn);
            newBuy.addEventListener('click', (e) => {
                 e.preventDefault();
                 if (typeof buyTokens === 'function') buyTokens();
            });
        }
    }

    // Run this after a short delay to ensure DOM is settled
    setTimeout(attachUniversalListeners, 1000);
    setTimeout(attachUniversalListeners, 3000);
    // --- DIAMOND FIX END ---
    """
    
    # Append the fix to the proper init function
    # We find the end of initTokenSale and append the call
    # Actually, easiest is just to append the whole block at the end of the script
    js_content += "\n" + universal_fix

    # 4. Inject
    script_tag = '<script src="frontend/js/token-sale.js"></script>'
    inline_script = f'<script>\n{js_content}\n</script>'
    
    if script_tag in html_content:
        html_content = html_content.replace(script_tag, inline_script)
    else:
        html_content = html_content.replace('</body>', f'{inline_script}</body>')

    # 5. Output Script
    HEREDOC_DELIM = "DIAMOND_EOF"
    
    script_content = f"""#!/bin/bash
# 🛡️ GuardianShield DIAMOND Edition Deployer
# ==========================================
# - Universal Button Fix (Finds ALL buttons by ID/Class)
# - Restores Images from GitHub Info
# - Auto-Launch

echo "💎 Deploying DIAMOND Edition..."

rm -rf guardianshield_diamond
mkdir -p guardianshield_diamond

echo "📄 Generating Diamond Website..."
cat << '{HEREDOC_DELIM}' > guardianshield_diamond/index.html
{html_content}
{HEREDOC_DELIM}

echo "✅ Website Generated!"
echo "---------------------------------------------------"
echo "👉 STARTING SERVER ON PORT 8081..."
echo "---------------------------------------------------"

cd guardianshield_diamond

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

    with open('DEPLOY_DIAMOND_EDITION.sh', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("DEPLOY_DIAMOND_EDITION.sh created successfully.")

if __name__ == "__main__":
    create_diamond_deploy_script()
