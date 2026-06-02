from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import json
import time
from typing import List, Optional, Any
import uvicorn

from dotenv import load_dotenv
import pickle
import datetime
from googleapiclient.discovery import build
import requests

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
    try:
        token_path = r"e:\medibot\token.pkl"
        if not os.path.exists(token_path):
            raise HTTPException(status_code=401, detail="Token not found.")
            
        with open(token_path, "rb") as token:
            creds = pickle.load(token)
            
        service = build('fitness', 'v1', credentials=creds)
        
        end_time = datetime.datetime.now(datetime.timezone.utc)
        start_time = end_time - datetime.timedelta(hours=24)
        
        body_hr = {
            "aggregateBy": [{"dataTypeName": "com.google.heart_rate.bpm"}],
            "bucketByTime": {"durationMillis": 60000},
            "startTimeMillis": int(start_time.timestamp() * 1000),
            "endTimeMillis": int(end_time.timestamp() * 1000)
        }
        
        body_spo2 = {
            "aggregateBy": [{"dataTypeName": "com.google.oxygen_saturation"}],
            "bucketByTime": {"durationMillis": 60000},
            "startTimeMillis": int(start_time.timestamp() * 1000),
            "endTimeMillis": int(end_time.timestamp() * 1000)
        }
        
        result_hr = service.users().dataset().aggregate(userId="me", body=body_hr).execute()
        result_spo2 = service.users().dataset().aggregate(userId="me", body=body_spo2).execute()
        
        # Use india timezone like livehr.py
        india_timezone = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        
        time_map = {}
        
        for bucket in result_hr.get("bucket", []):
            for dataset in bucket.get("dataset", []):
                for point in dataset.get("point", []):
                    values = point.get("value", [])
                    if values and values[0].get("fpVal"):
                        hr = round(values[0].get("fpVal"))
                        start_ns = int(point.get("startTimeNanos", 0))
                        utc_time = datetime.datetime.fromtimestamp(start_ns / 1e9, tz=datetime.timezone.utc)
                        local_time = utc_time.astimezone(india_timezone)
                        
                        if local_time not in time_map:
                            time_map[local_time] = {"time_obj": local_time}
                        time_map[local_time]["hr"] = hr
                        
        for bucket in result_spo2.get("bucket", []):
            for dataset in bucket.get("dataset", []):
                for point in dataset.get("point", []):
                    values = point.get("value", [])
                    if values and values[0].get("fpVal"):
                        spo2 = round(values[0].get("fpVal"), 1)
                        start_ns = int(point.get("startTimeNanos", 0))
                        utc_time = datetime.datetime.fromtimestamp(start_ns / 1e9, tz=datetime.timezone.utc)
                        local_time = utc_time.astimezone(india_timezone)
                        
                        if local_time not in time_map:
                            time_map[local_time] = {"time_obj": local_time}
                        time_map[local_time]["spo2"] = spo2
                        
        # Sort chronologically (oldest first) to carry forward fallbacks properly
        sorted_times = sorted(time_map.keys())
        
        history_all = []
        curr_hr = 72
        curr_spo2 = 98
        
        for t in sorted_times:
            entry = time_map[t]
            if "hr" in entry: curr_hr = entry["hr"]
            if "spo2" in entry: curr_spo2 = entry["spo2"]
            
            time_str = t.strftime("%I:%M %p")
            
            h_state = "ok"
            if curr_spo2 < 92 or curr_hr > 130 or curr_hr < 45: h_state = "danger"
            elif curr_spo2 < 95 or curr_hr > 110 or curr_hr < 55: h_state = "warn"
            
            # Since some points might have the exact same minute but different seconds, we can just append
            # But to avoid duplicate minute rows if we want, we could deduplicate. 
            # We'll just append them all.
            history_all.append({
                "time": time_str,
                "hr": curr_hr,
                "spo2": curr_spo2,
                "state": h_state
            })
            
        # Reverse to get newest first and take top 6
        history_all.reverse()
        history = history_all[:6]
                
        if not history:
            history = [{"time": "Now", "hr": 72, "spo2": 98, "state": "ok"}]
            hr_val = 72
            spo2_val = 98
        else:
            hr_val = history[0]["hr"]
            spo2_val = history[0]["spo2"]
        
        prompt = f"""
        You are a clinical AI assistant. A patient's smart watch just recorded a heart rate of {hr_val} bpm and SpO2 of {spo2_val}%.
        Analyze these readings briefly and reassuringly.
        Provide your response in JSON format with two keys:
        - "summary": A very short 1-sentence summary (e.g. "Based on your current readings, your cardiovascular status looks healthy.")
        - "insight": A detailed 2-3 sentence insight (e.g. "Your heart rate of {hr_val} bpm and SpO2 of {spo2_val}% are within optimal ranges. No action required.")
        Return ONLY valid JSON.
        """
        
        summary = "Based on your current biometric readings, your cardiovascular status looks healthy."
        insight = f"Your heart rate of {hr_val} bpm and SpO2 of {spo2_val}% are within optimal ranges. No action required — keep up your current lifestyle."
        
        try:
            ollama_res = requests.post("http://localhost:11434/api/generate", json={
                "model": "llama3a:latest",
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }, timeout=10)
            if ollama_res.status_code == 200:
                ollama_data = ollama_res.json()
                ai_resp = json.loads(ollama_data.get("response", "{}"))
                summary = ai_resp.get("summary", summary)
                insight = ai_resp.get("insight", insight)
        except Exception as e:
            print("[WARNING] Ollama failed:", e)
            
        state = "ok"
        if spo2_val < 92 or hr_val > 130 or hr_val < 45: state = "danger"
        elif spo2_val < 95 or hr_val > 110 or hr_val < 55: state = "warn"

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