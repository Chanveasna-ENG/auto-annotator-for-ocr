# backend/image_ops.py
from PIL import Image

class ResizeAndPad:
    def __init__(self, height, width, fill=(0, 0, 0)):
        self.height = height
        self.width = width
        self.fill = fill

    def __call__(self, img):
        original_width, original_height = img.size
        target_aspect = self.width / self.height
        original_aspect = original_width / original_height
        
        if original_aspect > target_aspect:
            new_width = self.width
            new_height = int(new_width / original_aspect)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            new_img = Image.new(img.mode, (self.width, self.height), self.fill)
            paste_y = (self.height - new_height) // 2
            new_img.paste(img, (0, paste_y))
        else:
            new_height = self.height
            new_width = int(new_height * original_aspect)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            new_img = Image.new(img.mode, (self.width, self.height), self.fill)
            paste_x = (self.width - new_width) // 2
            new_img.paste(img, (paste_x, 0))
            
        return new_img