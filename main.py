import os
import sys
import tkinter as tk
import argparse
import configparser
import threading
import uvicorn
from slideshow import SlideshowApp
from database import Database
from api import app as api_app

# load_config removed, now handled by Database class

def start_api_server():
    try:
        # Run uvicorn programmatically
        uvicorn.run(api_app, host="0.0.0.0", port=8080, log_level="info")
    except Exception as e:
        print(f"❌ Failed to start API server: {e}", file=sys.stderr)

def main():
    # Initialize Database
    db = Database()
    
    # Database now handles its own sync/initialization
    
    # Start API in daemon thread
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()

    # Load initial state from DB for CLI args
    raw_folder = db.get_setting('default_folder', '/etc/slideshow/images')
    def_folder = os.path.expanduser(raw_folder)
    def_interval = int(db.get_setting('default_interval', '5'))
    def_fullscreen = str(db.get_setting('start_fullscreen', 'True')).lower() == 'true'
    
    if not os.path.isabs(def_folder) and not def_folder.startswith('~'):
        def_folder = os.path.join(os.path.dirname(__file__), def_folder)
    
    parser = argparse.ArgumentParser(description="Clean & Simple Image Slideshow")
    parser.add_argument("--folder", type=str, default=def_folder, help="Folder with images")
    parser.add_argument("--interval", type=int, default=def_interval, help="Seconds between images")
    parser.add_argument("--windowed", action="store_true", help="Start in windowed mode")
    
    args = parser.parse_args()
    
    # Ensure final folder path is absolute and expanded
    final_folder = os.path.abspath(os.path.expanduser(args.folder))
    
    print(f"📂 Slideshow Folder: {final_folder}")
    if not os.path.isdir(final_folder):
        print(f"❌ Error: Directory '{final_folder}' not found.")
        # Don't exit, just show warning in GUI potentially? Or let SlideshowApp handle it
        # sys.exit(1) 

    root = tk.Tk()
    root.geometry("800x600")
    
    # Pass DB instance instead of static config dict
    app = SlideshowApp(
        root, 
        final_folder, 
        args.interval, 
        fullscreen=(def_fullscreen and not args.windowed),
        db=db
    )
    
    # Expose app instance to API for features like current image preview
    api_app.state.slideshow = app
    
    root.mainloop()

if __name__ == "__main__":
    main()
