#!/bin/bash
# Unified Image Slideshow Setup Script

# Exit on error
set -e

SHOW_HELP=false
ENABLE_BOOT=false
SKIP_TEST=false
UNINSTALL=false

# Get absolute path of the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Simple argument parsing
for arg in "$@"; do
  case $arg in
    -h|--help)
      SHOW_HELP=true
      shift
      ;;
    -b|--boot)
      ENABLE_BOOT=true
      shift
      ;;
    -t|--skip-test)
      SKIP_TEST=true
      shift
      ;;
    -u|--uninstall)
      UNINSTALL=true
      shift
      ;;
  esac
done

if [ "$SHOW_HELP" = true ]; then
    echo "Usage: ./setup.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help        Show this help message"
    echo "  -b, --boot        Automatically enable startup on boot"
    echo "  -t, --skip-test   Skip the post-installation GUI verification test"
    echo "  -u, --uninstall   Revert boot startup and uninstall the service"
    echo ""
    echo "If no options are provided, the script installs the app and runs a quick verification test."
    exit 0
fi

SERVICE_NAME="slideshow.service"
# Using user-level systemd service
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_PATH="$SERVICE_DIR/$SERVICE_NAME"
CONFIG_DIR="/etc/slideshow"

# --- UNINSTALL LOGIC ---
if [ "$UNINSTALL" = true ]; then
    echo "🗑️ Reverting boot startup configuration..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ -f "$SERVICE_PATH" ]; then
        echo "🛑 Stopping and disabling service..."
        systemctl --user stop "$SERVICE_NAME" || true
        systemctl --user disable "$SERVICE_NAME" || true
        
        echo "📂 Removing service file..."
        rm "$SERVICE_PATH"
        
        echo "🔄 Reloading systemd..."
        systemctl --user daemon-reload
        echo "✅ Startup service removed successfully."
    else
        echo "ℹ️ No startup service found to remove."
    fi

    # Legacy Cleanup (System Service)
    if [ -f "/etc/systemd/system/$SERVICE_NAME" ]; then
        echo "🧹 Removing legacy system service..."
        sudo systemctl stop "$SERVICE_NAME" || true
        sudo systemctl disable "$SERVICE_NAME" || true
        sudo rm "/etc/systemd/system/$SERVICE_NAME"
        sudo systemctl daemon-reload
    fi

    if [ -d "$CONFIG_DIR" ]; then
        echo "🗑️ Removing system configuration directory (sudo)..."
        # Optional: Ask user if they want to keep images? For now, we remove config dir but maybe keep images?
        # The user asked for /etc/slideshow/images, which is inside /etc/slideshow.
        # Removing /etc/slideshow will remove images too.
        sudo rm -rf "$CONFIG_DIR"
    fi
     
    DESKTOP_FILE="$HOME/Desktop/Slideshow.desktop"
    if [ -f "$DESKTOP_FILE" ]; then
        echo "🗑️ Removing desktop shortcut..."
        rm "$DESKTOP_FILE"
    fi
    
    echo "🐍 Removing application tool..."
    uv tool uninstall simple-image-slideshow || true
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✨ Cleanup finished!"
    exit 0
fi

# --- INSTALL LOGIC ---
echo "🚀 Starting Image Slideshow Unified Setup..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Install System Dependencies
echo "📦 Installing system dependencies (sudo required)..."
sudo apt update
sudo apt install -y python3-tk python3-pil.imagetk curl

# 2. Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv (modern Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source for current session
    if [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    fi
fi

# 3. Resolve uv path
UV_BIN=$(which uv)
if [ -z "$UV_BIN" ]; then
    echo "❌ Error: uv could not be found even after installation attempt."
    exit 1
fi
echo "✅ Using uv at: $UV_BIN"

# Sync dependencies to ensure fastapi/uvicorn are installed
echo "📦 Syncing Python environment..."
$UV_BIN sync

# Note: We are using 'uv run' so no need for 'uv tool install'
echo "ℹ️  Application will run directly from source using 'uv run'."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 4. Verification Test
if [ "$SKIP_TEST" = false ]; then
    echo "🧪 Running verification test (GUI smoke test)..."
    echo "   (A window will open briefly to confirm everything is working)"
    if ! python3 tests/smoke_test.py; then
        echo "⚠️ Warning: Verification test encountered an issue."
        echo "   Make sure you are in a graphical environment (X11/Wayland)."
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

# 5. Startup Setup
if [ "$ENABLE_BOOT" = true ]; then
    echo "⚙️ Setting up automatic startup service (-b flag detected)..."
    
    mkdir -p "$SERVICE_DIR"
    
    # System Config Setup
    echo "⚙️ Setting up global configuration in /etc/slideshow (sudo required)..."
    if [ ! -d "$CONFIG_DIR" ]; then
        sudo mkdir -p "$CONFIG_DIR"
    fi

    # Create default image directory
    IMAGES_DIR="/etc/slideshow/images"
    if [ ! -d "$IMAGES_DIR" ]; then
        echo "📂 Creating default image directory: $IMAGES_DIR"
        sudo mkdir -p "$IMAGES_DIR"
        # Make it writable by everyone for now so user can add images, or at least readable
        sudo chmod 777 "$IMAGES_DIR"
    fi

    # Ensure config directory is writable by user for DB creation
    echo "🔐 Adjusting permissions for database creation..."
    sudo chmod 777 "$CONFIG_DIR"

    # Copy config if not present
    if [ ! -f "$CONFIG_DIR/config.ini" ]; then
        echo "📂 Copying default configuration..."
        if [ -f "config.ini" ]; then
             sudo cp config.ini "$CONFIG_DIR/config.ini"
             # Ensure readable by all
             sudo chmod 644 "$CONFIG_DIR/config.ini"
        else
             echo "⚠️ Warning: config.ini not found in current directory."
        fi
    fi

    # Create service file from template
    if [ -f "$PROJECT_DIR/slideshow.service.template" ]; then
        sed "s|{{WORKDIR}}|$PROJECT_DIR|g; s|{{UV_BIN}}|$UV_BIN|g" \
            "$PROJECT_DIR/slideshow.service.template" > "$SERVICE_PATH"
        echo "✅ Service file created from template at $SERVICE_PATH"
    else
        echo "❌ Error: slideshow.service.template not found!"
        exit 1
    fi

    echo "🔄 Enabling service..."
    systemctl --user daemon-reload
    systemctl --user enable "$SERVICE_NAME"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Desktop Shortcut
    echo "🖥️ Creating Desktop Shortcut..."
    DESKTOP_PATH="$HOME/Desktop/Slideshow.desktop"
    
    cat <<EOF > "$DESKTOP_PATH"
[Desktop Entry]
Name=Image Slideshow
Comment=Start the Image Slideshow
Exec=$UV_BIN run --directory $PROJECT_DIR python main.py
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;Application;
EOF
    
    chmod +x "$DESKTOP_PATH"
    echo "✅ Desktop shortcut created at $DESKTOP_PATH"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Startup setup complete!"
    echo "The slideshow will start automatically on next boot."
fi

echo "🎉 Setup Finished! Enjoy your slideshow."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Usage tips:"
echo "  - Run manually: slideshow-app"
echo "  - Edit settings: nano config.ini"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
