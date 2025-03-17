import os
import random
from PIL import Image

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

    def previous_image(self):
        if self.has_images():
            if self.display_method == "random":
                self.current_image_index = random.randint(0, len(self.images) - 1)
            else:
                self.current_image_index = (self.current_image_index - 1) % len(self.images)

    def set_display_method(self, method):
        self.display_method = method
        if method == "name":
            self.images.sort()