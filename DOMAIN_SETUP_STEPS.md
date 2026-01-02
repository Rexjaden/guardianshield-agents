# GUARDIANSHIELD DOMAIN LINKING - STEP BY STEP
## Rex Judon Rogers - Domain Setup for Grant Applications

**Goal**: Get your GuardianShield platform live on a professional domain before submitting grant applications.

## 🎯 **STEP 1: REGISTER YOUR DOMAIN (5 minutes)**

### **BEST CHOICE: guardian-shield.io**
1. **Go to Cloudflare.com** (cheapest + best DNS)
2. **Click "Register Domain"**  
3. **Search**: `guardian-shield.io` or `guardianshield.io`
4. **Purchase** (~$12-15/year)
5. **Add to Cloudflare DNS** (automatic)

**Alternative if taken**: `guardian-shield.tech`, `guardianshield.ai`

---

## 🏗️ **STEP 2: GET HOSTING SERVER (10 minutes)**

### **RECOMMENDED: DigitalOcean**
1. **Go to**: digitalocean.com
2. **Sign up** (use GitHub account for quick setup)
3. **Create Droplet**:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic $6/month (1GB RAM)
   - **Location**: New York or San Francisco
   - **Authentication**: SSH Key (or Password)
4. **Note your server IP**: `XXX.XXX.XXX.XXX`

---

## 🔧 **STEP 3: CONNECT DOMAIN TO SERVER (5 minutes)**

### **In Cloudflare DNS**:
1. **Login to Cloudflare**
2. **Select your domain**
3. **Go to DNS Records**
4. **Add A Record**:
   - **Type**: A
   - **Name**: @ 
   - **Content**: YOUR_SERVER_IP
   - **TTL**: Auto
5. **Add CNAME Record**:
   - **Type**: CNAME
   - **Name**: www
   - **Content**: your-domain.com
   - **TTL**: Auto

---

## 🚀 **STEP 4: DEPLOY GUARDIANSHIELD TO SERVER (15 minutes)**

### **Connect to your server**:
```bash
# SSH into your server
ssh root@YOUR_SERVER_IP

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt update
apt install -y docker-compose nginx certbot python3-certbot-nginx git

# Clone your repository
git clone https://github.com/Rexjaden/Guardianshield-Agents.git
cd Guardianshield-Agents
```

### **Create production environment file**:
```bash
# Create .env file
cp .env.example .env

# Edit with your settings
nano .env
```

**Add these key variables to .env**:
```env
DOMAIN=your-domain.com
EMAIL=rexxrog1@gmail.com
POSTGRES_PASSWORD=your-secure-password
REDIS_PASSWORD=your-redis-password
```

---

## 🔒 **STEP 5: SSL CERTIFICATE & NGINX (10 minutes)**

### **Setup Nginx configuration**:
```bash
# Create Nginx config
cat > /etc/nginx/sites-available/guardianshield << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable the site
ln -s /etc/nginx/sites-available/guardianshield /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```

### **Get SSL Certificate**:
```bash
# Get free SSL from Let's Encrypt
certbot --nginx -d your-domain.com -d www.your-domain.com --email rexxrog1@gmail.com --agree-tos --non-interactive
```

---

## 🚀 **STEP 6: START GUARDIANSHIELD PLATFORM (5 minutes)**

```bash
# In your project directory
cd /root/Guardianshield-Agents

# Start the platform
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

---

## ✅ **STEP 7: VERIFY EVERYTHING WORKS (5 minutes)**

### **Test your domain**:
1. **Visit**: https://your-domain.com
2. **Should see**: GuardianShield dashboard/landing page
3. **Test API**: https://your-domain.com/api/status
4. **Check SSL**: Green lock in browser

### **Update your grant applications**:
- **Website URL**: https://your-domain.com
- **Demo URL**: https://your-domain.com/demo
- **API Documentation**: https://your-domain.com/docs

---

## 🎯 **QUICK DOMAIN OPTIONS FOR IMMEDIATE USE**

### **Option A: Use GitHub Pages (FREE - 2 minutes)**
1. **Go to your repo**: https://github.com/Rexjaden/Guardianshield-Agents
2. **Settings > Pages**
3. **Source**: Deploy from a branch (main)
4. **Your URL**: https://rexjaden.github.io/Guardianshield-Agents
5. **Update grant applications** with this URL

### **Option B: Use Vercel (FREE - 5 minutes)**
1. **Go to**: vercel.com
2. **Sign in with GitHub**
3. **Import**: Guardianshield-Agents repository
4. **Deploy** (automatic)
5. **Your URL**: https://guardianshield-agents.vercel.app
6. **Connect custom domain** later

---

## 📧 **UPDATE YOUR GRANT APPLICATIONS**

**Before submitting, update these fields in your applications**:

```json
{
  "website": "https://your-domain.com",
  "demo_url": "https://your-domain.com/demo", 
  "documentation": "https://your-domain.com/docs",
  "github_repository": "https://github.com/Rexjaden/Guardianshield-Agents",
  "contact_email": "rexxrog1@gmail.com"
}
```

---

## ⏰ **TOTAL TIME: 1 HOUR**

**Fastest Path (15 minutes)**:
1. Use Vercel deployment (5 min)
2. Register domain on Cloudflare (5 min)  
3. Connect domain to Vercel (3 min)
4. Update grant applications (2 min)

**Professional Path (1 hour)**:
Complete all steps above for full production deployment.

---

## 🆘 **IF YOU NEED HELP**

**Common Issues**:
- **DNS not working**: Wait 24 hours for propagation
- **SSL certificate failed**: Check domain DNS first
- **Docker issues**: Run `docker-compose down && docker-compose up -d`
- **Nginx errors**: Check config with `nginx -t`

**Quick Support**:
- DigitalOcean has 24/7 chat support
- Cloudflare docs are excellent: docs.cloudflare.com
- Vercel deployment is almost instant

**Ready to start? Which option do you prefer: Quick (Vercel) or Professional (DigitalOcean)?**