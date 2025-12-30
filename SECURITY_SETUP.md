# GuardianShield Security Setup Guide

## ⚠️ IMPORTANT SECURITY NOTICE

This repository contains template files for sensitive security configurations. **NEVER commit actual secrets, keys, or passwords to version control.**

## First-Time Setup

### 1. Automatic Setup (Recommended)

The system will automatically generate secure keys and credentials on first run:

```bash
python main.py
```

The following files will be auto-generated:
- `.guardian_secret` - JWT secret key
- `.guardian_master_password.txt` - Master admin password
- `master.key` - Master encryption key
- `audit_encryption.key` - Audit log encryption key
- `.guardian_admin` - Admin password hash
- `.guardian_authorized_users.json` - Authorized users database

**IMPORTANT**: After first run, save your master password securely and delete `.guardian_master_password.txt` or store it in a secure password manager.

### 2. Manual Setup (Advanced)

If you need to set up the system manually, follow these steps:

#### Generate Secret Key
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))" > .guardian_secret
chmod 600 .guardian_secret
```

#### Generate Encryption Keys
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" > master.key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" > audit_encryption.key
chmod 600 master.key audit_encryption.key
```

#### Set File Permissions
```bash
chmod 600 .guardian_*
chmod 600 *.key
chmod 600 .guardian_authorized_users.json
```

## Database Files

All `.db` files are excluded from version control as they may contain sensitive operational data. These files are automatically created when needed:

- `analytics.db` - Analytics data
- `community_portal.db` - Community data
- `guardian_audit.db` - Audit logs
- `guard_purchases.db` - Purchase records
- `graphics_engine.db` - Graphics data
- `multichain_security.db` - Blockchain security data
- `nft_builder.db` - NFT data
- `payment_gateway.db` - Payment records
- `remaining_agents_education.db` - Agent training data
- `staking.db` - Staking records
- Various agent memory and threat intelligence databases

## Production Deployment

### Environment Variables

For production deployments, use environment variables instead of file-based secrets:

```bash
export GUARDIAN_SECRET="your-secret-key-here"
export GUARDIAN_MASTER_PASSWORD="your-master-password-here"
export MASTER_ENCRYPTION_KEY="your-encryption-key-here"
export AUDIT_ENCRYPTION_KEY="your-audit-key-here"
```

### Docker Secrets

When deploying with Docker, use Docker secrets:

```bash
echo "your-secret" | docker secret create guardian_secret -
echo "your-key" | docker secret create master_key -
```

### Kubernetes Secrets

For Kubernetes deployments:

```bash
kubectl create secret generic guardian-secrets \
  --from-literal=guardian-secret=your-secret \
  --from-literal=master-key=your-key
```

## Security Best Practices

### 1. Key Rotation

Rotate encryption keys periodically (recommended: every 90 days):

```bash
# Backup current keys
cp master.key master.key.backup
cp audit_encryption.key audit_encryption.key.backup

# Generate new keys
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" > master.key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" > audit_encryption.key

# Re-encrypt sensitive data (see admin console)
python admin_console.py
```

### 2. Access Control

- Use strong passwords (minimum 12 characters)
- Enable MFA for all admin accounts
- Regularly review authorized users list
- Monitor failed login attempts

### 3. Backup Strategy

Backup sensitive files securely:

```bash
# Create encrypted backup
tar czf - .guardian_* *.key *.db | gpg -c > guardian_backup_$(date +%Y%m%d).tar.gz.gpg
```

Store backups in a secure, offline location.

### 4. Monitoring

Monitor security-related files:

```bash
# Check file permissions
ls -la .guardian_* *.key

# Review recent authentication attempts
tail -f guardian_audit.db
```

## Troubleshooting

### Missing Key Files

If key files are missing, the system will automatically regenerate them. However, this will make previously encrypted data unrecoverable.

### Permission Denied Errors

Ensure files have correct permissions:

```bash
chmod 600 .guardian_* *.key *.db
```

### Lost Master Password

If you lose the master password, you'll need to reset the security system:

```bash
# WARNING: This will delete all security configurations
rm .guardian_* master.key audit_encryption.key
python main.py  # System will reinitialize
```

## Template Files

The following template files are included in the repository as examples:

- `.guardian_master_password.txt.template`
- `.guardian_secret.template`
- `master.key.template`
- `audit_encryption.key.template`

**DO NOT** use these templates directly. They are for reference only.

## Getting Help

If you encounter security issues:

1. Check the [Security Assessment Report](SECURITY_ASSESSMENT_REPORT.md)
2. Review system logs in `guardian_audit.db`
3. Contact the security team
4. For vulnerabilities, follow responsible disclosure practices

## Additional Resources

- [Main README](README.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Production Deployment](PRODUCTION_DEPLOYMENT.md)
- [Security Assessment Report](SECURITY_ASSESSMENT_REPORT.md)
