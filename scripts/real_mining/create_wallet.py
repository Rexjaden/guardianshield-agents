#!/usr/bin/env python3
"""
GuardianShield Monero Wallet Generator
Creates a new XMR wallet with seed phrase
"""

try:
    from monero.seed import Seed
    
    # Generate new wallet
    seed = Seed()
    
    print('='*70)
    print('    GUARDIANSHIELD MONERO WALLET - SAVE THIS INFORMATION!')
    print('='*70)
    print()
    print('SEED PHRASE (WRITE THIS DOWN - DO NOT LOSE IT!):')
    print('-'*70)
    print(seed.phrase)
    print('-'*70)
    print()
    print('WALLET ADDRESS (for mining - this is what you share):')
    print(seed.public_address())
    print()
    print('='*70)
    print('WARNING: Anyone with the seed phrase can access your funds!')
    print('Store it somewhere safe OFFLINE (paper, encrypted file, etc.)')
    print('='*70)
    
except ImportError:
    # Fallback - generate using secrets
    import secrets
    import hashlib
    
    # BIP39 word list (subset for demo - real would need full 2048 words)
    # For a real wallet, use MyMonero.com instead
    print("="*70)
    print("  Monero library not available - Please use MyMonero.com")
    print("="*70)
    print()
    print("Steps to create your wallet:")
    print("1. Go to: https://mymonero.com")
    print("2. Click 'Create new wallet'")
    print("3. WRITE DOWN your 25-word seed phrase")
    print("4. Copy your wallet address (starts with '4')")
    print("5. Share the address with me to configure mining")
    print()
    print("="*70)
