import re

def create_ultimate_deploy_script():
    # 1. Read Files
    try:
        with open('professional-landing.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        with open('frontend/js/token-sale.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
    except Exception as e:
        print(f"Error reading source files: {e}")
        return

    # 2. Fix Images (Replace local assets with placeholders to prevent 404s)
    # Pattern: src="assets/filename.png" -> src="https://placehold.co/..."
    def replace_image(match):
        filename = match.group(1)
        # Clean filename for URL
        text = filename.replace('.png', '').replace('.jpg', '').replace('-', ' ')
        return f'src="https://placehold.co/200x200/0f172a/00d4aa.png?text={text}"'

    html_content = re.sub(r'src="assets/([^"]+)"', replace_image, html_content)
    
    # 3. Inject JavaScript (Inline)
    # Find the script tag and replace it with inline code
    script_tag = '<script src="frontend/js/token-sale.js"></script>'
    inline_script = f'<script>\n{js_content}\n</script>'
    
    if script_tag in html_content:
        html_content = html_content.replace(script_tag, inline_script)
    else:
        # Fallback: Append before body end
        html_content = html_content.replace('</body>', f'{inline_script}</body>')

    # 4. Prepare Bash Script Content with SAFE Heredoc
    # We use a custom delimiter unlikely to be in the code
    HEREDOC_DELIM = "EXTREME_EOF_MARKER"
    
    script_content = f"""#!/bin/bash
# 🛡️ GuardianShield ULTIMATE Website Deployer
# ===========================================
# This script generates a SINGLE self-contained index.html file.
# - No broken images (auto-placeholders)
# - No missing JS files (embedded logic)
# - No 404 errors

echo "🚀 Deploying Clean GuardianShield Website..."

# 清除旧文件 (Clean old files)
rm -rf guardianshield_website
mkdir -p guardianshield_website

echo "📄 Generating Self-Contained Website..."
cat << '{HEREDOC_DELIM}' > guardianshield_website/index.html
{html_content}
{HEREDOC_DELIM}

echo "✅ Website Generated!"
echo "---------------------------------------------------"
echo "👉 STARTING SERVER ON PORT 8081..."
echo "---------------------------------------------------"

cd guardianshield_website
# Kill port 8081 if in use
fuser -k 8081/tcp > /dev/null 2>&1
# Start server
python3 -m http.server 8081 --bind 0.0.0.0
"""

    with open('DEPLOY_ULTIMATE_WEBSITE.sh', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("DEPLOY_ULTIMATE_WEBSITE.sh created successfully.")

if __name__ == "__main__":
    create_ultimate_deploy_script()
