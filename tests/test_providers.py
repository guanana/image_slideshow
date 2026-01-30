"""
Unit tests for the provider system.

Tests the base provider interface, Immich provider, and registry functionality.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import tempfile
import shutil

# Add root folder to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from providers.base import (
    BaseImageProvider, 
    ConfigField, 
    RefreshResult, 
    RefreshStatus
)
from providers.immich import ImmichProvider


class TestRefreshResult(unittest.TestCase):
    """Tests for RefreshResult dataclass."""
    
    def test_to_dict(self):
        """RefreshResult should serialize to dictionary correctly."""
        result = RefreshResult(
            status=RefreshStatus.SUCCESS,
            message="Downloaded 10 images",
            downloaded=10,
            skipped=5,
            failed=0,
            total=15
        )
        
        data = result.to_dict()
        
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Downloaded 10 images")
        self.assertEqual(data["downloaded"], 10)
        self.assertEqual(data["skipped"], 5)
        self.assertEqual(data["failed"], 0)
        self.assertEqual(data["total"], 15)
        self.assertEqual(data["errors"], [])
    
    def test_default_errors_list(self):
        """Errors should default to empty list."""
        result = RefreshResult(status=RefreshStatus.SUCCESS, message="OK")
        self.assertEqual(result.errors, [])


class TestConfigField(unittest.TestCase):
    """Tests for ConfigField dataclass."""
    
    def test_to_dict_basic(self):
        """ConfigField should serialize basic fields."""
        field = ConfigField(
            key="server_url",
            label="Server URL",
            field_type="text",
            required=True,
            description="The server address"
        )
        
        data = field.to_dict()
        
        self.assertEqual(data["key"], "server_url")
        self.assertEqual(data["label"], "Server URL")
        self.assertEqual(data["type"], "text")
        self.assertTrue(data["required"])
        self.assertEqual(data["description"], "The server address")
    
    def test_to_dict_with_options(self):
        """ConfigField should include options for select type."""
        field = ConfigField(
            key="format",
            label="Format",
            field_type="select",
            options=[{"value": "jpg", "label": "JPEG"}, {"value": "png", "label": "PNG"}]
        )
        
        data = field.to_dict()
        
        self.assertIn("options", data)
        self.assertEqual(len(data["options"]), 2)


class TestImmichProvider(unittest.TestCase):
    """Tests for ImmichProvider implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.provider = ImmichProvider()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_name_and_display_name(self):
        """Provider should have correct identifiers."""
        self.assertEqual(self.provider.name, "immich")
        self.assertEqual(self.provider.display_name, "Immich")
    
    def test_get_config_fields(self):
        """Provider should return expected configuration fields."""
        fields = self.provider.get_config_fields()
        
        field_keys = [f.key for f in fields]
        self.assertIn("server_url", field_keys)
        self.assertIn("api_key", field_keys)
        self.assertIn("album_name", field_keys)
        self.assertIn("skip_existing", field_keys)
    
    def test_configure(self):
        """Provider should store configuration."""
        self.provider.configure({
            "server_url": "https://photos.example.com",
            "api_key": "test-api-key",
            "album_name": "Test Album"
        })
        
        config = self.provider.get_config()
        self.assertEqual(config["server_url"], "https://photos.example.com")
        self.assertNotEqual(config["api_key"], "test-api-key")  # Should be masked
        self.assertEqual(config["album_name"], "Test Album")
    
    def test_validate_config_missing_url(self):
        """Validation should fail without server URL."""
        self.provider.configure({"api_key": "test-key"})
        
        is_valid, error = self.provider.validate_config()
        
        self.assertFalse(is_valid)
        self.assertIn("Server URL", error)
    
    def test_validate_config_missing_key(self):
        """Validation should fail without API key."""
        self.provider.configure({"server_url": "https://photos.example.com"})
        
        is_valid, error = self.provider.validate_config()
        
        self.assertFalse(is_valid)
        self.assertIn("API Key", error)
    
    def test_validate_config_invalid_url(self):
        """Validation should fail with invalid URL scheme."""
        self.provider.configure({
            "server_url": "photos.example.com",
            "api_key": "test-key"
        })
        
        is_valid, error = self.provider.validate_config()
        
        self.assertFalse(is_valid)
        self.assertIn("http://", error)
    
    def test_validate_config_success(self):
        """Validation should pass with valid config."""
        self.provider.configure({
            "server_url": "https://photos.example.com",
            "api_key": "test-api-key"
        })
        
        is_valid, error = self.provider.validate_config()
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_get_config_schema(self):
        """get_config_schema should return list of dictionaries."""
        schema = self.provider.get_config_schema()
        
        self.assertIsInstance(schema, list)
        self.assertTrue(all(isinstance(item, dict) for item in schema))
        self.assertTrue(all("key" in item for item in schema))
    
    @patch('providers.immich.ImmichProvider._get_client')
    def test_test_connection_success(self, mock_get_client):
        """test_connection should return success when auth works."""
        mock_client = MagicMock()
        mock_client.check_auth.return_value = {"user": "test"}
        mock_get_client.return_value = mock_client
        
        self.provider.configure({
            "server_url": "https://photos.example.com",
            "api_key": "test-key"
        })
        
        success, message = self.provider.test_connection()
        
        self.assertTrue(success)
        self.assertIn("Connected", message)
    
    @patch('providers.immich.ImmichProvider._get_client')
    def test_test_connection_failure(self, mock_get_client):
        """test_connection should return failure when auth fails."""
        mock_client = MagicMock()
        mock_client.check_auth.return_value = None
        mock_get_client.return_value = mock_client
        
        self.provider.configure({
            "server_url": "https://photos.example.com",
            "api_key": "bad-key"
        })
        
        success, message = self.provider.test_connection()
        
        self.assertFalse(success)
        self.assertIn("Authentication failed", message)
    
    def test_test_connection_invalid_config(self):
        """test_connection should fail with invalid config."""
        # No configuration
        success, message = self.provider.test_connection()
        
        self.assertFalse(success)
        self.assertIn("Configuration error", message)
    
    @patch('providers.immich.ImmichProvider._get_client')
    def test_refresh_downloads_assets(self, mock_get_client):
        """refresh should download assets to target folder."""
        mock_client = MagicMock()
        mock_client.list_assets.return_value = [
            {"id": "asset-1", "originalFileName": "photo1.jpg"},
            {"id": "asset-2", "originalFileName": "photo2.jpg"},
        ]
        mock_get_client.return_value = mock_client
        
        self.provider.configure({
            "server_url": "https://photos.example.com",
            "api_key": "test-key"
        })
        
        result = self.provider.refresh(self.temp_dir)
        
        self.assertEqual(result.status, RefreshStatus.SUCCESS)
        self.assertEqual(result.downloaded, 2)
        self.assertEqual(mock_client.download_asset.call_count, 2)
    
    @patch('providers.immich.ImmichProvider._get_client')
    def test_refresh_skips_existing(self, mock_get_client):
        """refresh should skip existing files when skip_existing is True."""
        # Create an existing file
        existing_file = os.path.join(self.temp_dir, "photo1.jpg")
        with open(existing_file, 'w') as f:
            f.write("existing")
        
        mock_client = MagicMock()
        mock_client.list_assets.return_value = [
            {"id": "asset-1", "originalFileName": "photo1.jpg"},
            {"id": "asset-2", "originalFileName": "photo2.jpg"},
        ]
        mock_get_client.return_value = mock_client
        
        self.provider.configure({
            "server_url": "https://photos.example.com",
            "api_key": "test-key",
            "skip_existing": "True"
        })
        
        result = self.provider.refresh(self.temp_dir)
        
        self.assertEqual(result.downloaded, 1)
        self.assertEqual(result.skipped, 1)
    
    @patch('providers.immich.ImmichProvider._get_client')
    def test_refresh_from_album(self, mock_get_client):
        """refresh should download from specific album when configured."""
        mock_client = MagicMock()
        mock_client.find_album.return_value = {"id": "album-123", "albumName": "Vacation"}
        mock_client.get_album.return_value = {
            "id": "album-123",
            "assets": [{"id": "asset-1", "originalFileName": "beach.jpg"}]
        }
        mock_get_client.return_value = mock_client
        
        self.provider.configure({
            "server_url": "https://photos.example.com",
            "api_key": "test-key",
            "album_name": "Vacation"
        })
        
        result = self.provider.refresh(self.temp_dir)
        
        mock_client.find_album.assert_called_with("Vacation")
        self.assertEqual(result.downloaded, 1)
    
    def test_refresh_invalid_config(self):
        """refresh should fail with invalid config."""
        result = self.provider.refresh(self.temp_dir)
        
        self.assertEqual(result.status, RefreshStatus.FAILED)
        self.assertIn("Configuration error", result.message)
    
    @patch('providers.immich.ImmichProvider._get_client')
    def test_refresh_no_images(self, mock_get_client):
        """refresh should return NO_IMAGES when source is empty."""
        mock_client = MagicMock()
        mock_client.list_assets.return_value = []
        mock_get_client.return_value = mock_client
        
        self.provider.configure({
            "server_url": "https://photos.example.com",
            "api_key": "test-key"
        })
        
        result = self.provider.refresh(self.temp_dir)
        
        self.assertEqual(result.status, RefreshStatus.NO_IMAGES)


class TestProviderRegistry(unittest.TestCase):
    """Tests for provider registry functions."""
    
    def test_list_providers(self):
        """list_providers should return registered provider names."""
        from providers import list_providers
        
        names = list_providers()
        
        self.assertIn("immich", names)
    
    def test_get_provider(self):
        """get_provider should return provider instance."""
        from providers import get_provider
        
        provider = get_provider("immich")
        
        self.assertIsNotNone(provider)
        self.assertIsInstance(provider, ImmichProvider)
    
    def test_get_provider_unknown(self):
        """get_provider should return None for unknown provider."""
        from providers import get_provider
        
        provider = get_provider("nonexistent")
        
        self.assertIsNone(provider)
    
    def test_get_all_providers(self):
        """get_all_providers should return dict of all providers."""
        from providers import get_all_providers
        
        providers = get_all_providers()
        
        self.assertIn("immich", providers)
        self.assertIsInstance(providers["immich"], ImmichProvider)


if __name__ == "__main__":
    unittest.main()
