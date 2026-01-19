import os
import sys

# Add root folder to path to import slideshow
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_config():
    import configparser
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
    if not os.path.exists(config_path):
        print("❌ Config not found")
        return False
    config.read(config_path)
    print("✓ Config loaded")
    return "slideshow" in config

def test_images():
    test_dir = os.path.join(os.path.dirname(__file__), 'test_images')
    if not os.path.isdir(test_dir):
        print("❌ test_images not found")
        return False
    imgs = [f for f in os.listdir(test_dir) if f.endswith(('.png', '.jpg'))]
    print(f"✓ Found {len(imgs)} images")
    return len(imgs) > 0

if __name__ == "__main__":
    results = [test_config(), test_images()]
    if all(results):
        print("✓ All tests passed")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
