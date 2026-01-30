"""
Immich Image Provider

Integrates with Immich photo management server to download images
for the slideshow application.
"""

import os
from typing import Dict, Any, List, Optional, Tuple

from .base import BaseImageProvider, ConfigField, RefreshResult, RefreshStatus


class ImmichProvider(BaseImageProvider):
    """
    Provider for downloading images from an Immich server.
    
    Uses the immich-lib package from PyPI to communicate with the Immich API.
    Supports downloading from a specific album or all assets.
    """
    
    name = "immich"
    display_name = "Immich"
    description = "Download images from your Immich photo management server"
    
    def __init__(self):
        super().__init__()
        self._client = None
    
    def get_config_fields(self) -> List[ConfigField]:
        """Return configuration fields for Immich provider."""
        return [
            ConfigField(
                key="server_url",
                label="Server URL",
                field_type="text",
                required=True,
                description="Full URL to your Immich server (e.g., https://photos.example.com)",
            ),
            ConfigField(
                key="api_key",
                label="API Key",
                field_type="password",
                required=True,
                description="Your Immich API key (generate in Immich Account Settings)",
            ),
            ConfigField(
                key="album_name",
                label="Album Name",
                field_type="text",
                required=False,
                default="",
                description="Specific album to download (leave empty for all assets)",
            ),
            ConfigField(
                key="skip_existing",
                label="Skip Existing Files",
                field_type="boolean",
                required=False,
                default=True,
                description="Skip downloading files that already exist locally",
            ),
        ]
    
    def configure(self, settings: Dict[str, Any]) -> None:
        """Apply configuration settings."""
        self._config = {
            "server_url": settings.get("server_url", "").rstrip("/"),
            "api_key": settings.get("api_key", ""),
            "album_name": settings.get("album_name", ""),
            "skip_existing": str(settings.get("skip_existing", "True")).lower() == "true",
        }
        # Reset client when config changes
        self._client = None
    
    def validate_config(self) -> Tuple[bool, Optional[str]]:
        """Validate the current configuration."""
        if not self._config.get("server_url"):
            return False, "Server URL is required"
        
        if not self._config.get("api_key"):
            return False, "API Key is required"
        
        server_url = self._config["server_url"]
        if not (server_url.startswith("http://") or server_url.startswith("https://")):
            return False, "Server URL must start with http:// or https://"
        
        return True, None
    
    def _get_client(self):
        """Get or create the Immich client."""
        if self._client is None:
            try:
                from immich_lib.client import ImmichClient
                self._client = ImmichClient(
                    self._config["server_url"],
                    self._config["api_key"]
                )
            except ImportError:
                raise ImportError(
                    "immich-lib package is not installed. "
                    "Install it with: pip install immich-lib"
                )
        return self._client
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to the Immich server."""
        is_valid, error = self.validate_config()
        if not is_valid:
            return False, f"Configuration error: {error}"
        
        try:
            client = self._get_client()
            auth_info = client.check_auth()
            
            if auth_info:
                return True, f"Connected successfully to Immich"
            else:
                return False, "Authentication failed - check your API key"
                
        except ImportError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def refresh(self, target_folder: str) -> RefreshResult:
        """Download images from Immich to the target folder."""
        is_valid, error = self.validate_config()
        if not is_valid:
            result = RefreshResult(
                status=RefreshStatus.FAILED,
                message=f"Configuration error: {error}"
            )
            self._last_result = result
            return result
        
        try:
            client = self._get_client()
        except ImportError as e:
            result = RefreshResult(
                status=RefreshStatus.FAILED,
                message=str(e)
            )
            self._last_result = result
            return result
        
        # Ensure target folder exists
        os.makedirs(target_folder, exist_ok=True)
        
        try:
            assets = self._get_assets(client)
        except Exception as e:
            result = RefreshResult(
                status=RefreshStatus.FAILED,
                message=f"Failed to fetch assets: {str(e)}"
            )
            self._last_result = result
            return result
        
        if not assets:
            result = RefreshResult(
                status=RefreshStatus.NO_IMAGES,
                message="No images found in the specified source",
                total=0
            )
            self._last_result = result
            return result
        
        # Download assets
        downloaded = 0
        skipped = 0
        failed = 0
        errors = []
        skip_existing = self._config.get("skip_existing", True)
        
        for asset in assets:
            asset_id = asset.get("id")
            filename = asset.get("originalFileName", f"{asset_id}.jpg")
            output_path = os.path.join(target_folder, filename)
            
            # Skip if file exists and skip_existing is enabled
            if skip_existing and os.path.exists(output_path):
                skipped += 1
                continue
            
            try:
                client.download_asset(asset_id, output_path)
                downloaded += 1
            except Exception as e:
                failed += 1
                errors.append(f"Failed to download {filename}: {str(e)}")
        
        # Determine overall status
        total = len(assets)
        if failed == 0:
            status = RefreshStatus.SUCCESS
            message = f"Successfully downloaded {downloaded} images ({skipped} skipped)"
        elif downloaded > 0:
            status = RefreshStatus.PARTIAL
            message = f"Downloaded {downloaded} images, {failed} failed, {skipped} skipped"
        else:
            status = RefreshStatus.FAILED
            message = f"All {failed} downloads failed"
        
        result = RefreshResult(
            status=status,
            message=message,
            downloaded=downloaded,
            skipped=skipped,
            failed=failed,
            total=total,
            errors=errors[:10]  # Limit error messages
        )
        self._last_result = result
        return result
    
    def _get_assets(self, client) -> List[Dict[str, Any]]:
        """Fetch assets from Immich, optionally filtered by album."""
        album_name = self._config.get("album_name", "").strip()
        
        if album_name:
            # Find album by name
            album = client.find_album(album_name)
            if not album:
                raise ValueError(f"Album '{album_name}' not found")
            
            # Get album details with assets
            album_detail = client.get_album(album["id"])
            if not album_detail:
                raise ValueError(f"Could not retrieve album details")
            
            return album_detail.get("assets", [])
        else:
            # Get all assets
            return client.list_assets() or []
    
    def get_config(self) -> Dict[str, Any]:
        """Get current config, masking the API key."""
        config = self._config.copy()
        if config.get("api_key"):
            # Mask API key for display
            key = config["api_key"]
            config["api_key"] = key[:8] + "..." + key[-4:] if len(key) > 12 else "****"
        return config
