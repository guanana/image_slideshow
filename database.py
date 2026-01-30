import sqlite3
import os
import threading
import configparser
import sys

class Database:
    def __init__(self, db_path="/etc/slideshow/config.db", config_locations=None):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.config_locations = config_locations
        self._init_db()
        self.load_defaults()
        self.sync_with_config()
        self._validate_inky_constraint()

    def _init_db(self):
        # Ensure directory exists if possible, though strict permissions might block this
        # Usually setup.sh handles creation, but good to be safe for dev
        try:
             os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        except OSError:
             pass # Likely permission denied, assume dir exists

        with self._lock, sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.commit()

    def get_setting(self, key, default=None):
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def set_setting(self, key, value):
        with self._lock, sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (str(key), str(value)))
            conn.commit()

    def get_all_settings(self):
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT key, value FROM settings")
            return {row[0]: row[1] for row in cursor.fetchall()}

    def is_empty(self):
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM settings")
            return cursor.fetchone()[0] == 0

    def load_defaults(self):
        """Load built-in defaults if no config.ini or DB exists."""
        defaults = {
            'default_folder': '/etc/slideshow/images',
            'default_interval': '5',
            'background_color': 'black',
            'enable_manual_controls': 'True',
            'start_fullscreen': 'True',
            'image_extensions': '.jpg,.jpeg,.png,.gif,.bmp,.webp',
            'enable_inky': 'False',
            'orientation': 'landscape'
        }
        for k, v in defaults.items():
            if self.get_setting(k) is None:
                self.set_setting(k, v)

    def sync_with_config(self):
        """Searches for config.ini and loads settings into DB if found."""
        config = configparser.ConfigParser()
        
        # Locations: prioritizing system config then CWD then user config then script directory
        locations = self.config_locations or [
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
            print("⚠️ Warning: config.ini not found! Using database or basic defaults.", file=sys.stderr)
            if self.is_empty():
                self.load_defaults()
            return False
            
        print(f"📖 MATCHED CONFIG: {config_file}", file=sys.stderr)
        config.read(config_file)
        
        if 'slideshow' in config:
            # Pre-validate inky constraint from the file
            inky_enabled = config['slideshow'].get('enable_inky', 'False').lower() == 'true'
            interval = int(config['slideshow'].get('default_interval', '30'))
            
            # Note: We don't raise error here but adjust to be safe
            if inky_enabled and interval < 30:
                print("⚠️ Warning: Inky enabled with < 30s interval in config.ini. Adjusting to 30s.", file=sys.stderr)
                config['slideshow']['default_interval'] = '30'

            for key, value in config['slideshow'].items():
                self.set_setting(key, value)
            return True
        
        print("⚠️ Warning: [slideshow] section not found in config.ini!", file=sys.stderr)
        if self.is_empty():
            self.load_defaults()
        return False

    def _validate_inky_constraint(self):
        """Ensures default_interval is at least 30 if inky is enabled."""
        all_settings = self.get_all_settings()
        is_inky = all_settings.get('enable_inky', 'False').lower() == 'true'
        interval = int(all_settings.get('default_interval', '30'))

        if is_inky and interval < 30:
            print(f"⚠️ Boot-time Fix: Inky enabled with {interval}s interval. Correcting to 30s.", file=sys.stderr)
            self.set_setting('default_interval', '30')

    # ==================== Provider Settings ====================
    
    def get_provider_settings(self, provider_name: str) -> dict:
        """
        Get all settings for a specific provider.
        
        Args:
            provider_name: The unique provider identifier (e.g., "immich")
            
        Returns:
            Dictionary of provider-specific settings (without the prefix)
        """
        prefix = f"provider.{provider_name}."
        all_settings = self.get_all_settings()
        return {
            key[len(prefix):]: value 
            for key, value in all_settings.items() 
            if key.startswith(prefix)
        }
    
    def set_provider_setting(self, provider_name: str, key: str, value) -> None:
        """
        Set a provider-specific setting.
        
        Args:
            provider_name: The unique provider identifier
            key: The setting key (without provider prefix)
            value: The setting value
        """
        full_key = f"provider.{provider_name}.{key}"
        self.set_setting(full_key, value)
    
    def set_provider_settings(self, provider_name: str, settings: dict) -> None:
        """
        Set multiple provider settings at once.
        
        Args:
            provider_name: The unique provider identifier
            settings: Dictionary of key-value pairs to set
        """
        for key, value in settings.items():
            self.set_provider_setting(provider_name, key, value)
    
    def get_provider_last_sync(self, provider_name: str) -> dict:
        """
        Get the last sync result for a provider.
        
        Args:
            provider_name: The unique provider identifier
            
        Returns:
            Dictionary with last sync info or empty dict if never synced
        """
        import json
        result_json = self.get_setting(f"provider.{provider_name}._last_sync")
        if result_json:
            try:
                return json.loads(result_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_provider_last_sync(self, provider_name: str, result: dict) -> None:
        """
        Store the last sync result for a provider.
        
        Args:
            provider_name: The unique provider identifier
            result: Dictionary with sync result data
        """
        import json
        from datetime import datetime
        result["timestamp"] = datetime.utcnow().isoformat() + "Z"
        self.set_setting(f"provider.{provider_name}._last_sync", json.dumps(result))
