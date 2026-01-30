import os
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.responses import HTMLResponse, FileResponse
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

@app.post("/restart")
def restart_app():
    import signal
    import threading
    import time
    import sys

    # Standard restart via re-executing this process
    def restart_soon():
        time.sleep(1) # Give time for response to send
        
        # If we're using a full path to python (like in a venv), use that
        python = sys.executable
        # Get the path to the current script
        script = sys.argv[0]
        # Get the arguments passed to the script, filter out executable itself if present
        args = sys.argv[1:]
        
        print("🔄 Restarting application...")
        os.execv(python, [python, script] + args)

    threading.Thread(target=restart_soon).start()
    return {"status": "ok", "message": "Restarting application..."}

@app.get("/current-image")
def get_current_image(request: Request):
    try:
        slideshow = getattr(request.app.state, 'slideshow', None)
        if slideshow and getattr(slideshow, 'current_photo_path', None):
            path = slideshow.current_photo_path
            if path and os.path.exists(path):
                return FileResponse(path)
        raise HTTPException(status_code=404, detail="No image currently displayed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Provider Endpoints ====================

@app.get("/providers")
def list_providers():
    """List all registered image source providers."""
    from providers import list_providers as get_provider_names, get_provider
    
    result = []
    for name in get_provider_names():
        provider = get_provider(name)
        if provider:
            # Load saved config
            saved_config = db.get_provider_settings(name)
            provider.configure(saved_config)
            is_valid, _ = provider.validate_config()
            last_sync = db.get_provider_last_sync(name)
            
            result.append({
                "name": provider.name,
                "display_name": provider.display_name,
                "description": provider.description,
                "configured": is_valid,
                "last_sync": last_sync,
            })
    
    return {"providers": result}


@app.get("/providers/{provider_name}")
def get_provider_info(provider_name: str):
    """Get detailed information about a specific provider."""
    from providers import get_provider
    
    provider = get_provider(provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
    
    # Load saved config
    saved_config = db.get_provider_settings(provider_name)
    provider.configure(saved_config)
    is_valid, error = provider.validate_config()
    last_sync = db.get_provider_last_sync(provider_name)
    
    return {
        "name": provider.name,
        "display_name": provider.display_name,
        "description": provider.description,
        "configured": is_valid,
        "config_error": error,
        "config": provider.get_config(),  # Masked sensitive fields
        "config_schema": provider.get_config_schema(),
        "last_sync": last_sync,
    }


@app.get("/providers/{provider_name}/config")
def get_provider_config(provider_name: str):
    """Get configuration schema and current values for a provider."""
    from providers import get_provider
    
    provider = get_provider(provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
    
    saved_config = db.get_provider_settings(provider_name)
    provider.configure(saved_config)
    
    return {
        "schema": provider.get_config_schema(),
        "values": provider.get_config(),
    }


@app.post("/providers/{provider_name}/config")
def update_provider_config(provider_name: str, settings: Dict[str, Any] = Body(...)):
    """Update configuration for a provider."""
    from providers import get_provider
    
    provider = get_provider(provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
    
    try:
        # Merge with existing settings (for partial updates)
        existing = db.get_provider_settings(provider_name)
        merged = {**existing, **settings}
        
        # Validate new config
        provider.configure(merged)
        is_valid, error = provider.validate_config()
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid configuration: {error}")
        
        # Save to database
        db.set_provider_settings(provider_name, merged)
        
        return {"status": "ok", "message": f"Configuration updated for {provider.display_name}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/providers/{provider_name}/test")
def test_provider_connection(provider_name: str):
    """Test the connection to a provider's external service."""
    from providers import get_provider
    
    provider = get_provider(provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
    
    try:
        # Load saved config
        saved_config = db.get_provider_settings(provider_name)
        provider.configure(saved_config)
        
        success, message = provider.test_connection()
        
        return {
            "status": "ok" if success else "error",
            "success": success,
            "message": message,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/providers/{provider_name}/refresh")
def refresh_provider(provider_name: str):
    """Trigger image refresh/download from a provider."""
    from providers import get_provider
    
    provider = get_provider(provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
    
    try:
        # Load saved config
        saved_config = db.get_provider_settings(provider_name)
        provider.configure(saved_config)
        
        # Validate before refresh
        is_valid, error = provider.validate_config()
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Provider not configured: {error}")
        
        # Get target folder from slideshow config
        target_folder = db.get_setting('default_folder', '/etc/slideshow/images')
        target_folder = os.path.expanduser(target_folder)
        
        # Execute refresh
        result = provider.refresh(target_folder)
        
        # Store result for status tracking
        db.set_provider_last_sync(provider_name, result.to_dict())
        
        return {
            "status": "ok" if result.status.value in ("success", "partial") else "error",
            "result": result.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/providers/{provider_name}/force-sync")
def force_sync_provider(provider_name: str):
    """Clear target folder and perform a full refresh from the provider."""
    from providers import get_provider
    import shutil
    
    provider = get_provider(provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
    
    try:
        # Load saved config
        saved_config = db.get_provider_settings(provider_name)
        provider.configure(saved_config)
        
        # Validate before sync
        is_valid, error = provider.validate_config()
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Provider not configured: {error}")
            
        # Get target folder
        target_folder = db.get_setting('default_folder', '/etc/slideshow/images')
        target_folder = os.path.expanduser(target_folder)
        
        # Safety check: only clear if directory exists and is not root or critical dir
        if os.path.exists(target_folder) and len(target_folder) > 5:
            # List of extensions to remove
            ext_str = db.get_setting('image_extensions', '.jpg,.jpeg,.png,.gif,.bmp,.webp')
            valid_exts = {e.strip().lower() for e in ext_str.split(',')}
            
            for item in os.listdir(target_folder):
                item_path = os.path.join(target_folder, item)
                if os.path.isfile(item_path):
                    _, ext = os.path.splitext(item.lower())
                    if ext in valid_exts or not valid_exts:
                        os.remove(item_path)
        
        # Execute refresh (now it will download everything since folder is empty)
        result = provider.refresh(target_folder)
        
        # Store result
        db.set_provider_last_sync(provider_name, result.to_dict())
        
        return {
            "status": "ok" if result.status.value in ("success", "partial") else "error",
            "result": result.to_dict(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/providers/{provider_name}/status")
def get_provider_status(provider_name: str):
    """Get the last sync status for a provider."""
    from providers import get_provider
    
    provider = get_provider(provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
    
    last_sync = db.get_provider_last_sync(provider_name)
    
    return {
        "provider": provider_name,
        "last_sync": last_sync if last_sync else None,
    }


@app.post("/providers/{provider_name}/albums")
def fetch_provider_albums(provider_name: str, credentials: Dict[str, Any] = Body(...)):
    """Fetch available albums from the provider using provided credentials."""
    if provider_name != "immich":
        raise HTTPException(status_code=400, detail="Album fetching only supported for Immich provider")
    
    server_url = credentials.get("server_url", "").rstrip("/")
    api_key = credentials.get("api_key", "")
    
    if not server_url or not api_key:
        raise HTTPException(status_code=400, detail="Server URL and API Key are required")
    
    try:
        from immich_lib.client import ImmichClient
        client = ImmichClient(server_url, api_key)
        
        # Verify connection first
        auth = client.check_auth()
        if not auth:
            raise HTTPException(status_code=401, detail="Authentication failed - check your API key")
        
        # Fetch albums
        albums = client.list_albums() or []
        
        # Format for dropdown
        album_list = [{"id": "", "name": "(All Assets)", "count": 0}]
        for album in albums:
            album_list.append({
                "id": album.get("id", ""),
                "name": album.get("albumName", "Unknown"),
                "count": album.get("assetCount", 0),
            })
        
        return {
            "status": "ok",
            "albums": album_list,
        }
    except ImportError:
        raise HTTPException(status_code=500, detail="immich-lib package not installed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch albums: {str(e)}")

