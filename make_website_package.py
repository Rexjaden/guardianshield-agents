import os

def create_deploy_script():
    # Read the content of the files
    try:
        with open('professional-landing.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        with open('frontend/js/token-sale.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
            
    except Exception as e:
        print(f"Error reading source files: {e}")
        return

    # Escape single quotes for Bash heredoc
    # We use a pattern where we escape ' as '\'' inside a '...' block
    # But since we are putting this into a python string first, it's tricky.
    # Easiest way for Bash heredoc with EOF is to use "EOF" (quoted) to prevent variable expansion,
    # but we need to be careful about what characters are inside.
    # Actually, using python to write the file directly is safer if we were running python on target.
    # But user wants a script.
    
    # We will use the python script to generate the bash script content.
    
    script_content = f"""#!/bin/bash
# 🛡️ GuardianShield Start-Over Website Package
# ============================================
# This script creates a fresh 'guardianshield_website' folder
# and installs the working website + Web3 logic.

echo "🚀 Setting up GuardianShield Website..."

# 1. Create Directories
rm -rf guardianshield_website
mkdir -p guardianshield_website/frontend/js
mkdir -p guardianshield_website/assets

# 2. Install index.html
echo "📄 Installing index.html..."
cat << 'HTML_EOF' > guardianshield_website/index.html
{html_content}
HTML_EOF

# 3. Install Token Sale Logic
echo "🧠 Installing Web3 Logic..."
cat << 'JS_EOF' > guardianshield_website/frontend/js/token-sale.js
{js_content}
JS_EOF

# 4. Create a dummy image to prevent 404s if any
touch guardianshield_website/assets/logo.png

echo "✅ Website Package Installed!"
echo "---------------------------------------------------"
echo "👉 To preview your website:"
echo "   1. cd guardianshield_website"
echo "   2. python3 -m http.server 8081"
echo "   3. Click the 'Web Preview' button -> 'Change Port' -> 8081"
echo "---------------------------------------------------"
"""

    with open('DEPLOY_WEBSITE_PACKAGE.sh', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("DEPLOY_WEBSITE_PACKAGE.sh created successfully.")

if __name__ == "__main__":
    create_deploy_script()
