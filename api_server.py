from fastapi import FastAPI
from agents.behavioral_analytics import BehavioralAnalyticsAgent
from agents.dmer_monitor_agent import DMERMonitorAgent

app = FastAPI()

# Example: Endpoint to run Behavioral Analytics Agent
def get_behavioral_analytics_result():
    agent = BehavioralAnalyticsAgent()
    result = agent.run()  # Adjust method name as needed
    return result

@app.get("/api/behavioral-analytics")
def behavioral_analytics():
    return {"result": get_behavioral_analytics_result()}

# Example: Endpoint to run DMER Monitor Agent
def get_dmer_monitor_result():
    agent = DMERMonitorAgent()
    result = agent.run()  # Adjust method name as needed
    return result

@app.get("/api/dmer-monitor")
def dmer_monitor():
    return {"result": get_dmer_monitor_result()}

# Add more endpoints for other agents as needed

# To run: uvicorn api_server:app --reload
