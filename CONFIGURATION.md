# Configuration Management

This document explains how the Image Slideshow application handles its configuration, the priority of different configuration sources, and how to update settings dynamically.

## Configuration Loading Priorities

The application uses a hierarchical approach to find its configuration. It will use the **first** `config.ini` file it finds in the following order:

1.  **/etc/slideshow/config.ini** (System-wide configuration)
2.  **./config.ini** (Current working directory)
3.  **~/.config/simple-image-slideshow/config.ini** (User-specific configuration)
4.  **[script_directory]/config.ini** (Built-in or development configuration)

### Fallback Mechanism

-   **Database**: If no `config.ini` file is found, the application will use the settings previously stored in the database (`/etc/slideshow/config.db`).
-   **Defaults**: If both the configuration file and the database are missing/empty, the application will load a set of built-in safe defaults.

---

## How to Change Configuration

### 1. Modifying Configuration Files
You can edit any of the `config.ini` files listed in the [Priorities](#configuration-loading-priorities) section. The application expects a `[slideshow]` section:

```ini
[slideshow]
background_color = black
default_interval = 8
start_fullscreen = True
enable_manual_controls = True
image_extensions = .jpg,.jpeg,.png,.gif,.bmp,.webp
enable_inky = False
```

### Configuration Parameters
- **background_color**: Canvas color behind images (e.g. `black`, `#112233`).
- **default_interval**: Time in seconds between image rotations. *Note: Must be at least 30s if Inky is enabled.*
- **start_fullscreen**: Whether to launch in fullscreen mode (`True`/`False`).
- **enable_manual_controls**: Enable arrow key navigation (`True`/`False`).
- **image_extensions**: Comma-separated list of supported file types.
- **enable_inky**: Enable support for Inky e-paper displays (`True`/`False`). Default is `False`. *Note: Requires interval >= 30s.*

### 2. Updating via the API (On the fly)
The application runs a FastAPI server (by default on port 8080) that allows you to change settings without restarting the app.

#### A. Update Specific Settings
You can send a JSON object with the settings you want to change to the `/config` endpoint.

**Example using `curl`:**
```bash
curl -X POST http://localhost:8080/config \
     -H "Content-Type: application/json" \
     -d '{"background_color": "darkblue", "default_interval": "10"}'
```

#### B. Sync from `config.ini`
If you have modified a physical `config.ini` file and want the running application to pick up the changes immediately, use the `/config/sync` endpoint.

**Example using `curl`:**
```bash
curl -X POST http://localhost:8080/config/sync
```

### 3. Web Dashboard (Visual Control Hub)
A beautiful, real-time dashboard is available at the root URL of the API.

-   **Access**: Open `http://localhost:8080/` in your browser.
-   **Features**:
    -   View all current configuration values in a sleek grid.
    -   Refresh settings manually.
    -   Trigger a synchronization with `config.ini` with one click.
    -   Real-time system status indicators.

---

## Technical Details
-   **Synchronization**: When the `/config/sync` endpoint is called or when the application starts, it performs an "INSERT OR REPLACE" into the SQLite database.
-   **Live Updates**: The slideshow application polls the database every 5 seconds for changes to `background_color`, `default_interval`, and other visual settings, ensuring that API changes take effect almost immediately.
