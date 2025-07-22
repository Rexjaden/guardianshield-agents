"""
threat_definitions.py: Contains detailed definitions, patterns, and lists for all threat types GuardianShield agents should detect and prevent.
"""

# Example scam/fraudulent addresses (add real data as needed)
SCAM_ADDRESSES = [
    "0x1234abcd...",
    "0xdeadbeef...",
]

# Example scam/fraudulent apps and websites
SCAM_APPS = [
    "FakeWalletApp",
    "PhishingDApp",
]
SCAM_WEBSITES = [
    "http://scam-site.com",
    "http://phishing-site.net",
]

# Example threat actors
THREAT_ACTORS = [
    "EvilHackerGroup",
    "MaliciousBotnet",
]

# Example malicious IP addresses
MALICIOUS_IPS = [
    "192.0.2.1",
    "203.0.113.5",
]

# Types of theft and deceptive acts
THEFT_TYPES = [
    "wallet drain",
    "rug pull",
    "phishing",
    "social engineering",
    "man-in-the-middle",
    "address poisoning",
    "impersonation",
    "malware injection",
    "DNS hijacking",
    "fake airdrop",
    "pump and dump",
    "exit scam",
]

# Definitions of deceptive acts
DECEPTIVE_ACTS = {
    "phishing": "A fraudulent attempt to obtain sensitive information by disguising as a trustworthy entity.",
    "rug pull": "A type of scam where developers abandon a project and run away with investors' funds.",
    "wallet drain": "Unauthorized transfer of assets from a user's wallet.",
    "address poisoning": "Sending small amounts of tokens to a user's wallet to trick them into copying a scam address.",
    "impersonation": "Pretending to be someone else to gain trust and defraud victims.",
    # Add more definitions as needed
}

# Utility function to check if a value matches any known threat

def is_known_threat(value: str) -> bool:
    value = value.lower()
    return (
        value in [a.lower() for a in SCAM_ADDRESSES]
        or value in [a.lower() for a in SCAM_APPS]
        or value in [w.lower() for w in SCAM_WEBSITES]
        or value in [t.lower() for t in THREAT_ACTORS]
        or value in [ip.lower() for ip in MALICIOUS_IPS]
        or value in [t.lower() for t in THEFT_TYPES]
        or value in [d.lower() for d in DECEPTIVE_ACTS.keys()]
    )

# Utility function to get a definition of a deceptive act
def get_deceptive_act_definition(act: str) -> str:
    return DECEPTIVE_ACTS.get(act.lower(), "Unknown deceptive act.")
