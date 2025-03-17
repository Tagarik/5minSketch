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

    def resize_image(self):
        if self.original_image:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            image_width, image_height = self.original_image.size

            scale = min(canvas_width / image_width, canvas_height / image_height)
            new_width = int(image_width * scale)
            new_height = int(image_height * scale)

            resized_image = self.original_image.resize((new_width, new_height), Image.LANCZOS)
            processed_image = self.process_image(resized_image)
            
            self.image = ImageTk.PhotoImage(processed_image)

            if self.image_id:
                self.canvas.delete(self.image_id)
            self.image_id = self.canvas.create_image(canvas_width // 2, canvas_height // 2, anchor=tk.CENTER, image=self.image)

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