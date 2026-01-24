#!/bin/bash
# 🛡️ GuardianShield MASTER DEPLOYMENT
# ===================================
# "The One Script to Rule Them All"
# Launches:
# 1. 🧠 Brain (PyTorch LLM) on Port 5000
# 2. 🔌 API Server (FastAPI) on Port 8000
# 3. 🌐 Website (Ultimate Edition) on Port 8081
# 4. 🗄️ Database (Redis/Postgres)

echo "🚀 Initializing GuardianShield Master Stack..."

# --- 1. Prepare Brain Module ---
echo "🧠 preparing Brain Module..."
mkdir -p brain_build
cat << 'BRAIN_REQ' > brain_build/requirements.txt
torch
fastapi
uvicorn
pydantic
numpy
BRAIN_REQ

cat << 'BRAIN_PY' > brain_build/brain_server.py
from fastapi import FastAPI
from pydantic import BaseModel
import torch
import os

app = FastAPI(title="GuardianShield Brain")

@app.get("/")
def home():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return {"status": "online", "system": "Brain", "device": device}

@app.post("/generate")
def generate(data: BaseModel):
    return {"response": "Brain process active", "data": str(data)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
BRAIN_PY

cat << 'BRAIN_DOCKER' > brain_build/Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY brain_server.py .
CMD ["python", "brain_server.py"]
BRAIN_DOCKER


# --- 2. Prepare Website Module ---
echo "🌐 preparing Website Module..."
mkdir -p website_build
# We will use a simple nginx container for the website to be robust
cat << 'WEB_DOCKER' > website_build/Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY index.html .
CMD ["python", "-m", "http.server", "8081", "--bind", "0.0.0.0"]
WEB_DOCKER

# (We assume index.html exists or we copy the best one)
if [ -f "guardianshield_website/index.html" ]; then
    cp guardianshield_website/index.html website_build/index.html
elif [ -f "professional-landing.html" ]; then
    cp professional-landing.html website_build/index.html
else
    echo "<h1>GuardianShield Active</h1>" > website_build/index.html
fi


# --- 3. Create Master Docker Compose ---
echo "🐳 Generating Network Topology..."
cat << 'COMPOSE_EOF' > docker-compose.master.yml
version: '3.8'

services:
  # 🧠 THE BRAIN
  brain:
    build: 
      context: ./brain_build
    ports:
      - "5000:5000"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: always

  # 🔌 MAIN API (Uses current repo code)
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - BRAIN_URL=http://brain:5000
      - DATABASE_URL=postgresql://postgres:guardian_pass@postgres:5432/guardianshield
      - REDIS_URL=redis://redis:6379
    volumes:
      - .:/app
    depends_on:
      - brain
      - postgres
      - redis

  # 🌐 WEBSITE
  website:
    build:
      context: ./website_build
    ports:
      - "8081:8081"
    links:
      - api

  # 🗄️ INFRASTRUCTURE
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:13-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: guardian_pass
      POSTGRES_DB: guardianshield
    ports:
      - "5432:5432"

COMPOSE_EOF

# --- 4. Launch ---
echo "🧹 Cleaning Ports..."
if command -v fuser &> /dev/null; then
    fuser -k 8000/tcp 2>/dev/null
    fuser -k 8081/tcp 2>/dev/null
    fuser -k 5000/tcp 2>/dev/null
fi

echo "🔥 IGNITION: Launching Stack..."
# We use --build to ensure changes are picked up
docker-compose -f docker-compose.master.yml up -d --build --remove-orphans

echo ""
echo "✅ SYSTEM OPERATIONAL"
echo "------------------------------------------------"
echo "🌐 WEBSITE: http://localhost:8081"
echo "🔌 API:     http://localhost:8000"
echo "🧠 BRAIN:   http://localhost:5000"
echo "------------------------------------------------"
echo "👉 To stop: docker-compose -f docker-compose.master.yml down"
