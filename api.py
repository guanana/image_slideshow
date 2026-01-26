import os
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any
from database import Database

app = FastAPI(title="Slideshow API")
db = Database()

@app.get("/", response_class=HTMLResponse)
def dashboard():
    try:
        html_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
        with open(html_path, "r") as f:
            return f.read()
    except Exception as e:
        return f"<html><body><h1>Error loading dashboard</h1><p>{str(e)}</p></body></html>"

@app.get("/config")
def get_config():
    return db.get_all_settings()

@app.post("/config")
def update_config(settings: Dict[str, Any] = Body(...)):
    try:
        # Load current state to validate cross-field constraints
        current = db.get_all_settings()
        
        # Merge incoming changes with current state for validation
        new_inky = settings.get('enable_inky', current.get('enable_inky', 'False')).lower() == 'true'
        new_interval_raw = settings.get('default_interval', current.get('default_interval', '5'))
        new_interval = int(new_interval_raw)
        
        if new_inky and new_interval < 30:
            raise HTTPException(
                status_code=400, 
                detail="Default interval must be at least 30 seconds when Inky is enabled."
            )
            
        for key, value in settings.items():
            db.set_setting(key, value)
        return {"status": "ok", "message": "Configuration updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/config/sync")
def sync_config():
    try:
        success = db.sync_with_config()
        if success:
            return {"status": "ok", "message": "Configuration synced from config.ini"}
        else:
            return {"status": "warning", "message": "config.ini not found or invalid"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
