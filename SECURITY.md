# Security policy for GuardianShield Repository

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.x.x   | :white_check_mark: |
| 1.x.x   | :x:                |

## Reporting a Vulnerability

Please report security vulnerabilities to:
- Email: security@guardian-shield.io
- GitHub Security Advisories: Use private vulnerability reporting

### Response Time
- Critical: 24 hours
- High: 48 hours  
- Medium: 7 days
- Low: 14 days

## Security Measures

### Repository Security
- Branch protection enabled on main
- Require signed commits
- Dependency scanning enabled
- Code scanning with CodeQL enabled
- Secret scanning enabled

### Container Security
All containers use:
- Non-root users
- Read-only filesystems
- Capability restrictions (cap_drop: ALL)
- Security contexts and AppArmor
- Minimal attack surface

### Dependency Management
- Regular dependency updates
- Security patches applied within 48 hours
- Automated dependency scanning
- Container vulnerability scanning with Trivy

## Acknowledgments

We thank the security community for responsible disclosure.