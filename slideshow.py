import os
import random
import tkinter as tk
import threading
from PIL import Image, ImageTk, ImageOps
from inky.auto import auto

class SlideshowApp:
    def __init__(self, root, image_folder, interval=5, fullscreen=True, db=None):
        self.root = root
        self.image_folder = image_folder
        self.interval = interval * 1000  # Convert to milliseconds
        self.images = []
        self.current_image_index = 0
        self.db = db
        self._timer_id = None
        self._reload_timer_id = None
        self.is_first_run = True

        # Initial Configuration Load
        self.reload_config()
        
        # Schedule periodic config reload
        self.schedule_reload()
        
        self.root.title("Image Slideshow")
        self.root.configure(bg=self.bg_color)
        
        # UI Setup & Basic Bindings
        self.root.attributes("-fullscreen", fullscreen)
        self.update_cursor() # Initial cursor state

        self.label = tk.Label(root, bg=self.bg_color)
        self.label.pack(fill=tk.BOTH, expand=True)

        # Apply bindings and focus
        self.update_bindings()
        self.root.focus_set()

        self.load_images()
        if not self.images:
            self.label.config(text=f"No images found in:\n{self.image_folder}", fg="white", font=("Arial", 20))
            return

        # Start slideshow after window stabilizes
        self.root.after(200, self.start_slideshow)

    def schedule_reload(self):
        # Poll every 5 seconds
        if self._reload_timer_id:
            self.root.after_cancel(self._reload_timer_id)
        self._reload_timer_id = self.root.after(5000, self.auto_reload)
        
    def auto_reload(self):
        self.reload_config()
        self.schedule_reload()

    def reload_config(self):
        if not self.db:
            # Fallback defaults if no DB
            self.bg_color = 'black'
            self.manual_enabled = True
            self.ext_str = '.jpg,.jpeg,.png,.gif,.bmp,.webp'
            self.ink_screen = False
            # Ensure background is applied if root exists
            if hasattr(self, 'root'):
                 self.root.configure(bg=self.bg_color)
            return

        try:
            # Fetch settings
            self.bg_color = self.db.get_setting('background_color', 'black')
            str_interval = self.db.get_setting('default_interval', str(self.interval // 1000))
            new_interval = int(str_interval) * 1000
            
            # Update interval if changed
            if new_interval != self.interval:
                print(f"⏱️ Interval changed: {self.interval} -> {new_interval}")
                self.interval = new_interval
                
            self.manual_enabled = self.db.get_setting('enable_manual_controls', 'True').lower() == 'true'
            self.ext_str = self.db.get_setting('image_extensions', '.jpg,.jpeg,.png,.gif,.bmp,.webp')
            self.ink_screen = self.db.get_setting('enable_inky', 'False').lower() == 'true'
            
            # Update bindings in case manual_enabled changed
            self.update_bindings()
            
            # Apply immediate visual changes
            self.root.configure(bg=self.bg_color)
            if hasattr(self, 'label'):
                self.label.config(bg=self.bg_color)
                
            # For now, just re-scan images to pick up new files without restart
            self.load_images()
            
        except Exception as e:
            print(f"⚠️ Error reloading config: {e}")

    def update_bindings(self):
        """Update keyboard bindings based on current configuration."""
        # Standard bindings
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.root.bind("f", self.toggle_fullscreen)
        self.root.bind("q", lambda e: self.root.quit())
        self.root.bind("<Configure>", self.on_resize)

        # Toggleable manual navigation
        if self.manual_enabled:
            self.root.bind("<Right>", self.manual_next)
            self.root.bind("<Left>", self.manual_prev)
        else:
            self.root.unbind("<Right>")
            self.root.unbind("<Left>")

    def load_images(self):
        ext_str = getattr(self, 'ext_str', '.jpg,.jpeg,.png,.gif,.bmp,.webp')
        valid_exts = {e.strip().lower() for e in ext_str.split(',')}
        try:
            self.images = [
                os.path.join(self.image_folder, f) 
                for f in sorted(os.listdir(self.image_folder))
                if os.path.splitext(f)[1].lower() in valid_exts
            ]
            self.is_first_run = True
        except Exception as e:
            print(f"Error loading images: {e}")

    def on_resize(self, event=None):
        """Redraw current image when window is resized."""
        if hasattr(self, '_resize_timer'):
            self.root.after_cancel(self._resize_timer)
        self._resize_timer = self.root.after(100, self.update_display)

    def update_cursor(self):
        """Show or hide the cursor based on fullscreen state. 
        Also moves cursor to the corner as a fallback."""
        if self.root.attributes("-fullscreen"):
            # Hide cursor
            self.root.config(cursor="none")
            # Warp cursor to bottom-right corner as a fallback (some systems don't hide)
            try:
                screen_w = self.root.winfo_screenwidth()
                screen_h = self.root.winfo_screenheight()
                self.root.event_generate('<Motion>', warp=True, x=screen_w-1, y=screen_h-1)
            except Exception:
                pass 
        else:
            self.root.config(cursor="")

    def toggle_fullscreen(self, event=None):
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))
        self.update_cursor()
        self.root.focus_set()
        self.root.after(100, self.update_display)

    def exit_fullscreen(self, event=None):
        self.root.attributes("-fullscreen", False)
        self.update_cursor()
        self.root.focus_set()
        self.root.after(100, self.update_display)

    def start_slideshow(self):
        self.update_display()
        self.schedule_next()

    def schedule_next(self):
        if self._timer_id:
            self.root.after_cancel(self._timer_id)
        self._timer_id = self.root.after(self.interval, self.auto_next)

    def auto_next(self):
        if not self.images: return
        self.current_image_index += 1
        if self.current_image_index >= len(self.images):
            self.current_image_index = 0
            self.is_first_run = False
            random.shuffle(self.images)
        self.update_display()
        self.schedule_next()

    def manual_next(self, event=None):
        if not self.images: return
        self.current_image_index = (self.current_image_index + 1) % len(self.images)
        self.update_display()
        self.schedule_next() # Reset timer

    def manual_prev(self, event=None):
        if not self.images: return
        self.current_image_index = (self.current_image_index - 1) % len(self.images)
        self.update_display()
        self.schedule_next() # Reset timer

    def update_display(self):
        if not self.images: return
        
        try:
            image_path = self.images[self.current_image_index]
            img = Image.open(image_path)
            img = ImageOps.exif_transpose(img)
            
            self.root.update_idletasks()
            win_w = self.root.winfo_width()
            win_h = self.root.winfo_height()
            
            if win_w <= 1: 
                win_w = self.root.winfo_screenwidth()
                win_h = self.root.winfo_screenheight()

            img_w, img_h = img.size
            ratio = min(win_w/img_w, win_h/img_h)
            new_size = (int(img_w * ratio), int(img_h * ratio))
            
            img_gui = img.resize(new_size, Image.Resampling.LANCZOS)
            self.photo_image = ImageTk.PhotoImage(img_gui)
            self.label.config(image=self.photo_image)
            self.current_photo_path = image_path
            
            # Force UI update so image shows up immediately (before Inky blocks)
            self.root.update()

            # UPDATE INKY SYNCHRONOUSLY (Blocks the app until done)
            if self.ink_screen:
                try:
                    inky = auto(ask_user=False, verbose=False)
                    # Use ImageOps.pad to fit image into inky.resolution without distortion
                    # Centered on a white background
                    resizedimage = ImageOps.pad(img, inky.resolution, color=(255, 255, 255))

                    try:
                        inky.set_image(resizedimage, saturation=0.5)
                    except TypeError:
                        inky.set_image(resizedimage)
                    inky.show()
                except Exception as e:
                    print(f"⚠️ Inky update failed: {e}. Disabling Inky support for this cycle.")
                    self.ink_screen = False

        except Exception as e:
            print(f"Error displaying image: {e}")