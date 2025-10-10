"""
setup.py: Installation script for GuardianShield Agents
"""
from setuptools import setup, find_packages
import os

# Read README file
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

# Read requirements
def read_requirements():
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="guardianshield-agents",
    version="1.0.0",
    description="Autonomous self-improving security agents for Web3 threat detection and prevention",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    author="GuardianShield Team",
    author_email="security@guardianshield.network",
    url="https://github.com/guardianshield/guardianshield-agents",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Solidity",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "ai": [
            "torch>=2.0.0",
            "transformers>=4.30.0",
        ],
        "full": [
            "torch>=2.0.0",
            "transformers>=4.30.0",
            "sqlalchemy>=2.0.0",
            "psutil>=5.9.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "guardianshield=main:main",
            "guardian-admin=admin_console:main",
            "guardian-api=api_server:main",
        ]
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.yaml", "*.yml", "*.sol"],
    },
    keywords=[
        "security", "web3", "blockchain", "threat-detection", 
        "ai", "machine-learning", "autonomous-agents", "cybersecurity",
        "defi", "smart-contracts", "flare-network", "dmer"
    ],
    project_urls={
        "Bug Reports": "https://github.com/guardianshield/guardianshield-agents/issues",
        "Source": "https://github.com/guardianshield/guardianshield-agents",
        "Documentation": "https://docs.guardianshield.network",
    },
)