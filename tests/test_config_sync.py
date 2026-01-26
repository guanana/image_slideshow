import os
import sys
import unittest
import sqlite3
import configparser
import tempfile
import shutil

# Add root folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database import Database

class TestConfigSync(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_config.db")
        self.config_path = os.path.join(self.test_dir, "config.ini")
        
        # Change CWD so Database finds the local config.ini
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)

    def test_initial_sync_with_config(self):
        # Create a dummy config.ini
        with open(self.config_path, "w") as f:
            f.write("[slideshow]\n")
            f.write("background_color = blue\n")
            f.write("default_interval = 10\n")

        db = Database(self.db_path, config_locations=[self.config_path])
        
        self.assertEqual(db.get_setting("background_color"), "blue")
        self.assertEqual(db.get_setting("default_interval"), "10")

    def test_sync_no_config_uses_defaults(self):
        # No config.ini exists in self.test_dir
        db = Database(self.db_path, config_locations=[self.config_path])
        
        # Should have loaded defaults
        self.assertEqual(db.get_setting("background_color"), "black")
        self.assertEqual(db.get_setting("default_interval"), "5")

    def test_manual_sync_after_file_change(self):
        # Initial config
        with open(self.config_path, "w") as f:
            f.write("[slideshow]\n")
            f.write("background_color = red\n")
        
        db = Database(self.db_path, config_locations=[self.config_path])
        self.assertEqual(db.get_setting("background_color"), "red")

        # Update config file
        with open(self.config_path, "w") as f:
            f.write("[slideshow]\n")
            f.write("background_color = green\n")
        
        # DB shouldn't change yet
        self.assertEqual(db.get_setting("background_color"), "red")
        
        # Manual sync
        db.sync_with_config()
        self.assertEqual(db.get_setting("background_color"), "green")

if __name__ == "__main__":
    unittest.main()
