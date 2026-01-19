from PIL import Image, ImageDraw, ImageFont
import os

def create_test_images():
    # Create directory in test_images relative to this script
    # Note: The instruction mentioned 'tests/test_images' but the provided code edit
    # only creates 'test_images' relative to the script's directory.
    # Sticking to the provided code edit's logic for the path.
    script_dir = os.path.dirname(__file__)
    test_dir = os.path.join(script_dir, 'test_images')
    
    os.makedirs(test_dir, exist_ok=True)
    
    colors = ['red', 'green', 'blue', 'yellow', 'purple']
    
    for i, color in enumerate(colors):
        # Create a simple colored image with text
        img = Image.new('RGB', (800, 600), color=color)
        d = ImageDraw.Draw(img)
        d.text((350, 280), f"Image {i+1}", fill="white")
        img.save(os.path.join(test_dir, f'img_{i+1}.png'))
    
    print(f"Test images created in {test_dir}")

if __name__ == "__main__":
    create_test_images()
