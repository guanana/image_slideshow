# Image Slideshow

A simple, robust Python image slideshow that covers the whole screen while maintaining aspect ratio (never crops).

## 🚀 Quick Start

1. **Run the Setup Script**:
   ```bash
   bash setup.sh
   ```
   *Options:*
   - `-b, --boot`: Automatically enable startup on boot (no prompt).
   - `-t, --skip-test`: Skip the post-installation GUI verification test.
   - `-u, --uninstall`: Revert boot startup and uninstall the service.
   - `-h, --help`: Show help and exit.

2. **Run manually**:
   ```bash
   slideshow-app
   ```

## ⌨️ Controls
- **F**: Toggle Fullscreen
- **Esc**: Exit Fullscreen
- **Q**: Quit
- **Right Arrow**: Next image (if enabled in config)
- **Left Arrow**: Previous image (if enabled in config)

## ⚙️ Configuration
Edit `config.ini` to change defaults:
- `default_folder`: Folder to scan for images (defaults to `~/Pictures`).
- `default_interval`: Seconds between images.
- `background_color`: Background color for images.
- `enable_manual_controls`: Enable arrow key navigation.

See [CONFIGURATION.md](CONFIGURATION.md) for detailed configuration options.

## 📥 Image Sources (Providers)

The slideshow supports **external image source providers** — a modular plugin system that allows you to automatically download images from remote services directly to your slideshow folder.

### Built-in Providers

| Provider | Description |
|----------|-------------|
| **Immich** | Download images from your [Immich](https://immich.app/) photo server |

### Using Providers via Dashboard

1. Open the web dashboard at `http://<device-ip>:8080`
2. Scroll to the **Image Sources** section
3. Click **Configure** on a provider to enter credentials
4. Click **Test** to verify the connection
5. Click **Refresh Images** to download photos to your slideshow folder

Provider settings (including credentials) are stored in the local SQLite database.

> ⚠️ **Immich API Key Permissions**
>
> If your Immich server uses granular permissions for API keys, ensure your key has the following enabled:
> - `album.read`: To fetch the list of available albums.
> - `asset.read`: To retrieve photo metadata.
> - `asset.download`: To download the high-resolution photos.
>
> Alternatively, you can use a key with the `all` permission(better not!).

### Adding Custom Providers

To add support for another image source (e.g., Google Photos, Dropbox), create a new provider class:

```python
# providers/my_provider.py
from .base import BaseImageProvider, ConfigField, RefreshResult, RefreshStatus
from . import register_provider

@register_provider
class MyProvider(BaseImageProvider):
    name = "my_provider"           # Unique identifier
    display_name = "My Provider"   # Shown in dashboard
    description = "Download images from My Service"
    
    def get_config_fields(self):
        return [
            ConfigField(key="api_key", label="API Key", field_type="password", required=True),
            # Add more fields as needed
        ]
    
    def configure(self, settings):
        self._config = settings
    
    def validate_config(self):
        if not self._config.get("api_key"):
            return False, "API Key is required"
        return True, None
    
    def test_connection(self):
        # Test connection to your service
        return True, "Connected successfully"
    
    def refresh(self, target_folder):
        # Download images to target_folder
        # Return RefreshResult with statistics
        return RefreshResult(
            status=RefreshStatus.SUCCESS,
            message="Downloaded 10 images",
            downloaded=10, total=10
        )
```

The provider will automatically appear in the dashboard once registered.

## 🌐 Web Dashboard & API

The application exposes a REST API on port **8080**:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web dashboard |
| `/config` | GET/POST | View or update slideshow settings |
| `/providers` | GET | List all image source providers |
| `/providers/{name}/config` | GET/POST | View or update provider settings |
| `/providers/{name}/test` | POST | Test provider connection |
| `/providers/{name}/refresh` | POST | Trigger image download |
| `/current-image` | GET | Get currently displayed image |
| `/restart` | POST | Restart the application |

## 🍓 Raspberry Pi Deployment
Installation is the same as above. The `setup.sh` script will ask if you want to enable a **systemd service** to start the slideshow automatically when the Pi boots.

## 🧪 Testing
Run `./run_tests.sh` to access the test menu.

## 📁 Project Structure

```
image_slideshow/
├── main.py              # Application entry point
├── slideshow.py         # Tkinter slideshow GUI
├── api.py               # FastAPI REST endpoints
├── database.py          # SQLite configuration storage
├── dashboard.html       # Web dashboard UI
├── providers/           # Image source provider plugins
│   ├── __init__.py      # Provider registry
│   ├── base.py          # Abstract base class
│   └── immich.py        # Immich provider implementation
└── tests/               # Unit and integration tests
```

