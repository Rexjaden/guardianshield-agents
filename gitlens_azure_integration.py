#!/usr/bin/env python3
"""
GuardianShield Azure Integration with GitLens Enhancement
Leverages VS Code GitLens and Azure extensions for enhanced development workflow.
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class GitLensAzureIntegration:
    """Enhanced development workflow using GitLens and Azure extensions."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.git_info = {}
        self.azure_resources = {}
    
    def analyze_git_contributions(self) -> Dict[str, Any]:
        """Analyze Git contributions for GuardianShield project."""
        try:
            # Get commit statistics
            result = subprocess.run([
                'git', 'log', '--pretty=format:%an|%ae|%ad|%s', 
                '--date=short', '--since=30.days.ago'
            ], capture_output=True, text=True, cwd=self.project_root)
            
            commits = []
            contributors = {}
            
            for line in result.stdout.strip().split('\n'):
                if line:
                    author, email, date, subject = line.split('|', 3)
                    commits.append({
                        'author': author,
                        'email': email,
                        'date': date,
                        'subject': subject
                    })
                    
                    if author not in contributors:
                        contributors[author] = {'count': 0, 'email': email}
                    contributors[author]['count'] += 1
            
            # Get file statistics for GuardianShield components
            file_stats = self.get_file_statistics()
            
            self.git_info = {
                'total_commits_30days': len(commits),
                'contributors': contributors,
                'recent_commits': commits[:10],
                'file_statistics': file_stats,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            return self.git_info
            
        except Exception as e:
            print(f"Git analysis error: {str(e)}")
            return {}
    
    def get_file_statistics(self) -> Dict[str, Any]:
        """Get file statistics for key GuardianShield components."""
        key_files = [
            'main.py',
            'admin_console.py',
            'api_server.py',
            'agents/learning_agent.py',
            'agents/behavioral_analytics.py',
            'agents/dmer_monitor_agent.py',
            'dashboard_manager.py',
            'cache_cleanup.py',
            'memory_optimizer.py'
        ]
        
        file_stats = {}
        
        for file_path in key_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    # Get file size
                    size = full_path.stat().st_size
                    
                    # Get line count
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = len(f.readlines())
                    
                    # Get last modified (Git blame would be better with GitLens)
                    result = subprocess.run([
                        'git', 'log', '-1', '--pretty=format:%an|%ad', 
                        '--date=short', '--', file_path
                    ], capture_output=True, text=True, cwd=self.project_root)
                    
                    last_author, last_date = 'Unknown', 'Unknown'
                    if result.stdout:
                        parts = result.stdout.split('|')
                        if len(parts) == 2:
                            last_author, last_date = parts
                    
                    file_stats[file_path] = {
                        'size_bytes': size,
                        'lines': lines,
                        'last_author': last_author,
                        'last_modified': last_date
                    }
                    
                except Exception as e:
                    file_stats[file_path] = {'error': str(e)}
        
        return file_stats
    
    def generate_azure_deployment_config(self) -> Dict[str, Any]:
        """Generate Azure deployment configuration for GuardianShield."""
        return {
            'resource_group': 'guardianshield-rg',
            'location': 'eastus2',
            'components': {
                'web_server': {
                    'service': 'Azure App Service',
                    'plan': 'guardianshield-plan',
                    'runtime': 'python|3.11',
                    'files': ['api_server.py', 'admin_console.py']
                },
                'functions': {
                    'service': 'Azure Functions',
                    'runtime': 'python',
                    'functions': [
                        {
                            'name': 'threat-analysis',
                            'file': 'agents/behavioral_analytics.py',
                            'trigger': 'timer'
                        },
                        {
                            'name': 'dmer-monitor', 
                            'file': 'agents/dmer_monitor_agent.py',
                            'trigger': 'http'
                        },
                        {
                            'name': 'memory-optimizer',
                            'file': 'memory_optimizer.py',
                            'trigger': 'timer'
                        }
                    ]
                },
                'database': {
                    'service': 'Azure Cosmos DB',
                    'api': 'NoSQL',
                    'containers': [
                        'threat-intelligence',
                        'agent-logs',
                        'security-events'
                    ]
                },
                'analytics': {
                    'service': 'Azure OpenSearch',
                    'dashboards': ['threat-intel', 'web3-security', 'compliance']
                }
            }
        }
    
    def create_gitignore_azure(self):
        """Create/update .gitignore with Azure-specific entries."""
        azure_ignores = [
            "# Azure Functions",
            "bin/",
            "obj/",
            ".azure/",
            "local.settings.json",
            "*.user",
            "*.suo",
            "",
            "# Azure App Service",
            ".deployment",
            "deploy.cmd",
            ".kudu/",
            "",
            "# Environment files",
            ".env.local",
            ".env.production",
            ".env.azure",
            "",
            "# Azure DevOps",
            ".vscode/tasks.json",
            ".vscode/launch.json"
        ]
        
        gitignore_path = self.project_root / '.gitignore'
        
        # Read existing content
        existing_content = []
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                existing_content = f.read().splitlines()
        
        # Check if Azure section already exists
        if "# Azure Functions" not in existing_content:
            with open(gitignore_path, 'a') as f:
                f.write('\n'.join([''] + azure_ignores + ['']))
            print("✅ Updated .gitignore with Azure-specific entries")
        else:
            print("ℹ️ .gitignore already contains Azure entries")
    
    def generate_development_report(self) -> str:
        """Generate a comprehensive development report."""
        git_analysis = self.analyze_git_contributions()
        azure_config = self.generate_azure_deployment_config()
        
        report = f"""
🛡️ GUARDIANSHIELD DEVELOPMENT REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 GIT ANALYSIS (Last 30 days):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Total Commits: {git_analysis.get('total_commits_30days', 0)}
• Active Contributors: {len(git_analysis.get('contributors', {}))}

Top Contributors:
"""
        
        # Add contributor stats
        contributors = git_analysis.get('contributors', {})
        for author, info in sorted(contributors.items(), key=lambda x: x[1]['count'], reverse=True):
            report += f"  • {author}: {info['count']} commits\n"
        
        report += f"""
📁 KEY FILE STATISTICS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Add file stats
        file_stats = git_analysis.get('file_statistics', {})
        for file_path, stats in file_stats.items():
            if 'error' not in stats:
                report += f"• {file_path}: {stats['lines']} lines, last by {stats['last_author']} on {stats['last_modified']}\n"
        
        report += f"""
☁️ AZURE DEPLOYMENT PLAN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Resource Group: {azure_config['resource_group']}
• Location: {azure_config['location']}
• Web Server: {azure_config['components']['web_server']['service']}
• Functions: {len(azure_config['components']['functions']['functions'])} Azure Functions
• Database: {azure_config['components']['database']['service']}
• Analytics: {azure_config['components']['analytics']['service']}

🚀 NEXT STEPS WITH EXTENSIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Use GitLens to explore commit history and blame annotations
• Deploy functions using Azure Functions extension
• Set up Cosmos DB using Azure Cosmos DB extension
• Configure App Service using Azure App Service extension
• Monitor resources using Azure Resources extension

💡 GITLENS FEATURES TO EXPLORE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Git Blame annotations on key files
• Repository timeline and visualization
• Compare branches and commits
• File history exploration
• Contributor insights and statistics
"""
        
        return report


def main():
    """Main function to demonstrate GitLens and Azure integration."""
    integration = GitLensAzureIntegration()
    
    print("🛡️ GuardianShield GitLens & Azure Integration")
    print("=" * 60)
    
    # Update .gitignore for Azure
    integration.create_gitignore_azure()
    
    # Generate and display report
    report = integration.generate_development_report()
    print(report)
    
    # Save report
    report_file = integration.project_root / f"development_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"📊 Report saved to: {report_file.name}")
    print("\n🎯 Ready to leverage GitLens and Azure extensions!")


if __name__ == "__main__":
    main()