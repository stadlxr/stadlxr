"""
prep_photo.py — turn a normal photo into a clean, high-contrast, background-free
grayscale image that's ready to be converted into ASCII art.

Usage:
    python scripts/prep_photo.py source-photo.jpg

Output:
    source-prepped.png  (grayscale, subject isolated, composited on white)
"""

import sys
import io

import numpy as np
import cv2
from PIL import Image
from rembg import remove


def remove_background(image_bytes: bytes) -> Image.Image:
    """Run rembg and return an RGBA PIL image with the background stripped."""
    out_bytes = remove(image_bytes)
    return Image.open(io.BytesIO(out_bytes)).convert("RGBA")


def composite_on_white(rgba: Image.Image) -> Image.Image:
    """Flatten an RGBA cutout onto a solid white background."""
    white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    flattened = Image.alpha_composite(white_bg, rgba)
    return flattened.convert("RGB")


def apply_clahe(gray: np.ndarray) -> np.ndarray:
    """
    Contrast-limited adaptive histogram equalization.
    This is what turns a flatly-lit face into something with real
    highlights/shadows instead of one mushy gray blob.
    """
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    return clahe.apply(gray)


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/prep_photo.py <source-photo.jpg>")
        sys.exit(1)

    src_path = sys.argv[1]

    with open(src_path, "rb") as f:
        original_bytes = f.read()

    print("Removing background...")
    cutout = remove_background(original_bytes)

    print("Compositing onto white...")
    flattened = composite_on_white(cutout)

    print("Boosting local contrast (CLAHE)...")
    gray = cv2.cvtColor(np.array(flattened), cv2.COLOR_RGB2GRAY)
    contrasted = apply_clahe(gray)

    out_path = "source-prepped.png"
    Image.fromarray(contrasted).save(out_path)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
