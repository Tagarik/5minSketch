import os
import time
import tkinter as tk
from src.image_handler import ImageHandler
from src.timer import Timer
from src.ui import AppUI

class ImageViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("5 minute sketcher")
        
        self.image_handler = ImageHandler()
        self.timer = Timer()
        self.ui = AppUI(root, self.image_handler, self.timer, self.update_image)

        self.timer.set_timer_callback(self.on_timer_tick)
        
        # Bind arrow keys for navigation
        self.root.bind("<Left>", self.previous_image)
        self.root.bind("<Right>", self.next_image)

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
        
    def next_image(self, event=None):
        self.image_handler.next_image()
        self.update_image()
        
    def previous_image(self, event=None):
        self.image_handler.previous_image()  # We'll need to add this method
        self.update_image()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewerApp(root)
    app.run()