# 🚀 GuardianShield DigitalOcean Deployment Guide

## 📋 Complete Step-by-Step Deployment

### **STEP 1: Create DigitalOcean Droplet**

1. **Login to DigitalOcean**
2. **Create Droplet:**
   - **Image:** Ubuntu 22.04 LTS
   - **Size:** Basic $18/month (2 vCPU, 2GB RAM) - Recommended
   - **Region:** Choose closest to your users (NYC, SFO, AMS)
   - **Authentication:** Add your SSH key
   - **Hostname:** guardianshield-production
   - **Tags:** guardianshield, production
   - **Enable:** Backups, Monitoring

### **STEP 2: Initial Server Setup**

```bash
# SSH into your droplet
ssh root@YOUR_DROPLET_IP

# Upload and run setup script
wget https://your-transfer-service.com/droplet_setup.sh
chmod +x droplet_setup.sh
./droplet_setup.sh
```

### **STEP 3: Upload Application Files**

From your local machine:
```bash
# Edit upload script with your droplet IP
nano upload_to_droplet.sh
# Set DROPLET_IP="your.droplet.ip.here"

# Run upload
./upload_to_droplet.sh
```

### **STEP 4: Configure GoDaddy DNS**

In your GoDaddy control panel for **guardian-shield.io**:

| Type  | Name   | Value            | TTL   |
|-------|--------|------------------|-------|
| A     | @      | YOUR_DROPLET_IP  | 1 Hour|
| CNAME | www    | guardian-shield.io    | 1 Hour|
| CNAME | agents | guardian-shield.io    | 1 Hour|
| CNAME | api    | guardian-shield.io    | 1 Hour|
| CNAME | admin  | guardian-shield.io    | 1 Hour|
| CNAME | token  | guardian-shield.io    | 1 Hour|

⏰ **Wait 5-30 minutes for DNS propagation**

### **STEP 5: Deploy Applications**

SSH into your droplet:
```bash
ssh root@YOUR_DROPLET_IP
cd /var/www/guardian-shield.io
./deploy_applications.sh
```

### **STEP 6: Setup SSL Certificates**

After DNS has propagated:
```bash
# Check DNS first
dig +short guardian-shield.io
# Should return your droplet IP

# Setup SSL
./ssl_setup.sh
```

## 🎉 **DEPLOYMENT COMPLETE!**

Your GuardianShield system will be live at:

- **🏠 Main Site:** https://guardian-shield.io
- **🤖 Agent Gallery:** https://agents.guardian-shield.io
- **⚡ API Server:** https://api.guardian-shield.io
- **🔧 Admin Console:** https://admin.guardian-shield.io
- **🪙 Token System:** https://token.guardian-shield.io

## 📊 **Monitoring & Maintenance**

```bash
# Check system status
./monitor_system.sh

# View service logs
journalctl -u guardianshield-gallery -f
journalctl -u guardianshield-api -f
journalctl -u guardianshield-admin -f

# Restart services if needed
systemctl restart guardianshield-gallery
systemctl restart guardianshield-api
systemctl restart guardianshield-admin
```

## 💰 **Monthly Costs**

- **DigitalOcean Droplet:** $18/month (2GB RAM, 2 vCPU)
- **Domain:** ~$1/month (guardian-shield.io)
- **SSL Certificate:** FREE (Let's Encrypt)
- **Backups:** Included
- **Total:** ~$19/month

## 🔧 **Troubleshooting**

**Service won't start:**
```bash
systemctl status guardianshield-SERVICE_NAME
journalctl -u guardianshield-SERVICE_NAME
```

**SSL issues:**
```bash
certbot certificates
certbot renew --dry-run
```

**DNS not working:**
```bash
dig +short guardian-shield.io
nslookup guardian-shield.io
```

Your professional GuardianShield ecosystem is ready for production! 🛡️🚀
