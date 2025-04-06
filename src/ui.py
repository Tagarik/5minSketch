import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk, ImageOps
import os
import time
import threading
import random

class AppUI:
    def __init__(self, root, image_handler, timer, update_image_callback):
        self.root = root
        self.image_handler = image_handler
        self.timer = timer
        self.update_image_callback = update_image_callback

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.main_frame = tk.Frame(self.notebook)
        self.settings_frame = tk.Frame(self.notebook)

        self.notebook.add(self.main_frame, text="Main")
        self.notebook.add(self.settings_frame, text="Settings")

        self.canvas = tk.Canvas(self.main_frame, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.config(highlightthickness=0)
        self.canvas.focus_set()  # Ensure the canvas can receive events

        self.progress_frame = tk.Frame(self.main_frame)
        self.progress_frame.pack(fill=tk.X, pady=5)

        self.progress = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10)

        self.time_label = tk.Label(self.progress_frame, text="0:00", font=("Arial", 12))
        self.time_label.pack(pady=5)

        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=5)

        self.folder_button = tk.Button(self.control_frame, text="Select Folder", command=self.select_folder)
        self.folder_button.pack(side=tk.LEFT, padx=5)

        self.timer_label = tk.Label(self.control_frame, text="Timer (minutes):")
        self.timer_label.pack(side=tk.LEFT, padx=5)

        self.timer_entry = tk.Entry(self.control_frame, width=5)
        self.timer_entry.pack(side=tk.LEFT, padx=5)

        self.timer_running = False
        self.toggle_timer_button = tk.Button(self.control_frame, text="Start Timer", command=self.toggle_timer)
        self.toggle_timer_button.pack(side=tk.LEFT, padx=5)

        self.lock_button = tk.Button(self.control_frame, text="Lock Window", command=self.lock_window)
        self.lock_button.pack(side=tk.LEFT, padx=5)

        self.opacity_slider = tk.Scale(self.control_frame, from_=0.1, to=1.0, resolution=0.1, orient=tk.HORIZONTAL, label="Opacity", command=self.set_opacity)
        self.opacity_slider.set(1.0)
        self.opacity_slider.pack(side=tk.LEFT, padx=10)

        self.monochrome_mode = False
        self.monochrome_button = tk.Button(self.control_frame, text="Monochrome: Off", command=self.toggle_monochrome)
        self.monochrome_button.pack(side=tk.LEFT, padx=5)
        
        # Add zoom dropdown menu
        self.zoom_label = tk.Label(self.control_frame, text="Zoom:")
        self.zoom_label.pack(side=tk.LEFT, padx=5)
        
        self.zoom_var = tk.StringVar(value="100%")
        self.zoom_options = ["100%", "125%", "150%", "200%", "300%"]
        self.zoom_dropdown = ttk.Combobox(self.control_frame, textvariable=self.zoom_var, 
                                          values=self.zoom_options, width=5, state="readonly")
        self.zoom_dropdown.pack(side=tk.LEFT, padx=5)
        self.zoom_dropdown.bind("<<ComboboxSelected>>", self.on_zoom_selected)

        self.additional_frame = tk.Frame(self.main_frame)
        self.additional_frame.pack(fill=tk.X, pady=5)

        self.image_id = None
        self.original_image = None
        self.resize_after_id = None
        self.window_locked = False

        self.root.bind("<Configure>", self.on_resize)

        # Settings tab
        self.settings_label = tk.Label(self.settings_frame, text="Settings", font=("Arial", 16))
        self.settings_label.pack(pady=10)

        self.display_method = tk.StringVar(value="name")

        self.name_radio = tk.Radiobutton(self.settings_frame, text="Sort by name", variable=self.display_method, value="name")
        self.name_radio.pack(anchor=tk.W, padx=10)

        self.random_radio = tk.Radiobutton(self.settings_frame, text="Randomize", variable=self.display_method, value="random")
        self.random_radio.pack(anchor=tk.W, padx=10)

        self.save_settings_button = tk.Button(self.settings_frame, text="Save Settings", command=self.save_settings)
        self.save_settings_button.pack(pady=10)

        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False
        
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)    # Linux scroll down
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_end)

        self.zoom_cache = {}  # Cache for different zoom levels
        self.max_cache_entries = 10  # Limit cache size

        self.zoom_presets = [1.0, 1.25, 1.5, 2.0, 3.0]  # The 5 zoom presets
        self.current_zoom_index = 0  # Start at 1x zoom (index 0)
        self.zoom_factor = self.zoom_presets[self.current_zoom_index]

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.image_handler.load_images(folder_path)
            self.update_image_callback()

    def toggle_timer(self):
        if self.timer_running:
            self.timer.stop()
            self.timer_running = False
            self.toggle_timer_button.config(text="Start Timer")
        else:
            try:
                # Convert minutes to seconds, allow for float values
                minutes = float(self.timer_entry.get())
                seconds = int(minutes * 60)
                
                # Ensure we have at least 1 second
                seconds = max(1, seconds)
                
                self.progress['maximum'] = seconds
                self.progress['value'] = seconds
                
                # Update the time display with the initial value
                formatted_time = self.format_time(seconds)
                self.time_label.config(text=formatted_time)
                
                self.timer.start(seconds)
                self.timer_running = True
                self.toggle_timer_button.config(text="Stop Timer")
            except ValueError:
                # Handle invalid input
                print("Please enter a valid number of minutes")

    def start_timer(self):
        interval = int(self.timer_entry.get())
        self.progress['maximum'] = interval
        self.progress['value'] = interval
        self.timer.start(interval)

    def stop_timer(self):
        self.timer.stop()

    def format_time(self, seconds):
        """Convert seconds to minutes:seconds format"""
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:02d}"

    def update_progress(self, value):
        self.progress['value'] = value
        
        # Update the progress bar text to show the formatted time
        formatted_time = self.format_time(value)
        
        # Then update it here:
        self.time_label.config(text=formatted_time)

    def display_image(self, image_path):
        try:
            # Clear the zoom cache when loading a new image
            self.zoom_cache.clear()
            
            # Reset zoom and pan values
            self.current_zoom_index = 0
            self.zoom_factor = self.zoom_presets[self.current_zoom_index]
            self.pan_x = 0
            self.pan_y = 0
            
            # Reset zoom dropdown to match
            self.zoom_var.set(f"{int(self.zoom_factor * 100)}%")
            
            # Load the original image 
            original = Image.open(image_path)
            
            # Check for alpha channel
            if original.mode == 'RGBA':
                # Create a white background
                background = Image.new('RGB', original.size, (255, 255, 255))
                # Composite the image onto the background
                original = Image.alpha_composite(background.convert('RGBA'), original).convert('RGB')
            
            # Check if image needs to be resized for performance
            width, height = original.size
            max_dimension = max(width, height)
            
            if max_dimension > 2000:
                # Calculate the scaling factor to reduce to 1500px max dimension
                scale_factor = 1500 / max_dimension
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                
                # Resize the image while maintaining aspect ratio
                self.original_image = original.resize((new_width, new_height), Image.NEAREST)
                print(f"Resized large image from {width}x{height} to {new_width}x{new_height} for performance")
            else:
                # Use the original image if it's already smaller than the threshold
                self.original_image = original
            
            # Delete existing image on canvas if any
            if self.image_id:
                self.canvas.delete(self.image_id)
                self.image_id = None
                
            # Force reference clearing for any previous image
            self.image = None
            
            # Pre-cache all zoom levels
            self.precache_zoom_levels()
                
            # Now resize with fresh state
            self.resize_image()
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")

    def on_resize(self, event=None):
        if self.resize_after_id:
            self.root.after_cancel(self.resize_after_id)
        self.resize_after_id = self.root.after(200, self.resize_image)

    def lock_window(self):
        self.window_locked = not self.window_locked
        self.root.attributes("-topmost", self.window_locked)
        self.lock_button.config(text="Unlock Window" if self.window_locked else "Lock Window")

    def set_opacity(self, value):
        opacity = float(value)
        self.root.attributes("-alpha", opacity)

    def save_settings(self):
        display_method = self.display_method.get()
        try:
            self.image_handler.set_display_method(display_method)
        except AttributeError:
            # If the method doesn't exist, set the attribute directly
            self.image_handler.display_method = display_method
            if display_method == "name":
                self.image_handler.images.sort()
        print(f"Settings saved: Display method = {display_method}")

    def toggle_monochrome(self):
        self.monochrome_mode = not self.monochrome_mode
        self.monochrome_button.config(text=f"Monochrome: {'On' if self.monochrome_mode else 'Off'}")
        
        # Refresh the current image to apply the effect
        if self.original_image:
            self.resize_image()
    
    def process_image(self, img):
        """Apply image processing based on current settings"""
        if self.monochrome_mode:
            return ImageOps.grayscale(img)
        return img

    # Add these new methods for zoom and pan
    def on_mouse_wheel(self, event):
        """Handle mouse wheel events with discrete zoom presets"""
        if not self.original_image:
            return
        
        # Store old zoom factor for ratio calculation
        old_zoom = self.zoom_factor
        old_zoom_index = self.current_zoom_index
        
        # Get canvas coordinates of the mouse
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Get center position of the image
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        center_x = canvas_width // 2 + self.pan_x
        center_y = canvas_height // 2 + self.pan_y
        
        # Calculate mouse position relative to image center
        mouse_x = canvas_x - center_x
        mouse_y = canvas_y - center_y
        
        # Determine zoom direction with preset increments
        if event.num == 5 or event.delta < 0:  # Scroll down or negative delta - zoom out
            self.current_zoom_index = max(0, self.current_zoom_index - 1)
        elif event.num == 4 or event.delta > 0:  # Scroll up or positive delta - zoom in
            self.current_zoom_index = min(len(self.zoom_presets) - 1, self.current_zoom_index + 1)
        
        # Get the new zoom factor from presets
        self.zoom_factor = self.zoom_presets[self.current_zoom_index]
        
        # Update the zoom dropdown to match
        self.zoom_var.set(f"{int(self.zoom_factor * 100)}%")
        
        # Reset pan if we're back to zoom level 1
        if self.zoom_factor == 1.0:
            self.pan_x = 0
            self.pan_y = 0
        else:
            # Adjust pan to keep mouse cursor position stable
            zoom_ratio = self.zoom_factor / old_zoom
            # Calculate how much the image coordinates would shift due to zoom
            new_mouse_x = mouse_x * zoom_ratio
            new_mouse_y = mouse_y * zoom_ratio
            # Adjust pan to compensate for the shift
            self.pan_x += (mouse_x - new_mouse_x)
            self.pan_y += (mouse_y - new_mouse_y)
        
        # Use the resize_image method to update the view
        self.resize_image()

    def on_drag_start(self, event):
        """Begin dragging to pan the image - always allowed but with limits"""
        self.is_dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_drag_motion(self, event):
        """Pan the image as the mouse is dragged with incremental rendering"""
        if self.is_dragging:
            # Calculate the distance moved
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            # Calculate current image dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if self.zoom_factor >= 1.0:
                # When zoomed in, allow full panning
                self.pan_x += dx
                self.pan_y += dy
            else:
                # When zoomed out, limit panning proportionally to zoom level
                pan_limit = 100 * self.zoom_factor
                
                # Calculate new pan position
                new_pan_x = self.pan_x + dx
                new_pan_y = self.pan_y + dy
                
                # Apply stricter limits when zoomed out
                self.pan_x = max(-pan_limit, min(pan_limit, new_pan_x))
                self.pan_y = max(-pan_limit, min(pan_limit, new_pan_y))
            
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            
            # Use very fast mode during active dragging
            self.resize_image(very_fast_mode=True)
            
            # Cancel any pending quality upgrades
            if hasattr(self, 'drag_fast_quality_id') and self.drag_fast_quality_id:
                self.root.after_cancel(self.drag_fast_quality_id)
                
            if hasattr(self, 'drag_high_quality_id') and self.drag_high_quality_id:
                self.root.after_cancel(self.drag_high_quality_id)
            
            # Schedule quality upgrades with delay
            self.drag_fast_quality_id = self.root.after(50, lambda: self.resize_image(fast_mode=True))

    def on_drag_end(self, event):
        """End the dragging operation but keep using fast rendering"""
        self.is_dragging = False
        
        # No longer schedule high-quality rendering to maintain speed
        # self.root.after(100, lambda: self.resize_image(fast_mode=False))
    
    def resize_image(self, fast_mode=True, very_fast_mode=True):  # Changed defaults to True
        """Resize image with quality level based on interaction state"""
        if not self.original_image:
            return
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Skip if canvas isn't properly sized yet
        if canvas_width <= 1 or canvas_height <= 1:
            return
            
        image_width, image_height = self.original_image.size
        
        # Use the zoom cache
        img_id = id(self.original_image)
        cache_key = f"{img_id}_{self.zoom_factor:.1f}"
        
        if cache_key in self.zoom_cache:
            processed_image = self.zoom_cache[cache_key]
            self.display_processed_image(processed_image)
            return
        
        # Calculate scaling
        base_scale = min(canvas_width / image_width, canvas_height / image_height)
        scale = base_scale * self.zoom_factor
        
        new_width = int(image_width * scale)
        new_height = int(image_height * scale)
        
        # Simple approach: always use NEAREST for all resize operations
        resample_method = Image.NEAREST
        temp_width, temp_height = new_width, new_height
        
        # Resize the image
        resized_image = self.original_image.resize((temp_width, temp_height), resample_method)
        
        processed_image = self.process_image(resized_image)
        
        # Only cache high quality images
        if not very_fast_mode and not fast_mode:
            if len(self.zoom_cache) >= self.max_cache_entries:
                self.zoom_cache.pop(next(iter(self.zoom_cache)))
            self.zoom_cache[cache_key] = processed_image
        
        # Display the image
        self.display_processed_image(processed_image)

    def display_processed_image(self, processed_image):
        """Display a processed image on the canvas"""
        self.image = ImageTk.PhotoImage(processed_image)
        
        if self.image_id:
            self.canvas.delete(self.image_id)
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        center_x = canvas_width // 2 + self.pan_x
        center_y = canvas_height // 2 + self.pan_y
        
        self.image_id = self.canvas.create_image(center_x, center_y, anchor=tk.CENTER, image=self.image)

    def precache_zoom_levels(self):
        """Pre-cache all zoom preset levels for smoother zooming"""
        if not self.original_image:
            return
            
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Skip if canvas isn't properly sized yet
        if canvas_width <= 1 or canvas_height <= 1:
            return
            
        image_width, image_height = self.original_image.size
        
        # Calculate base scale once
        base_scale = min(canvas_width / image_width, canvas_height / image_height)
        
        # Pre-cache images for all zoom presets (except 1.0 which will be cached on first display)
        for zoom_level in self.zoom_presets[1:]:  # Skip 1.0 as it will be done immediately
            scale = base_scale * zoom_level
            new_width = int(image_width * scale)
            new_height = int(image_height * scale)
            
            # Generate cache key
            img_id = id(self.original_image)
            cache_key = f"{img_id}_{zoom_level:.2f}"
            
            # Skip if already cached
            if cache_key in self.zoom_cache:
                continue
                
            # Resize with NEAREST for consistent appearance
            resized_image = self.original_image.resize((new_width, new_height), Image.NEAREST)
            processed_image = self.process_image(resized_image)
            
            # Cache the processed image
            self.zoom_cache[cache_key] = processed_image
            
            print(f"Cached zoom level: {zoom_level:.2f}")

    def on_zoom_selected(self, event=None):
        """Handle zoom dropdown selection"""
        if not self.original_image:
            return
            
        # Get the selected zoom level from the dropdown (remove % and convert to float)
        selected_zoom = self.zoom_var.get().rstrip('%')
        zoom_factor = float(selected_zoom) / 100.0
        
        # Find the closest preset zoom level
        closest_index = 0
        min_diff = float('inf')
        for i, preset in enumerate(self.zoom_presets):
            diff = abs(preset - zoom_factor)
            if diff < min_diff:
                min_diff = diff
                closest_index = i
        
        # Update the current zoom index and factor
        self.current_zoom_index = closest_index
        self.zoom_factor = self.zoom_presets[self.current_zoom_index]
        
        # Reset pan if we're back to zoom level 1
        if self.zoom_factor == 1.0:
            self.pan_x = 0
            self.pan_y = 0
        
        # Update the image with the new zoom level
        self.resize_image()

