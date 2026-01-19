import sqlite3
import os
import threading

class Database:
    def __init__(self, db_path="/etc/slideshow/config.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

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
