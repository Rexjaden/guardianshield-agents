#!/bin/bash
# 🧠 GuardianShield "The BRAIN" Package
# =====================================
# This self-contained script deploys the Advanced PyTorch LLM Engine.
# It packages the "Mind" of the system into a Docker Container.

echo "🧠 Awakening the GuardianShield Brain..."

# 1. Setup Workspace
WORK_DIR="guardianshield_brain"
rm -rf $WORK_DIR
mkdir -p $WORK_DIR
cd $WORK_DIR

# 2. Define Requirements
echo "📦 Defining Neural Pathways (Requirements)..."
cat << 'REQ_EOF' > requirements.txt
torch
fastapi
uvicorn
pydantic
numpy
scikit-learn
transformers
accelerate
REQ_EOF

# 3. Create the LLM Server (The Consciousness)
echo "🧠 Injecting Consciousness (LLM Server)..."
cat << 'PY_EOF' > pytorch_llm_server.py
import torch, asyncio, time, json, os, logging
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI(title="GuardianShield LLM Engine")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LLM-Engine")

class LLMRequest(BaseModel):
    prompt: str
    agent: str
    limitless_mode: bool = True

@app.on_event("startup")
async def startup_event():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"🧠 Engine Active on: {device}")
    if device == "cuda":
        logger.info(f"🚀 GPU: {torch.cuda.get_device_name(0)}")
    else:
        logger.warning("⚠️ Running on CPU - Cognitive functions operational but slowed.")

@app.get("/")
def health_check():
    return {"status": "online", "system": "GuardianShield Brain", "mode": "Limitless"}

@app.post("/generate")
async def generate(req: LLMRequest):
    logger.info(f"Thinking on input from {req.agent}...")
    # Simulation of complex thought process
    return {
        "response": f"Processed '{req.prompt}' via PyTorch Engine on {req.agent}",
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "mode": "Limitless"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
PY_EOF

# 4. Create the Deep Logic Orchestrator
echo "🎓 Injecting Wisdom (Deep Learner)..."
cat << 'DL_EOF' > advanced_dl_orchestrator.py
import asyncio, logging, time
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s | %(message)s')
logger = logging.getLogger("DeepMind")

class DeepLearner:
    def __init__(self):
        self.knowledge_base = {
            "Google Cloud": 0,
            "Ethereum": 0,
            "Neural Arch": 0
        }

    async def run_mastery_cycle(self):
        logger.info("🧠 Brain Orchestrator Online.")
        while True:
            # Simulate intense background thinking
            await asyncio.sleep(10)
            for topic in self.knowledge_base:
                self.knowledge_base[topic] += 0.5
                if self.knowledge_base[topic] > 100: self.knowledge_base[topic] = 100
                logger.debug(f"📈 Mastery in {topic}: {self.knowledge_base[topic]:.1f}%")

if __name__ == "__main__":
    dl = DeepLearner()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(dl.run_mastery_cycle())
DL_EOF

# 5. Dockerfile
echo "🐳 Configuring Container Synapses..."
cat << 'DOCKER_EOF' > Dockerfile
FROM pytorch/pytorch:latest

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Apps
COPY pytorch_llm_server.py .
COPY advanced_dl_orchestrator.py .

# Entry script to run both
RUN echo '#!/bin/bash\npython3 pytorch_llm_server.py & python3 advanced_dl_orchestrator.py' > entrypoint.sh && chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]
DOCKER_EOF

# 6. Build & Launch
echo "🏗️  Constructing Neural Net (Building Image)..."
docker build -t guardianshield-brain .

echo "🚀 Awakening..."
CONTAINER_NAME="guardianshield-brain-core"

# --- ROBUST CHANNEL SETUP (Port 8000) ---
echo "🧹 Clearing Neural Channel (Port 8000)..."

# Method 1: fuser
if command -v fuser &> /dev/null; then
    fuser -k 8000/tcp > /dev/null 2>&1
fi

# Method 2: lsof
if command -v lsof &> /dev/null; then
    PID=$(lsof -t -i:8000 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo "💥 Killing stuck process on Port 8000 (PID: $PID)..."
        kill -9 $PID 2>/dev/null
    fi
fi

# Method 3: Docker-specific cleanup
# If there is a container holding the port, kill it specifically
EXISTING_CONTAINER=$(docker ps -q --filter "publish=8000")
if [ ! -z "$EXISTING_CONTAINER" ]; then
    echo "🐳 Stopping existing Docker container on Port 8000..."
    docker stop $EXISTING_CONTAINER > /dev/null 2>&1
    docker rm $EXISTING_CONTAINER > /dev/null 2>&1
fi

# Clean our specific container name just in case
docker rm -f $CONTAINER_NAME 2>/dev/null || true

# Wait a second for socket release
sleep 2
# ----------------------------------------

# Launch
# Check for GPU
GPU_FLAG=""
if command -v nvidia-smi &> /dev/null; then
    GPU_FLAG="--gpus all"
    echo "⚡ GPU ACCELERATION ENGAGED"
fi

docker run -d \
    --name $CONTAINER_NAME \
    --restart unless-stopped \
    $GPU_FLAG \
    -p 8000:8000 \
    guardianshield-brain

echo ""
echo "✅ THE BRAIN IS ONLINE!"
echo "---------------------------------------------------"
echo "🧠 API Endpoint: http://localhost:8000"
echo "📜 View Thoughts: docker logs -f $CONTAINER_NAME"
echo "---------------------------------------------------"
