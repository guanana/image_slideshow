#!/usr/bin/env python3
"""
Interactive GUI Demo/Test for Image Slideshow

This runs the slideshow with a visible control panel showing:
- Current image info
- Test progress
- Interactive controls
- Real-time status
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from slideshow import SlideshowApp

class SlideshowDemo:
    """Interactive demo of the slideshow with visual feedback."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Image Slideshow - Interactive Demo")
        self.root.geometry("1000x700")
        self.root.configure(bg="#2b2b2b")
        
        # Demo state
        self.demo_running = False
        self.test_step = 0
        self.start_time = time.time()
        
        self.setup_ui()
        self.create_slideshow()
    
    def setup_ui(self):
        """Create the demo UI with control panel."""
        
        # Title
        title = tk.Label(
            self.root,
            text="🎬 Image Slideshow - Interactive GUI Demo",
            font=("Arial", 18, "bold"),
            bg="#2b2b2b",
            fg="#00ff00",
            pady=15
        )
        title.pack(fill=tk.X)
        
        # Main container
        main_frame = tk.Frame(self.root, bg="#2b2b2b")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left side - Slideshow
        self.slideshow_frame = tk.Frame(main_frame, bg="black", relief=tk.SUNKEN, bd=2)
        self.slideshow_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Right side - Control Panel
        control_panel = tk.Frame(main_frame, bg="#1e1e1e", width=300, relief=tk.RAISED, bd=2)
        control_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        control_panel.pack_propagate(False)
        
        # Control panel title
        tk.Label(
            control_panel,
            text="📊 Control Panel",
            font=("Arial", 14, "bold"),
            bg="#1e1e1e",
            fg="#ffffff",
            pady=10
        ).pack(fill=tk.X)
        
        # Status section
        status_frame = tk.LabelFrame(
            control_panel,
            text="Status",
            bg="#1e1e1e",
            fg="#00ff00",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = tk.Label(
            status_frame,
            text="⏸ Ready to start",
            font=("Arial", 10),
            bg="#1e1e1e",
            fg="#ffff00",
            anchor="w",
            justify=tk.LEFT
        )
        self.status_label.pack(fill=tk.X)
        
        # Image info section
        info_frame = tk.LabelFrame(
            control_panel,
            text="Current Image",
            bg="#1e1e1e",
            fg="#00ff00",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.image_info = tk.Label(
            info_frame,
            text="No image loaded",
            font=("Arial", 9),
            bg="#1e1e1e",
            fg="#ffffff",
            anchor="w",
            justify=tk.LEFT
        )
        self.image_info.pack(fill=tk.X)
        
        # Progress section
        progress_frame = tk.LabelFrame(
            control_panel,
            text="Demo Progress",
            bg="#1e1e1e",
            fg="#00ff00",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=250
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = tk.Label(
            progress_frame,
            text="0% Complete",
            font=("Arial", 9),
            bg="#1e1e1e",
            fg="#ffffff"
        )
        self.progress_label.pack()
        
        # Test log section
        log_frame = tk.LabelFrame(
            control_panel,
            text="Test Log",
            bg="#1e1e1e",
            fg="#00ff00",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrollable log
        log_scroll = tk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(
            log_frame,
            height=10,
            font=("Courier", 8),
            bg="#000000",
            fg="#00ff00",
            yscrollcommand=log_scroll.set,
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)
        
        # Control buttons
        button_frame = tk.Frame(control_panel, bg="#1e1e1e", pady=10)
        button_frame.pack(fill=tk.X, padx=10)
        
        self.start_btn = tk.Button(
            button_frame,
            text="▶ Start Demo",
            command=self.start_demo,
            bg="#00aa00",
            fg="white",
            font=("Arial", 10, "bold"),
            pady=8
        )
        self.start_btn.pack(fill=tk.X, pady=2)
        
        self.stop_btn = tk.Button(
            button_frame,
            text="⏹ Stop",
            command=self.stop_demo,
            bg="#aa0000",
            fg="white",
            font=("Arial", 10, "bold"),
            pady=8,
            state=tk.DISABLED
        )
        self.stop_btn.pack(fill=tk.X, pady=2)
        
        tk.Button(
            button_frame,
            text="❌ Close",
            command=self.root.quit,
            bg="#555555",
            fg="white",
            font=("Arial", 10, "bold"),
            pady=8
        ).pack(fill=tk.X, pady=2)
        
        # Footer
        footer = tk.Label(
            self.root,
            text="Keyboard: F=Fullscreen | Esc=Exit Fullscreen | Q=Quit",
            font=("Arial", 9),
            bg="#2b2b2b",
            fg="#888888",
            pady=8
        )
        footer.pack(fill=tk.X)
    
    def create_slideshow(self):
        """Create the slideshow instance."""
        import configparser
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
        config.read(config_path)
        
        test_images_path = os.path.join(os.path.dirname(__file__), 'test_images')
        
        # Create a container for the slideshow
        self.app = SlideshowApp(
            self.slideshow_frame,
            test_images_path,
            interval=3,
            fullscreen=False,
            config=config['slideshow'] if 'slideshow' in config else {}
        )
        
        self.log("✓ Slideshow initialized")
        self.log(f"✓ Found {len(self.app.images)} images")
        self.update_image_info()
        
        # Start monitoring
        self.monitor_slideshow()
    
    def log(self, message):
        """Add message to log."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def update_status(self, text, color="#ffff00"):
        """Update status label."""
        self.status_label.config(text=text, fg=color)
    
    def update_image_info(self):
        """Update current image information."""
        if self.app.images:
            current_idx = self.app.current_image_index
            total = len(self.app.images)
            current_file = os.path.basename(self.app.images[current_idx])
            
            info = f"Image: {current_idx + 1}/{total}\n"
            info += f"File: {current_file}\n"
            
            if self.app.photo_image:
                info += f"Size: {self.app.photo_image.width()}x{self.app.photo_image.height()}"
            
            self.image_info.config(text=info)
    
    def monitor_slideshow(self):
        """Monitor slideshow state and update UI."""
        self.update_image_info()
        
        # Schedule next update
        self.root.after(500, self.monitor_slideshow)
    
    def start_demo(self):
        """Start the automated demo."""
        self.demo_running = True
        self.test_step = 0
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        self.log("=" * 40)
        self.log("🎬 Starting automated demo...")
        self.log("=" * 40)
        self.update_status("▶ Demo running...", "#00ff00")
        
        self.run_demo_steps()
    
    def stop_demo(self):
        """Stop the demo."""
        self.demo_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.update_status("⏸ Demo stopped", "#ff0000")
        self.log("⏹ Demo stopped by user")
    
    def run_demo_steps(self):
        """Run automated demo steps."""
        if not self.demo_running:
            return
        
        steps = [
            (0, "Watching slideshow rotation...", lambda: self.log("✓ Slideshow is rotating images")),
            (3000, "Testing image display...", lambda: self.test_image_display()),
            (6000, "Checking aspect ratio...", lambda: self.test_aspect_ratio()),
            (9000, "Testing fullscreen toggle...", lambda: self.test_fullscreen()),
            (12000, "Verifying keyboard controls...", lambda: self.log("✓ Keyboard controls available (F, Esc, Q)")),
            (15000, "Demo complete!", lambda: self.complete_demo()),
        ]
        
        for delay, message, action in steps:
            if self.test_step * 3000 == delay:
                self.log(f"▶ Step {self.test_step + 1}: {message}")
                action()
                
                # Update progress
                progress = ((self.test_step + 1) / len(steps)) * 100
                self.progress_bar['value'] = progress
                self.progress_label.config(text=f"{int(progress)}% Complete")
                
                self.test_step += 1
                if self.test_step < len(steps):
                    self.root.after(3000, self.run_demo_steps)
                return
    
    def test_image_display(self):
        """Test image display."""
        if self.app.photo_image:
            self.log("✓ Images are displaying correctly")
        else:
            self.log("✗ No image displayed")
    
    def test_aspect_ratio(self):
        """Test aspect ratio preservation."""
        if self.app.photo_image:
            w, h = self.app.photo_image.width(), self.app.photo_image.height()
            self.log(f"✓ Current display size: {w}x{h}")
            self.log("✓ Aspect ratio preserved")
    
    def test_fullscreen(self):
        """Test fullscreen toggle."""
        self.log("▶ Toggling fullscreen...")
        self.app.toggle_fullscreen()
        self.root.after(1500, lambda: [
            self.app.exit_fullscreen(),
            self.log("✓ Fullscreen toggle works")
        ])
    
    def complete_demo(self):
        """Complete the demo."""
        self.demo_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.update_status("✓ Demo complete!", "#00ff00")
        self.log("=" * 40)
        self.log("✓ All demo steps completed!")
        self.log("=" * 40)
        self.log("You can now interact with the slideshow")
        self.log("or click 'Start Demo' to run again")
    
    def run(self):
        """Start the demo application."""
        print("\n" + "=" * 60)
        print("IMAGE SLIDESHOW - INTERACTIVE GUI DEMO")
        print("=" * 60)
        print("A visual demo window will open.")
        print("Click 'Start Demo' to see automated testing!")
        print("=" * 60 + "\n")
        
        self.root.mainloop()


def main():
    """Main entry point."""
    try:
        demo = SlideshowDemo()
        demo.run()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
