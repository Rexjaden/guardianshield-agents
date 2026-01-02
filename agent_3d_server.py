#!/usr/bin/env python3
"""
Web server for 3D Agent Visualization
Serves 3D models and provides interactive viewer
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio
from pathlib import Path
import shutil
from agent_3d_visualizer import Agent3DVisualizer

app = FastAPI(title="GuardianShield 3D Agent Viewer")

# Initialize 3D visualizer
visualizer = Agent3DVisualizer()

# Mount static files for serving 3D assets
app.mount("/assets", StaticFiles(directory="agent_assets"), name="assets")

@app.on_event("startup")
async def startup_event():
    """Load all agent models on startup"""
    await visualizer.load_agent_models()

@app.get("/", response_class=HTMLResponse)
async def showcase():
    """Main showcase page showing all 3D agents"""
    return await visualizer.create_agent_showcase()

@app.get("/agent/3d/{agent_name}", response_class=HTMLResponse)
async def view_agent_3d(agent_name: str):
    """View specific agent in 3D"""
    if agent_name not in visualizer.list_available_agents():
        raise HTTPException(status_code=404, detail="Agent 3D model not found")
    
    return visualizer.generate_web_viewer_html(agent_name)

@app.get("/api/agents")
async def list_agents():
    """API endpoint to list all available 3D agents"""
    return {
        "agents": visualizer.list_available_agents(),
        "count": len(visualizer.list_available_agents())
    }

@app.get("/api/agent/{agent_name}")
async def get_agent_info(agent_name: str):
    """Get information about a specific agent"""
    model = visualizer.get_agent_model(agent_name)
    if not model:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "name": model.agent_name,
        "model_path": model.model_path,
        "texture_path": model.texture_path,
        "position": model.position,
        "rotation": model.rotation,
        "scale": model.scale,
        "metadata": model.metadata
    }

@app.post("/api/agent/{agent_name}/upload")
async def upload_agent_model(
    agent_name: str, 
    model_file: UploadFile = File(...),
    texture_file: UploadFile = File(None)
):
    """Upload a 3D model for an agent"""
    
    # Validate file format
    if not any(model_file.filename.lower().endswith(ext) for ext in visualizer.supported_formats):
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported model format. Supported: {visualizer.supported_formats}"
        )
    
    # Read file data
    model_data = await model_file.read()
    texture_data = await texture_file.read() if texture_file else None
    
    # Get file extension
    model_format = Path(model_file.filename).suffix[1:]  # Remove the dot
    
    # Add the model
    await visualizer.add_agent_model(agent_name, model_data, model_format, texture_data)
    
    return {
        "message": f"3D model uploaded successfully for agent: {agent_name}",
        "model_file": model_file.filename,
        "texture_file": texture_file.filename if texture_file else None
    }

@app.delete("/api/agent/{agent_name}")
async def delete_agent_model(agent_name: str):
    """Delete an agent's 3D model"""
    model = visualizer.get_agent_model(agent_name)
    if not model:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Remove the agent directory
    agent_dir = visualizer.assets_dir / agent_name
    if agent_dir.exists():
        shutil.rmtree(agent_dir)
        
    # Remove from memory
    if agent_name in visualizer.models:
        del visualizer.models[agent_name]
    
    return {"message": f"Agent {agent_name} 3D model deleted successfully"}

@app.get("/upload", response_class=HTMLResponse)
async def upload_page():
    """Upload page for adding new 3D models"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Upload 3D Agent Models</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .upload-form { background: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0; }
            input, button { padding: 10px; margin: 5px; border: 1px solid #ccc; border-radius: 4px; }
            button { background: #007bff; color: white; cursor: pointer; }
            button:hover { background: #0056b3; }
            .back-link { display: inline-block; margin-bottom: 20px; color: #007bff; text-decoration: none; }
            .info { background: #e7f3ff; padding: 15px; border-radius: 4px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <a href="/" class="back-link">← Back to Showcase</a>
        <h1>Upload 3D Agent Models</h1>
        
        <div class="info">
            <h3>Supported Formats:</h3>
            <p><strong>Models:</strong> .glb, .gltf, .obj, .fbx, .dae</p>
            <p><strong>Textures:</strong> .png, .jpg, .jpeg, .webp, .tga</p>
        </div>
        
        <div class="upload-form">
            <h3>Upload New Agent Model</h3>
            <form id="uploadForm" enctype="multipart/form-data">
                <div>
                    <label>Agent Name:</label>
                    <input type="text" id="agentName" placeholder="e.g., learning_agent" required>
                </div>
                <div>
                    <label>3D Model File:</label>
                    <input type="file" id="modelFile" accept=".glb,.gltf,.obj,.fbx,.dae" required>
                </div>
                <div>
                    <label>Texture File (optional):</label>
                    <input type="file" id="textureFile" accept=".png,.jpg,.jpeg,.webp,.tga">
                </div>
                <button type="submit">Upload 3D Model</button>
            </form>
            <div id="status"></div>
        </div>
        
        <script>
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const agentName = document.getElementById('agentName').value;
                const modelFile = document.getElementById('modelFile').files[0];
                const textureFile = document.getElementById('textureFile').files[0];
                
                if (!agentName || !modelFile) {
                    document.getElementById('status').innerHTML = '<p style="color: red;">Please provide agent name and model file.</p>';
                    return;
                }
                
                const formData = new FormData();
                formData.append('model_file', modelFile);
                if (textureFile) {
                    formData.append('texture_file', textureFile);
                }
                
                document.getElementById('status').innerHTML = '<p>Uploading...</p>';
                
                try {
                    const response = await fetch(`/api/agent/${agentName}/upload`, {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        document.getElementById('status').innerHTML = `<p style="color: green;">${result.message}</p>`;
                        setTimeout(() => window.location.href = '/', 2000);
                    } else {
                        document.getElementById('status').innerHTML = `<p style="color: red;">Error: ${result.detail}</p>`;
                    }
                } catch (error) {
                    document.getElementById('status').innerHTML = `<p style="color: red;">Upload failed: ${error.message}</p>`;
                }
            });
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)