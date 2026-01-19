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

def load_config():
    config = configparser.ConfigParser()
    
    # Locations: prioritizing system config then CWD then user config then script directory
    locations = [
        '/etc/slideshow/config.ini',
        os.path.join(os.getcwd(), 'config.ini'),
        os.path.expanduser('~/.config/simple-image-slideshow/config.ini'),
        os.path.join(os.path.dirname(__file__), 'config.ini')
    ]
    
    config_file = None
    for loc in locations:
        if os.path.exists(loc):
            config_file = loc
            break
            
    if not config_file:
        print("⚠️ Warning: config.ini not found! Using very basic defaults.", file=sys.stderr)
        return {}
        
    print(f"📖 MATCHED CONFIG: {config_file}", file=sys.stderr)
    config.read(config_file)
    
    if 'slideshow' in config:
        return dict(config['slideshow'])
    
    print("⚠️ Warning: [slideshow] section not found in config.ini!")
    return {}

def start_api_server():
    try:
        # Run uvicorn programmatically
        uvicorn.run(api_app, host="0.0.0.0", port=8080, log_level="info")
    except Exception as e:
        print(f"❌ Failed to start API server: {e}", file=sys.stderr)

def main():
    # Initialize Database
    db = Database()
    
    # Check if migration is needed (if DB is empty)
    if db.is_empty():
        print("ℹ️  Database empty. Migrating initial config...", file=sys.stderr)
        config = load_config()
        # Default defaults if even load_config returns nothing useful
        defaults = {
            'default_folder': '/etc/slideshow/images',
            'default_interval': '5',
            'background_color': 'black',
            'enable_manual_controls': 'True',
            'start_fullscreen': 'True',
            'image_extensions': '.jpg,.jpeg,.png,.gif,.bmp,.webp'
        }
        
        # Merge loaded config over defaults
        final_config = defaults.copy()
        final_config.update(config)
        
        for k, v in final_config.items():
            db.set_setting(k, v)
    
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
    
    root.mainloop()

if __name__ == "__main__":
    main()
