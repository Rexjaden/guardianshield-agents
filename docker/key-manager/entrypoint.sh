#!/bin/sh
# GuardianShield Key Manager Entrypoint
# Secure key management for validator nodes

set -e

echo "🔐 Starting GuardianShield Key Manager..."
echo "Region: ${VALIDATOR_REGION:-default}"
echo "Validator ID: ${VALIDATOR_ID:-unknown}"

# Initialize key directory
mkdir -p /kms/keys /kms/data /kms/backup
chmod 700 /kms/keys
chmod 755 /kms/data
chmod 700 /kms/backup

# Generate validator keys if they don't exist
if [ ! -f "/kms/keys/validator.key" ]; then
    echo "🗝️ Generating new validator keys..."
    openssl genrsa -out /kms/keys/validator.key 4096
    openssl rsa -in /kms/keys/validator.key -pubout -out /kms/keys/validator.pub
    chmod 600 /kms/keys/validator.key
    chmod 644 /kms/keys/validator.pub
    echo "✅ Validator keys generated"
fi

# Start key manager daemon
echo "🔄 Starting key management daemon..."
python3 secure_key_management.py --daemon

# Keep container running
tail -f /dev/null