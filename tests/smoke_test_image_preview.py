import os
import sys
import time
import threading
import uvicorn
import httpx
from PIL import Image
from tempfile import TemporaryDirectory

# Add root folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api import app
from slideshow import SlideshowApp
from database import Database

def run_smoke_test():
    print("🚀 Starting Image Preview Smoke Test...")
    
    with TemporaryDirectory() as tmp_dir:
        # 1. Create a dummy image
        img_path = os.path.join(tmp_dir, "test.jpg")
        img = Image.new('RGB', (100, 100), color='red')
        img.save(img_path)
        print(f"✅ Created dummy image at {img_path}")

        # 2. Mock Database
        db_path = os.path.join(tmp_dir, "test.db")
        db = Database(db_path=db_path)
        
        # 3. Setup Slideshow (Mocking Tkinter root to avoid window opening if possible, but Slideshow needs it)
        # We'll just manually set the state instead of running fully
        mock_app = type('obj', (object,), {
            'current_photo_path': img_path
        })
        app.state.slideshow = mock_app
        print("✅ Mocked application state with current image")

        # 4. Test the API directly using a client (instead of starting server for speed/stability)
        print("🧪 Testing API endpoint...")
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        response = client.get("/current-image")
        if response.status_code == 200:
            print("✅ API returned 200 OK")
            # Verify it's actually an image
            if 'image/' in response.headers.get('content-type', ''):
                print(f"✅ Content-Type is valid: {response.headers['content-type']}")
            else:
                print(f"❌ Unexpected Content-Type: {response.headers.get('content-type')}")
                return False
        else:
            print(f"❌ API failed with status {response.status_code}: {response.text}")
            return False

        print("✨ Smoke Test Passed!")
        return True

if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
