"""
GitHub Repository Security Manager
Protects your GuardianShield repository from unauthorized access
"""

import os
import json
import subprocess
import requests
from datetime import datetime
from typing import Dict, List, Optional

class GitHubRepositorySecurityManager:
    def __init__(self):
        self.repo_path = os.getcwd()
        self.config_file = "github_security_config.json"
        self.load_config()
    
    def load_config(self):
        """Load GitHub security configuration"""
        default_config = {
            "owner": "",
            "repo": "",
            "protected_branches": ["main", "master", "production"],
            "required_reviews": 2,
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": True,
            "required_status_checks": [],
            "enforce_admins": True,
            "allow_force_pushes": False,
            "allow_deletions": False,
            "restrict_pushes": True,
            "restrictions": {
                "users": [],
                "teams": [],
                "apps": []
            },
            "secret_scanning": True,
            "dependency_scanning": True,
            "code_scanning": True,
            "private_vulnerability_reporting": True
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = default_config
        else:
            self.config = default_config
    
    def save_config(self):
        """Save GitHub security configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_github_token(self) -> Optional[str]:
        """Get GitHub token from environment"""
        token = os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
        if not token:
            print("⚠️ GitHub token not found in environment variables")
            print("Set GITHUB_TOKEN or GH_TOKEN for API access")
        return token
    
    def detect_repository_info(self) -> Dict:
        """Detect GitHub repository information"""
        try:
            # Try to get remote origin
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True, text=True, cwd=self.repo_path
            )
            
            if result.returncode == 0:
                origin_url = result.stdout.strip()
                
                # Parse GitHub URL
                if 'github.com' in origin_url:
                    if origin_url.startswith('https://'):
                        # https://github.com/owner/repo.git
                        parts = origin_url.replace('https://github.com/', '').replace('.git', '').split('/')
                    elif origin_url.startswith('git@'):
                        # git@github.com:owner/repo.git
                        parts = origin_url.replace('git@github.com:', '').replace('.git', '').split('/')
                    else:
                        return {"error": "Unable to parse GitHub URL format"}
                    
                    if len(parts) >= 2:
                        owner, repo = parts[0], parts[1]
                        self.config['owner'] = owner
                        self.config['repo'] = repo
                        self.save_config()
                        
                        return {
                            "owner": owner,
                            "repo": repo,
                            "url": f"https://github.com/{owner}/{repo}",
                            "detected": True
                        }
            
            return {"error": "No GitHub repository detected"}
        
        except Exception as e:
            return {"error": f"Failed to detect repository: {e}"}
    
    def setup_branch_protection(self, branch: str = "main") -> Dict:
        """Setup branch protection rules"""
        token = self.get_github_token()
        if not token:
            return {"error": "GitHub token required"}
        
        if not self.config['owner'] or not self.config['repo']:
            repo_info = self.detect_repository_info()
            if "error" in repo_info:
                return repo_info
        
        owner = self.config['owner']
        repo = self.config['repo']
        
        protection_rules = {
            "required_status_checks": {
                "strict": True,
                "contexts": self.config['required_status_checks']
            },
            "enforce_admins": self.config['enforce_admins'],
            "required_pull_request_reviews": {
                "required_approving_review_count": self.config['required_reviews'],
                "dismiss_stale_reviews": self.config['dismiss_stale_reviews'],
                "require_code_owner_reviews": self.config['require_code_owner_reviews']
            },
            "restrictions": self.config['restrictions'] if self.config['restrict_pushes'] else None,
            "allow_force_pushes": self.config['allow_force_pushes'],
            "allow_deletions": self.config['allow_deletions']
        }
        
        url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}/protection"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            response = requests.put(url, json=protection_rules, headers=headers)
            
            if response.status_code == 200:
                return {"success": f"Branch protection enabled for {branch}"}
            else:
                return {"error": f"API call failed: {response.status_code} - {response.text}"}
        
        except Exception as e:
            return {"error": f"Failed to setup branch protection: {e}"}
    
    def enable_security_features(self) -> Dict:
        """Enable GitHub security features"""
        token = self.get_github_token()
        if not token:
            return {"error": "GitHub token required"}
        
        if not self.config['owner'] or not self.config['repo']:
            repo_info = self.detect_repository_info()
            if "error" in repo_info:
                return repo_info
        
        owner = self.config['owner']
        repo = self.config['repo']
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        results = []
        
        # Enable secret scanning
        if self.config['secret_scanning']:
            url = f"https://api.github.com/repos/{owner}/{repo}/secret-scanning/alerts"
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    results.append("✅ Secret scanning: Already enabled")
                else:
                    results.append("⚠️ Secret scanning: Check repository settings")
            except:
                results.append("❌ Secret scanning: API error")
        
        # Enable dependency scanning (Dependabot)
        if self.config['dependency_scanning']:
            dependabot_config = """
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "daily"
    reviewers:
      - "{owner}"
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "daily"
    reviewers:
      - "{owner}"
""".format(owner=owner)
            
            results.append("💡 Create .github/dependabot.yml with dependency scanning config")
        
        return {"results": results}
    
    def scan_repository_secrets(self) -> Dict:
        """Scan repository for potential secrets"""
        print("🔍 Scanning repository for potential secrets...")
        
        dangerous_patterns = [
            r'(?i)(password|passwd|pwd|secret|key|token|api)["\s]*[:=]["\s]*[a-zA-Z0-9+/=]{8,}',
            r'(?i)(github|gh)[_-]?(token|key)["\s]*[:=]["\s]*[a-zA-Z0-9]{20,}',
            r'(?i)(aws|amazon)[_-]?(access|secret)[_-]?(key|id)["\s]*[:=]["\s]*[a-zA-Z0-9+/=]{16,}',
            r'(?i)(database|db)[_-]?(url|connection|conn)["\s]*[:=]["\s]*[^\s"\']{10,}',
            r'(?i)(smtp|email)[_-]?(password|pass|pwd)["\s]*[:=]["\s]*[^\s"\']{6,}',
            r'(?i)(private[_-]?key|ssh[_-]?key)["\s]*[:=]',
            r'-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----',
        ]
        
        suspicious_files = []
        ignore_patterns = ['.git/', '__pycache__/', '.env.example', '.env.template']
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                if file.startswith('.') and file not in ['.env', '.env.local']:
                    continue
                
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, self.repo_path)
                
                # Skip files matching ignore patterns
                if any(pattern in relative_path for pattern in ignore_patterns):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Check for dangerous patterns
                        import re
                        for pattern in dangerous_patterns:
                            matches = re.finditer(pattern, content)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                suspicious_files.append({
                                    'file': relative_path,
                                    'line': line_num,
                                    'pattern': 'Potential secret detected',
                                    'context': match.group()[:50] + '...' if len(match.group()) > 50 else match.group()
                                })
                
                except Exception:
                    continue
        
        return {
            'suspicious_files': suspicious_files,
            'total_found': len(suspicious_files),
            'recommendations': [
                "Review each detected potential secret",
                "Move secrets to environment variables",
                "Add sensitive files to .gitignore",
                "Consider using secret management tools",
                "Rotate any exposed secrets immediately"
            ]
        }
    
    def create_security_workflow(self) -> str:
        """Create GitHub Actions security workflow"""
        workflow_dir = ".github/workflows"
        os.makedirs(workflow_dir, exist_ok=True)
        
        security_workflow = """
name: Security Scanning

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'

jobs:
  security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 0
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: 'trivy-results.sarif'
    
    - name: Run GitLeaks secret detection
      uses: zricethezav/gitleaks-action@v2
      with:
        config-path: .gitleaks.toml
        
    - name: Python Security Check
      if: hashFiles('**/*.py') != ''
      run: |
        pip install bandit safety
        bandit -r . -f json -o bandit-report.json || true
        safety check --json --output safety-report.json || true
    
    - name: Node.js Security Check  
      if: hashFiles('**/package.json') != ''
      run: |
        npm audit --json > npm-audit.json || true
        
    - name: Upload security reports
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: security-reports
        path: |
          bandit-report.json
          safety-report.json  
          npm-audit.json
"""
        
        workflow_file = os.path.join(workflow_dir, "security.yml")
        with open(workflow_file, 'w') as f:
            f.write(security_workflow)
        
        # Create GitLeaks config
        gitleaks_config = """
[allowlist]
  description = "GuardianShield allowed patterns"
  paths = [
    ".env.example",
    ".env.template",
    "tests/",
  ]

[[rules]]
  id = "generic-api-key"
  description = "Generic API Key"
  regex = '''(?i)((access.key|api.key|secret.key)['"]*\s*[:=]\s*['"][a-zA-Z0-9]+['"])'''
  
[[rules]]
  id = "github-token"
  description = "GitHub Token"
  regex = '''ghp_[0-9A-Za-z]{36}'''
  
[[rules]]  
  id = "github-app-token"
  description = "GitHub App Token"
  regex = '''(ghu|ghs)_[0-9A-Za-z]{36}'''
"""
        
        with open(".gitleaks.toml", 'w') as f:
            f.write(gitleaks_config)
        
        return f"Created security workflow: {workflow_file}"
    
    def get_security_status(self) -> Dict:
        """Get current repository security status"""
        repo_info = self.detect_repository_info()
        
        if "error" in repo_info:
            return repo_info
        
        # Check current protection status
        token = self.get_github_token()
        security_status = {
            "repository": repo_info,
            "branch_protection": {},
            "security_features": {},
            "recommendations": []
        }
        
        if token:
            owner = self.config['owner']
            repo = self.config['repo']
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Check branch protection for main branches
            for branch in ["main", "master"]:
                try:
                    url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}/protection"
                    response = requests.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        security_status["branch_protection"][branch] = "✅ Protected"
                    elif response.status_code == 404:
                        if branch == "main":
                            # Check if branch exists
                            branch_url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}"
                            branch_response = requests.get(branch_url, headers=headers)
                            if branch_response.status_code == 200:
                                security_status["branch_protection"][branch] = "❌ Not protected"
                                security_status["recommendations"].append(f"Enable branch protection for {branch}")
                        else:
                            continue  # Branch doesn't exist
                    else:
                        security_status["branch_protection"][branch] = f"❓ Unknown ({response.status_code})"
                        
                except Exception as e:
                    security_status["branch_protection"][branch] = f"❌ Error: {e}"
        
        # Check for security files
        security_files = {
            "Security Policy": "SECURITY.md",
            "Code of Conduct": "CODE_OF_CONDUCT.md",
            "Contributing Guide": "CONTRIBUTING.md",
            "GitHub Security Workflow": ".github/workflows/security.yml",
            "Dependabot Config": ".github/dependabot.yml",
            "GitLeaks Config": ".gitleaks.toml"
        }
        
        for name, filename in security_files.items():
            if os.path.exists(filename):
                security_status["security_features"][name] = "✅ Present"
            else:
                security_status["security_features"][name] = "❌ Missing"
                security_status["recommendations"].append(f"Add {filename}")
        
        return security_status

def main():
    """Main function for command-line usage"""
    import sys
    
    manager = GitHubRepositorySecurityManager()
    
    if len(sys.argv) < 2:
        print("Usage: python github_security_manager.py <command>")
        print("Commands: status, protect, scan, workflow")
        return
    
    command = sys.argv[1]
    
    if command == "status":
        status = manager.get_security_status()
        print("🛡️ Repository Security Status")
        print("=" * 40)
        
        if "repository" in status:
            repo = status["repository"]
            print(f"Repository: {repo.get('url', 'Unknown')}")
        
        if status.get("branch_protection"):
            print("\n🌿 Branch Protection:")
            for branch, status_text in status["branch_protection"].items():
                print(f"  {branch}: {status_text}")
        
        if status.get("security_features"):
            print("\n🔒 Security Features:")
            for feature, status_text in status["security_features"].items():
                print(f"  {feature}: {status_text}")
        
        if status.get("recommendations"):
            print("\n💡 Recommendations:")
            for rec in status["recommendations"]:
                print(f"  • {rec}")
    
    elif command == "protect":
        branch = sys.argv[2] if len(sys.argv) > 2 else "main"
        result = manager.setup_branch_protection(branch)
        
        if "success" in result:
            print(f"✅ {result['success']}")
        else:
            print(f"❌ {result['error']}")
    
    elif command == "scan":
        result = manager.scan_repository_secrets()
        print(f"🔍 Secret Scan Results: {result['total_found']} potential issues found")
        
        if result['suspicious_files']:
            for issue in result['suspicious_files'][:10]:  # Show first 10
                print(f"  ⚠️ {issue['file']}:{issue['line']} - {issue['pattern']}")
        
        print("\n💡 Recommendations:")
        for rec in result['recommendations']:
            print(f"  • {rec}")
    
    elif command == "workflow":
        result = manager.create_security_workflow()
        print(f"✅ {result}")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()