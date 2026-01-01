#!/usr/bin/env python3
"""
Test script to verify sensitive files are properly excluded from version control
and that the system handles missing files gracefully.
"""

import os
import subprocess
import sys

def test_gitignore():
    """Test that .gitignore properly excludes sensitive files"""
    print("🔍 Testing .gitignore configuration...")
    
    sensitive_files = [
        '.guardian_secret',
        '.guardian_master_password.txt',
        'master.key',
        'audit_encryption.key',
        'test.db',
        'agent_action_log.jsonl',
    ]
    
    errors = []
    for file in sensitive_files:
        # Check if file would be ignored
        result = subprocess.run(
            ['git', 'check-ignore', file],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            errors.append(f"❌ File '{file}' is NOT ignored by .gitignore")
        else:
            print(f"✅ File '{file}' is properly ignored")
    
    if errors:
        print("\n".join(errors))
        return False
    
    print("✅ All sensitive file patterns are properly ignored")
    return True

def test_no_sensitive_files_tracked():
    """Verify no sensitive files are currently tracked in git"""
    print("\n🔍 Checking for tracked sensitive files...")
    
    result = subprocess.run(
        ['git', 'ls-files'],
        capture_output=True,
        text=True
    )
    
    tracked_files = result.stdout.split('\n')
    
    sensitive_patterns = [
        '.guardian_master_password.txt',
        '.guardian_secret',
        '.guardian_admin',
        'master.key',
        'audit_encryption.key',
        'mfa_qr_',
        '.db',
        'agent_action_log.jsonl',
        'agent_decision_log.jsonl',
        'agent_evolution_log.jsonl',
    ]
    
    # Exclude patterns that are not actually sensitive
    exclude_patterns = [
        '.dbg.json',  # Hardhat/Solidity debug artifacts
        'artifacts/',  # Build artifacts
    ]
    
    found_sensitive = []
    for file in tracked_files:
        # Skip if matches an exclude pattern
        if any(excl in file for excl in exclude_patterns):
            continue
        
        for pattern in sensitive_patterns:
            if pattern in file and not file.endswith('.template'):
                found_sensitive.append(file)
    
    if found_sensitive:
        print("❌ Found tracked sensitive files:")
        for file in found_sensitive:
            print(f"   - {file}")
        return False
    
    print("✅ No sensitive files are tracked in git")
    return True

def test_template_files_exist():
    """Verify template files exist"""
    print("\n🔍 Checking for template files...")
    
    template_files = [
        '.guardian_master_password.txt.template',
        '.guardian_secret.template',
        'master.key.template',
        'audit_encryption.key.template',
    ]
    
    errors = []
    for file in template_files:
        if not os.path.exists(file):
            errors.append(f"❌ Template file missing: {file}")
        else:
            print(f"✅ Template exists: {file}")
    
    if errors:
        print("\n".join(errors))
        return False
    
    print("✅ All template files exist")
    return True

def test_documentation_exists():
    """Verify security documentation exists"""
    print("\n🔍 Checking security documentation...")
    
    doc_files = [
        'SECURITY_SETUP.md',
        'README.md',
    ]
    
    errors = []
    for file in doc_files:
        if not os.path.exists(file):
            errors.append(f"❌ Documentation missing: {file}")
        else:
            # Check if README mentions security
            if file == 'README.md':
                with open(file, 'r') as f:
                    content = f.read()
                    if 'SECURITY_SETUP.md' not in content:
                        errors.append(f"❌ README.md doesn't reference SECURITY_SETUP.md")
                    else:
                        print(f"✅ README.md references security documentation")
            else:
                print(f"✅ Documentation exists: {file}")
    
    if errors:
        print("\n".join(errors))
        return False
    
    print("✅ Security documentation is complete")
    return True

def main():
    """Run all validation tests"""
    print("🛡️  GuardianShield Security Configuration Validation")
    print("=" * 60)
    
    tests = [
        ("GitIgnore Configuration", test_gitignore),
        ("No Sensitive Files Tracked", test_no_sensitive_files_tracked),
        ("Template Files", test_template_files_exist),
        ("Security Documentation", test_documentation_exists),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Error running test '{test_name}': {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ All security configuration tests passed!")
        return 0
    else:
        print("❌ Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
