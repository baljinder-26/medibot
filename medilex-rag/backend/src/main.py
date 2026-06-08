from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import sys

# Append the current directory (src) to sys.path so Render can find local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import time
from typing import List, Optional, Any
import uvicorn

from dotenv import load_dotenv

load_dotenv()

# Agent logic ko import kar rahe hain (jo rag_engine ko manage karta hai)
from agent_logic import run_agentic_rag
import sqlite_db

app = FastAPI(title="MediLex AI - Advanced Medical RAG")

@app.on_event("startup")
def startup_event():
    sqlite_db.init_sqlite_db()

# 1. CORS Setup (Taaki Streamlit backend se baat kar sake bina error ke)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Static Files Setup
# 'assets' folder ko mount kar rahe hain taaki images 'http://localhost:8000/assets/images/...' par accessible hon
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assets_path = os.path.join(BASE_DIR, "assets")
if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
else:
    print(f"[WARNING] Assets folder not found at {assets_path}")
# 3. Request Models
class ChatRequest(BaseModel):
    prompt: str

class UserAuth(BaseModel):
    email: str
    password: str

class UserSignup(BaseModel):
    username: str
    email: str
    password: str
    height: Optional[str] = "N/A"
    weight: Optional[str] = "N/A"
    bmi: Optional[str] = "N/A"
    sessions: List[Any] = []

class UserUpdate(BaseModel):
    email: str
    username: Optional[str] = None
    password: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    bmi: Optional[str] = None
    sessions: Optional[List[Any]] = None

# 4. Endpoints
@app.get("/")
def health_check():
    return {"status": "active", "message": "MediLex AI Backend is running smoothly."}

@app.post("/auth/signup")
def signup(user: UserSignup):
    email_clean = user.email.strip().lower()
    existing = sqlite_db.get_user_by_email(email_clean)
    if existing:
        raise HTTPException(status_code=400, detail="Account with this email already exists.")
    
    new_user = sqlite_db.create_user_db(
        username=user.username,
        email=email_clean,
        password=user.password,
        height=user.height,
        weight=user.weight,
        bmi=user.bmi,
        sessions=user.sessions
    )
    return {"message": "Signup successful", "user": new_user}

@app.post("/auth/signin")
def signin(user: UserAuth):
    email_clean = user.email.strip().lower()
    db_user = sqlite_db.get_user_by_email(email_clean)
    if db_user and db_user["password"] == user.password:
        return {"message": "Signin successful", "user": db_user}
    raise HTTPException(status_code=401, detail="Invalid email or password.")

@app.post("/auth/update")
def update_user(user: UserUpdate):
    email_clean = user.email.strip().lower()
    existing = sqlite_db.get_user_by_email(email_clean)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found.")
    
    updated_user = sqlite_db.update_user_db(
        email=email_clean,
        username=user.username,
        password=user.password,
        height=user.height,
        weight=user.weight,
        bmi=user.bmi,
        sessions=user.sessions
    )
    return {"message": "Update successful", "user": updated_user}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    User ka sawal leta hai aur Agentic Logic ke through 
    Structured Answer + Source Pages + Image return karta hai.
    """
    try:
        if not request.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")

        # Agentic RAG flow start (Routing -> Search -> Rerank -> LLM)
        result = run_agentic_rag(request.prompt)
        
        return result

    except Exception as e:
        print(f"[ERROR] Backend Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/vitals")
def get_live_vitals():
    """
    Returns mock biometric data since live Google Fit integration is disabled for deployment.
    """
    try:
        hr_val = 72
        spo2_val = 98
        summary = "Based on your current biometric readings, your cardiovascular status looks healthy."
        insight = "Your heart rate of 72 bpm and SpO2 of 98% are within optimal ranges. No action required — keep up your current lifestyle."
        state = "ok"
        history = [{"time": "Now", "hr": hr_val, "spo2": spo2_val, "state": state}]
        
        return {
            "hr": hr_val,
            "spo2": spo2_val,
            "summary": summary,
            "insight": insight,
            "state": state,
            "history": history
        }
    except Exception as e:
        print("[ERROR] /api/vitals error:", e)
        raise HTTPException(status_code=500, detail=str(e))

# 5. Run Server
if __name__ == "__main__":
    # Port 8000 par server start hoga
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)