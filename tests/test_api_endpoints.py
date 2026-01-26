import os
import sys
import unittest
from unittest.mock import MagicMock, patch, mock_open

# Add root folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create a mock for Database so api.py doesn't try to access real DB/files on import
mock_db_instance = MagicMock()
with patch('database.Database', return_value=mock_db_instance):
    import api

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        # Reset mock before each test completely
        mock_db_instance.reset_mock()
        mock_db_instance.sync_with_config.side_effect = None
        mock_db_instance.sync_with_config.return_value = MagicMock() # default
        mock_db_instance.get_all_settings.side_effect = None
        mock_db_instance.set_setting.side_effect = None

    @patch('api.db', mock_db_instance)
    def test_sync_config_success(self):
        mock_db_instance.sync_with_config.return_value = True
        response = api.sync_config()
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["message"], "Configuration synced from config.ini")
        mock_db_instance.sync_with_config.assert_called_once()

    @patch('api.db', mock_db_instance)
    def test_sync_config_warning(self):
        mock_db_instance.sync_with_config.return_value = False
        response = api.sync_config()
        self.assertEqual(response["status"], "warning")
        self.assertIn("not found or invalid", response["message"])
        mock_db_instance.sync_with_config.assert_called_once()

    @patch('api.db', mock_db_instance)
    def test_sync_config_error(self):
        mock_db_instance.sync_with_config.side_effect = Exception("DB Error")
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as cm:
            api.sync_config()
        self.assertEqual(cm.exception.status_code, 500)
        self.assertEqual(cm.exception.detail, "DB Error")

    @patch('api.db', mock_db_instance)
    def test_get_config(self):
        mock_db_instance.get_all_settings.return_value = {"key": "value"}
        response = api.get_config()
        self.assertEqual(response, {"key": "value"})
        mock_db_instance.get_all_settings.assert_called_once()

    @patch('api.db', mock_db_instance)
    def test_update_config(self):
        response = api.update_config({"test_key": "test_value"})
        self.assertEqual(response["status"], "ok")
        mock_db_instance.set_setting.assert_called_with("test_key", "test_value")

    @patch('api.open', new_callable=mock_open, read_data="<html>Dashboard</html>")
    @patch('os.path.exists', return_value=True)
    def test_dashboard_success(self, mock_exists, mock_file):
        response = api.dashboard()
        self.assertEqual(response, "<html>Dashboard</html>")

    @patch('api.open', side_effect=Exception("File not found"))
    def test_dashboard_error(self, mock_file):
        response = api.dashboard()
        self.assertIn("Error loading dashboard", response)
        self.assertIn("File not found", response)

    @patch('api.db', mock_db_instance)
    def test_update_config_inky_validation_fail(self):
        from fastapi import HTTPException
        mock_db_instance.get_all_settings.return_value = {"enable_inky": "False", "default_interval": "5"}
        
        # Should fail if trying to enable inky with existing small interval
        with self.assertRaises(HTTPException) as cm:
            api.update_config({"enable_inky": "True"})
        self.assertEqual(cm.exception.status_code, 400)
        self.assertIn("at least 30 seconds", cm.exception.detail)

    @patch('api.db', mock_db_instance)
    def test_update_config_inky_validation_success(self):
        mock_db_instance.get_all_settings.return_value = {"enable_inky": "False", "default_interval": "60"}
        
        response = api.update_config({"enable_inky": "True"})
        self.assertEqual(response["status"], "ok")

if __name__ == "__main__":
    unittest.main()
