
# 🌐 Guardian-Shield.io Domain Integration Guide

## 📋 STEP 1: GODADDY DNS CONFIGURATION

Login to your GoDaddy account and navigate to DNS Management for **guardian-shield.io**

Add these DNS records:

### A Record (Main Domain):
- **Type**: A
- **Name**: @ 
- **Value**: YOUR_SERVER_IP
- **TTL**: 1 Hour

### CNAME Records (Subdomains):
- **www** → guardian-shield.io
- **app** → guardian-shield.io  
- **api** → guardian-shield.io
- **agents** → guardian-shield.io
- **token** → guardian-shield.io
- **admin** → guardian-shield.io
- **docs** → guardian-shield.io

⏰ **DNS propagation takes 5-30 minutes**

## 📋 STEP 2: SERVER SETUP

### Option A: DigitalOcean Droplet ($12/month)
1. Create Ubuntu 22.04 droplet
2. Point your DNS to droplet IP
3. Run deployment script

### Option B: Vercel + Railway (Modern)
1. Deploy frontend to Vercel
2. Deploy backend to Railway  
3. Configure custom domains

## 📋 STEP 3: DEPLOYMENT

Upload your GuardianShield files and run:
```bash
chmod +x deploy_guardian_shield.sh
./deploy_guardian_shield.sh
```

## 📋 STEP 4: SSL CERTIFICATE

Automatic SSL setup with Let's Encrypt:
```bash
sudo certbot --nginx -d guardian-shield.io -d www.guardian-shield.io -d agents.guardian-shield.io
```

## 🌟 FINAL RESULT

After setup, your sites will be live at:

- **🏠 Main Site**: https://guardian-shield.io
- **🤖 Agent Gallery**: https://agents.guardian-shield.io  
- **⚡ API Server**: https://api.guardian-shield.io
- **🔧 Admin Console**: https://admin.guardian-shield.io
- **🪙 Token System**: https://token.guardian-shield.io

## 💡 RECOMMENDED NEXT STEPS

1. **Set up monitoring** (UptimeRobot)
2. **Configure backups** (automated)
3. **Add Google Analytics** 
4. **Create professional email** (admin@guardian-shield.io)
5. **Set up CI/CD pipeline** (GitHub Actions)

Your GuardianShield ecosystem will be professionally deployed! 🚀
