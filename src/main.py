import os
import time
import tkinter as tk
from tkinter import filedialog
from image_handler import ImageHandler
from timer import Timer
from ui import AppUI

class ImageViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Viewer App")
        
        self.image_handler = ImageHandler()
        self.timer = Timer()
        self.ui = AppUI(root, self.image_handler, self.timer, self.update_image)

        self.timer.set_timer_callback(self.on_timer_tick)

    def update_image(self):
        if self.image_handler.has_images():
            image_path = self.image_handler.get_current_image()
            self.ui.display_image(image_path)

    def on_timer_tick(self, remaining_time):
        self.ui.update_progress(remaining_time)
        if remaining_time == 0:
            self.root.after(0, self._update_image_and_reset_timer)

    def _update_image_and_reset_timer(self):
        self.image_handler.next_image()
        self.update_image()
        self.timer.reset()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewerApp(root)
    app.run()