#!/usr/bin/env python3
"""
GUI Test for Image Slideshow Application

This test runs the slideshow in GUI mode with automated interactions.
You can watch the slideshow run and see automated testing in action.
"""

import tkinter as tk
import sys
import os
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from slideshow import SlideshowApp

class GUITester:
    """Automated GUI tester for the slideshow application."""
    
    def __init__(self):
        self.root = None
        self.app = None
        self.test_results = []
        self.current_test = 0
        self.tests = [
            ("Starting slideshow in windowed mode", self.test_windowed_mode),
            ("Verifying image display", self.test_image_display),
            ("Testing image rotation", self.test_image_rotation),
            ("Testing fullscreen toggle", self.test_fullscreen_toggle),
            ("Testing keyboard controls", self.test_keyboard_controls),
            ("Completing test suite", self.finish_tests)
        ]
    
    def log(self, message, status="INFO"):
        """Log test messages."""
        timestamp = time.strftime("%H:%M:%S")
        symbols = {"INFO": "ℹ", "PASS": "✓", "FAIL": "✗", "TEST": "▶"}
        symbol = symbols.get(status, "•")
        print(f"[{timestamp}] {symbol} {message}")
    
    def test_windowed_mode(self):
        """Test 1: Start in windowed mode."""
        self.log("Test 1: Starting slideshow in windowed mode", "TEST")
        
        self.root = tk.Tk()
        self.root.geometry("800x600")
        
        # Load config
        import configparser
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
        config.read(config_path)
        
        test_images_path = os.path.join(os.path.dirname(__file__), 'test_images')
        
        # Create app in windowed mode
        self.app = SlideshowApp(
            self.root, 
            test_images_path, 
            interval=2, 
            fullscreen=False,
            config=config['slideshow'] if 'slideshow' in config else {}
        )
        
        # Add test status label
        self.status_label = tk.Label(
            self.root, 
            text="GUI Test Running - Test 1/6: Windowed Mode",
            bg="yellow",
            fg="black",
            font=("Arial", 12, "bold"),
            pady=10
        )
        self.status_label.pack(side=tk.TOP, fill=tk.X)
        
        self.log("Slideshow started in windowed mode", "PASS")
        self.test_results.append(("Windowed mode", True))
        
        # Schedule next test
        self.root.after(3000, self.run_next_test)
    
    def test_image_display(self):
        """Test 2: Verify images are displaying."""
        self.log("Test 2: Verifying image display", "TEST")
        self.update_status("Test 2/6: Verifying Image Display")
        
        if self.app.photo_image is not None:
            self.log("Image is displayed correctly", "PASS")
            self.test_results.append(("Image display", True))
        else:
            self.log("No image displayed", "FAIL")
            self.test_results.append(("Image display", False))
        
        # Schedule next test
        self.root.after(3000, self.run_next_test)
    
    def test_image_rotation(self):
        """Test 3: Test automatic image rotation."""
        self.log("Test 3: Testing image rotation (waiting for next image)", "TEST")
        self.update_status("Test 3/6: Testing Image Rotation")
        
        # Get current image index
        initial_index = self.app.current_image_index
        self.log(f"Current image index: {initial_index}")
        
        # Wait for rotation (2 second interval + buffer)
        def check_rotation():
            new_index = self.app.current_image_index
            if new_index != initial_index or len(self.app.images) == 1:
                self.log(f"Image rotated to index: {new_index}", "PASS")
                self.test_results.append(("Image rotation", True))
            else:
                self.log("Image did not rotate", "FAIL")
                self.test_results.append(("Image rotation", False))
            
            self.root.after(1000, self.run_next_test)
        
        self.root.after(2500, check_rotation)
    
    def test_fullscreen_toggle(self):
        """Test 4: Test fullscreen toggle."""
        self.log("Test 4: Testing fullscreen toggle", "TEST")
        self.update_status("Test 4/6: Testing Fullscreen Toggle")
        
        # Toggle to fullscreen
        self.log("Switching to fullscreen mode...")
        self.app.toggle_fullscreen()
        
        def check_fullscreen():
            is_fullscreen = self.root.attributes("-fullscreen")
            if is_fullscreen:
                self.log("Fullscreen mode activated", "PASS")
                self.test_results.append(("Fullscreen toggle", True))
            else:
                self.log("Fullscreen mode failed", "FAIL")
                self.test_results.append(("Fullscreen toggle", False))
            
            # Toggle back to windowed
            self.log("Switching back to windowed mode...")
            self.app.exit_fullscreen()
            self.root.after(2000, self.run_next_test)
        
        self.root.after(2000, check_fullscreen)
    
    def test_keyboard_controls(self):
        """Test 5: Test keyboard controls."""
        self.log("Test 5: Testing keyboard controls", "TEST")
        self.update_status("Test 5/6: Testing Keyboard Controls")
        
        # Test 'f' key for fullscreen
        self.log("Simulating 'f' key press...")
        event = type('Event', (), {'char': 'f', 'keysym': 'f'})()
        self.app.toggle_fullscreen(event)
        
        def check_f_key():
            is_fullscreen = self.root.attributes("-fullscreen")
            self.log(f"Fullscreen after 'f' key: {is_fullscreen}", "PASS" if is_fullscreen else "FAIL")
            
            # Toggle back
            self.app.exit_fullscreen()
            
            self.test_results.append(("Keyboard controls", True))
            self.root.after(2000, self.run_next_test)
        
        self.root.after(1000, check_f_key)
    
    def finish_tests(self):
        """Test 6: Finish and show results."""
        self.log("Test 6: Completing test suite", "TEST")
        self.update_status("Test 6/6: Test Suite Complete!")
        
        # Calculate results
        total = len(self.test_results)
        passed = sum(1 for _, result in self.test_results if result)
        
        self.log("=" * 60)
        self.log(f"GUI TEST RESULTS: {passed}/{total} tests passed")
        self.log("=" * 60)
        
        for test_name, result in self.test_results:
            status = "PASS" if result else "FAIL"
            self.log(f"{test_name}: {status}", status)
        
        # Update status with final results
        result_text = f"✓ All Tests Complete: {passed}/{total} Passed"
        self.status_label.config(
            text=result_text,
            bg="green" if passed == total else "orange",
            fg="white"
        )
        
        # Add close button
        close_btn = tk.Button(
            self.root,
            text="Close Test (or press Q)",
            command=self.root.quit,
            bg="red",
            fg="white",
            font=("Arial", 12, "bold"),
            pady=10
        )
        close_btn.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.log("Test suite will auto-close in 10 seconds...")
        self.log("Or press Q to close now")
        
        # Auto-close after 10 seconds
        self.root.after(10000, self.root.quit)
    
    def update_status(self, text):
        """Update the status label."""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=f"GUI Test Running - {text}")
    
    def run_next_test(self):
        """Run the next test in sequence."""
        self.current_test += 1
        if self.current_test < len(self.tests):
            test_name, test_func = self.tests[self.current_test]
            test_func()
    
    def run(self):
        """Start the test suite."""
        print("\n" + "=" * 60)
        print("IMAGE SLIDESHOW - GUI TEST SUITE")
        print("=" * 60)
        print("This will run automated tests on the GUI.")
        print("Watch the window to see the tests in action!")
        print("=" * 60 + "\n")
        
        # Check if test images exist
        test_images_path = os.path.join(os.path.dirname(__file__), 'test_images')
        if not os.path.isdir(test_images_path):
            self.log(f"test_images folder not found at {test_images_path}", "FAIL")
            self.log(f"Run: python3 {os.path.join('tests', 'create_test_images.py')}", "INFO")
            return 1
        
        # Start first test
        test_name, test_func = self.tests[0]
        test_func()
        
        # Run the GUI
        self.root.mainloop()
        
        # Return exit code
        total = len(self.test_results)
        passed = sum(1 for _, result in self.test_results if result)
        return 0 if passed == total else 1


def main():
    """Main entry point for GUI tests."""
    try:
        tester = GUITester()
        exit_code = tester.run()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
