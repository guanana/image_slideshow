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

## 🍓 Raspberry Pi Deployment
Installation is the same as above. The `setup.sh` script will ask if you want to enable a **systemd service** to start the slideshow automatically when the Pi boots.

## 🧪 Testing
Run `./run_tests.sh` to access the test menu.
