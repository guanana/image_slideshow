#!/usr/bin/env python3
import tkinter as tk
import os
import sys
import time

# Add root folder to path to import slideshow
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from slideshow import SlideshowApp

class MockDB:
    def __init__(self, initial_settings=None):
        self.settings = initial_settings or {}
        
    def get_setting(self, key, default=None):
        return self.settings.get(key, default)
        
    def set_setting(self, key, value):
        self.settings[key] = value

def main():
    print("▶ Starting Smoke Test (Verification)...")
    
    # Check for test images
    test_images = os.path.join(os.path.dirname(__file__), 'test_images')
    if not os.path.isdir(test_images):
        print("🔧 Creating test images for verification...")
        try:
            import create_test_images
            create_test_images.main()
        except ImportError:
            # Fallback if import fails
            os.system(f"{sys.executable} {os.path.join(os.path.dirname(__file__), 'create_test_images.py')}")

    root = tk.Tk()
    root.title("Verification Test")
    root.geometry("600x400")
    
    # Use a simpler setup for the test
    label = tk.Label(root, text="🚀 Installation Verified!\nClosing in 5 seconds...", 
                    font=("Arial", 16, "bold"), pady=20)
    label.pack()
    
    try:
        # Mock DB with minimal config
        mock_db = MockDB({
            'background_color': 'black',
            'enable_manual_controls': 'True'
        })

        app = SlideshowApp(
            root, 
            test_images, 
            interval=2, 
            fullscreen=False,
            db=mock_db
        )
        
        print("✓ GUI initialized successfully")
        
        # Auto-exit after 5 seconds
        root.after(5000, root.quit)
        root.mainloop()
        print("✓ Smoke test completed successfully")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Smoke test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
