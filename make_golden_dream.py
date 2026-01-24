import re

def create_golden_deploy_script():
    # 1. Read Files
    try:
        with open('professional-landing.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        with open('frontend/js/token-sale.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
    except Exception as e:
        print(f"Error reading source files: {e}")
        return

    # 2. THE GOLDEN FIX: Link directly to the Repo Images
    # This bypasses all local file path issues.
    repo_base = "https://raw.githubusercontent.com/Rexjaden/guardianshield-agents/main/assets"
    
    # Map specific assets we know exist
    known_assets = [
        "guard-token-logo.png",
        "gs-token-logo.png",
        "guardian-avatar.png",
        "prometheus-avatar.png",
        "silva-avatar.png",
        "turlo-avatar.png",
        "lindo-avatar.png"
    ]
    
    # Function to replace src="assets/..." with Raw GitHub URL
    def replace_image_source(match):
        full_match = match.group(0) # src="assets/filename.png"
        filename = match.group(1)   # filename.png
        
        if filename in known_assets:
            return f'src="{repo_base}/{filename}"'
        else:
            # Fallback for unknown assets (still use placeholder to prevent broke UI)
            text = filename.replace('.png', '').replace('.jpg', '').replace('-', ' ')
            return f'src="https://placehold.co/200x200/0f172a/00d4aa.png?text={text}"'

    # Regex to find src="assets/..."
    html_content = re.sub(r'src="assets/([^"]+)"', replace_image_source, html_content)
    
    # 3. Inject JavaScript (Inline)
    script_tag = '<script src="frontend/js/token-sale.js"></script>'
    inline_script = f'<script>\n{js_content}\n</script>'
    
    if script_tag in html_content:
        html_content = html_content.replace(script_tag, inline_script)
    else:
        html_content = html_content.replace('</body>', f'{inline_script}</body>')

    # 4. Create the Bash Script
    HEREDOC_DELIM = "GOLDEN_DREAM_EOF"
    
    script_content = f"""#!/bin/bash
# 🛡️ GuardianShield GOLDEN DREAM Deployer
# ========================================
# Restores the website with:
# 1. Working Token Logic
# 2. REAL Logos and Avatars (linked to repo)
# 3. Port 8081 Auto-Launch

echo "✨ Restoring the Golden Dream..."

# Clean workspace
rm -rf guardianshield_golden
mkdir -p guardianshield_golden

echo "📄 Generating Website with Restored Assets..."
cat << '{HEREDOC_DELIM}' > guardianshield_golden/index.html
{html_content}
{HEREDOC_DELIM}

echo "✅ Website Restored!"
echo "---------------------------------------------------"
echo "👉 STARTING SERVER ON PORT 8081..."
echo "---------------------------------------------------"

cd guardianshield_golden

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

    with open('DEPLOY_GOLDEN_DREAM.sh', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("DEPLOY_GOLDEN_DREAM.sh created successfully.")

if __name__ == "__main__":
    create_golden_deploy_script()
