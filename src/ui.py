import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
import os
import time
import threading

class AppUI:
    def __init__(self, root, image_handler, timer, update_image_callback):
        self.root = root
        self.image_handler = image_handler
        self.timer = timer
        self.update_image_callback = update_image_callback

        self.frame = tk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.frame, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.control_frame = tk.Frame(root)
        self.control_frame.pack(fill=tk.X)

        self.folder_button = tk.Button(self.control_frame, text="Select Folder", command=self.select_folder)
        self.folder_button.pack(side=tk.LEFT)

        self.timer_label = tk.Label(self.control_frame, text="Timer (seconds):")
        self.timer_label.pack(side=tk.LEFT)

        self.timer_entry = tk.Entry(self.control_frame)
        self.timer_entry.pack(side=tk.LEFT)

        self.start_button = tk.Button(self.control_frame, text="Start", command=self.start_timer)
        self.start_button.pack(side=tk.LEFT)

        self.stop_button = tk.Button(self.control_frame, text="Stop", command=self.stop_timer)
        self.stop_button.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(self.control_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.progress.pack(side=tk.LEFT, padx=10)

        self.image_id = None
        self.original_image = None
        self.resize_after_id = None

        self.root.bind("<Configure>", self.on_resize)

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.image_handler.load_images(folder_path)
            self.update_image_callback()

    def start_timer(self):
        interval = int(self.timer_entry.get())
        self.progress['maximum'] = interval
        self.progress['value'] = interval
        self.timer.start(interval)

    def stop_timer(self):
        self.timer.stop()

    def update_progress(self, value):
        self.progress['value'] = value

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
            self.image = ImageTk.PhotoImage(resized_image)

            if self.image_id:
                self.canvas.delete(self.image_id)
            self.image_id = self.canvas.create_image(canvas_width // 2, canvas_height // 2, anchor=tk.CENTER, image=self.image)

    def on_resize(self, event=None):
        if self.resize_after_id:
            self.root.after_cancel(self.resize_after_id)
        self.resize_after_id = self.root.after(200, self.resize_image)

class ImageHandler:
    def __init__(self):
        self.images = []
        self.current_image_index = 0

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

    def has_images(self):
        return len(self.images) > 0

    def get_current_image(self):
        if self.has_images():
            return self.images[self.current_image_index]
        return None

    def next_image(self):
        if self.has_images():
            self.current_image_index = (self.current_image_index + 1) % len(self.images)

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
                self.timer_seconds = int(self.timer_entry.get())

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