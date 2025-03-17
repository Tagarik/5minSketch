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
            self.original_image = Image.open(image_path)
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
        """Handle mouse wheel events for zooming"""
        if not self.original_image:
            return
            
        # Store old zoom factor for ratio calculation
        old_zoom = self.zoom_factor
        
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
        
        # Determine zoom direction
        if event.num == 5 or event.delta < 0:  # Scroll down or negative delta
            self.zoom_factor = max(0.1, self.zoom_factor - 0.1)
        elif event.num == 4 or event.delta > 0:  # Scroll up or positive delta
            self.zoom_factor = min(5.0, self.zoom_factor + 0.1)
        
        # Reset pan if we're back to zoom level 1
        if abs(self.zoom_factor - 1.0) < 0.05:
            self.zoom_factor = 1.0
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
            
        self.resize_image()
        
    def on_drag_start(self, event):
        """Begin dragging to pan the image"""
        if self.zoom_factor > 1.0:  # Only enable panning when zoomed in
            self.is_dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
    
    def on_drag_motion(self, event):
        """Pan the image as the mouse is dragged"""
        if self.is_dragging:
            # Calculate the distance moved
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            self.pan_x += dx
            self.pan_y += dy
            
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            
            # Redraw with new pan values
            self.resize_image()
    
    def on_drag_end(self, event):
        """End the dragging operation"""
        self.is_dragging = False
    
    def resize_image(self):
        if self.original_image:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            image_width, image_height = self.original_image.size

            base_scale = min(canvas_width / image_width, canvas_height / image_height)
            
            # zoom factor
            scale = base_scale * self.zoom_factor
            
            new_width = int(image_width * scale)
            new_height = int(image_height * scale)

            # Resize
            resized_image = self.original_image.resize((new_width, new_height), Image.LANCZOS)
            
            # Apply any processing (eg. monochrome)
            processed_image = self.process_image(resized_image)
            
            self.image = ImageTk.PhotoImage(processed_image)

            if self.image_id:
                self.canvas.delete(self.image_id)
                
            # Calculate center position
            center_x = canvas_width // 2 + self.pan_x
            center_y = canvas_height // 2 + self.pan_y
            
            # Create final image
            self.image_id = self.canvas.create_image(center_x, center_y, anchor=tk.CENTER, image=self.image)

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