class ImageHandler:
    def __init__(self):
        self.images = []
        self.current_image_index = 0
        self.display_method = "name"

    def load_images(self, folder_path):
        self.images = []
        for file_name in os.listdir(folder_path):
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                file_path = os.path.join(folder_path, file_name)
                try:
                    # Attempt to open the image to ensure it is valid
                    Image.open(file_path).verify()
                    self.images.append(file_path)
                except Exception as e:
                    print(f"Skipping file {file_path}: {e}")
        self.current_image_index = 0
        if self.display_method == "name":
            self.images.sort()

    def has_images(self):
        return len(self.images) > 0

    def get_current_image(self):
        if self.has_images():
            return self.images[self.current_image_index]
        return None

    def next_image(self):
        if self.has_images():
            if self.display_method == "random":
                self.current_image_index = random.randint(0, len(self.images) - 1)
            else:
                self.current_image_index = (self.current_image_index + 1) % len(self.images)

    def set_display_method(self, method):
        self.display_method = method
        if method == "name":
            self.images.sort()

class Timer:
    def __init__(self, update_callback):
        self.update_callback = update_callback
        self.timer_seconds = 0
        self.timer_running = False
        self.timer_thread = None

    def start(self, interval):
        self.timer_seconds = interval
        self.timer_running = True
        self.timer_thread = threading.Thread(target=self.run_timer)
        self.timer_thread.start()

    def run_timer(self):
        while self.timer_running and self.timer_seconds > 0:
            time.sleep(1)
            self.timer_seconds -= 1
            if self.timer_seconds == 0:
                self.update_callback()

    def stop(self):
        self.timer_running = False
        if self.timer_thread:
            self.timer_thread.join()


def update_image():
    image_path = image_handler.get_current_image()
    if image_path:
        app.display_image(image_path)

if __name__ == "__main__":
    root = tk.Tk()
    image_handler = ImageHandler()
    timer = Timer(update_image)
    app = AppUI(root, image_handler, timer, update_image)
    root.mainloop()