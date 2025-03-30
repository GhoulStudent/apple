import base64
import io
from PIL import Image

def resize_image(image, max_size=800):
    """Resize an image while maintaining aspect ratio"""
    width, height = image.size
    if width > max_size or height > max_size:
        ratio = min(max_size / width, max_size / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        return image.resize((new_width, new_height), Image.LANCZOS)
    return image

def format_confidence(confidence):
    """Format confidence score for display"""
    return f"{confidence:.2f}%"

def get_confidence_class(confidence):
    """Return Bootstrap class based on confidence level"""
    if confidence >= 90:
        return "bg-success"
    elif confidence >= 70:
        return "bg-info"
    elif confidence >= 50:
        return "bg-warning"
    else:
        return "bg-danger"
