"""
Deterministic color generation for trucks.
Ensures each truck gets a consistent, unique, high-contrast color.
"""

import hashlib


def generate_truck_color(truck_id: str) -> str:
    """
    Generate a deterministic hex color for a truck based on its ID.
    Uses HSL color space to ensure high saturation and contrast.
    
    Args:
        truck_id: Unique truck identifier (e.g., "TRUCK-001")
    
    Returns:
        Hex color string (e.g., "#FF5733")
    """
    # Create a hash of the truck ID to get a numeric value
    hash_obj = hashlib.md5(truck_id.encode())
    hash_int = int(hash_obj.hexdigest(), 16)
    
    # Use hash to generate hue (0-359 degrees)
    hue = hash_int % 360
    
    # Use fixed saturation and lightness for high contrast
    saturation = 75  # 75% saturation (vibrant)
    lightness = 45   # 45% lightness (medium brightness)
    
    # Convert HSL to RGB
    rgb = hsl_to_rgb(hue, saturation, lightness)
    
    # Convert RGB to hex
    hex_color = f"#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}"
    
    return hex_color.upper()


def hsl_to_rgb(h: float, s: float, l: float) -> tuple:
    """
    Convert HSL (Hue, Saturation, Lightness) to RGB.
    
    Args:
        h: Hue (0-360)
        s: Saturation (0-100)
        l: Lightness (0-100)
    
    Returns:
        Tuple of (R, G, B) values (0-255)
    """
    # Normalize values to 0-1
    h = h / 360
    s = s / 100
    l = l / 100
    
    if s == 0:
        # Achromatic (gray)
        r = g = b = l * 255
    else:
        def hue_to_rgb(p: float, q: float, t: float) -> float:
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1/6:
                return p + (q - p) * 6 * t
            if t < 1/2:
                return q
            if t < 2/3:
                return p + (q - p) * (2/3 - t) * 6
            return p
        
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        
        r = hue_to_rgb(p, q, h + 1/3) * 255
        g = hue_to_rgb(p, q, h) * 255
        b = hue_to_rgb(p, q, h - 1/3) * 255
    
    return (r, g, b)


def get_halo_color(hex_color: str, alpha: float = 0.15) -> str:
    """
    Generate a light halo color (nearly white with slight tint).
    Used for the glow layer under route polylines.
    
    Args:
        hex_color: Main route color (not directly used, just for consistency)
        alpha: Alpha transparency (0-1)
    
    Returns:
        RGBA color string for CSS
    """
    # Use a very light blue-white for maximum contrast
    # This works on both street and satellite map backgrounds
    return f"rgba(200, 220, 255, {alpha})"
