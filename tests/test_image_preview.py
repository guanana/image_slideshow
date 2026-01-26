import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Add root folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create a mock for Database so api.py doesn't try to access real DB on import
mock_db_instance = MagicMock()
with patch('database.Database', return_value=mock_db_instance):
    from api import app

client = TestClient(app)

class TestImagePreview(unittest.TestCase):
    
    def test_current_image_not_set(self):
        # Clear state
        if hasattr(app.state, 'slideshow'):
            delattr(app.state, 'slideshow')
            
        response = client.get("/current-image")
        self.assertEqual(response.status_code, 404)
        self.assertIn("No image currently displayed", response.json()["detail"])

    def test_current_image_success(self):
        # Create a real dummy file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"fake data")
            tmp_path = tmp.name

        try:
            # Mock slideshow app
            mock_slideshow = MagicMock()
            mock_slideshow.current_photo_path = tmp_path
            app.state.slideshow = mock_slideshow
            
            response = client.get("/current-image")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["content-type"], "image/jpeg")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            
    def test_current_image_file_missing(self):
        mock_slideshow = MagicMock()
        mock_slideshow.current_photo_path = "/tmp/non_existent.jpg"
        app.state.slideshow = mock_slideshow
        
        with patch('os.path.exists', return_value=False):
            response = client.get("/current-image")
            self.assertEqual(response.status_code, 404)

if __name__ == "__main__":
    unittest.main()
