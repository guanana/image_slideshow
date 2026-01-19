from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any
from database import Database

app = FastAPI()
db = Database()

@app.get("/config")
def get_config():
    return db.get_all_settings()

@app.post("/config")
def update_config(settings: Dict[str, Any] = Body(...)):
    try:
        for key, value in settings.items():
            db.set_setting(key, value)
        return {"status": "ok", "message": "Configuration updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
