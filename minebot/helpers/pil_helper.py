from PIL import Image
import os

def open_image(path: str) -> Image.Image:
    """Open an image file and convert it to RGBA."""
    return Image.open(path).convert("RGBA")

def resize_image(image: Image.Image, scale: float) -> Image.Image:
    """Resize the image using high-quality downscaling."""
    new_size = (int(image.width * scale), int(image.height * scale))
    return image.resize(new_size, Image.Resampling.LANCZOS)

def paste_image(base: Image.Image, overlay: Image.Image, position: tuple):
    """Paste an overlay image onto a base image with transparency."""
    base.paste(overlay, position, overlay)

def save_image(image: Image.Image, path: str):
    """Save the image to disk."""
    image.save(path)

def ensure_temp_dir(directory: str):
    """Ensure that a temporary directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)