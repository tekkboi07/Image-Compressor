# backend/processor.py

import io
from typing import Optional, Tuple

from PIL import Image

_ROTATE_MAP = {
    "right": Image.ROTATE_270,  # 90° clockwise
    "left": Image.ROTATE_90,    # 90° counter-clockwise
    "180": Image.ROTATE_180,
}


def load_image(file_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(file_bytes))


def apply_transforms(
    img: Image.Image,
    flip: Optional[str] = None,    # None | "horizontal" | "vertical"
    rotate: Optional[str] = None,  # None | "right" | "left" | "180"
) -> Image.Image:
    if flip == "horizontal":
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    elif flip == "vertical":
        img = img.transpose(Image.FLIP_TOP_BOTTOM)

    if rotate:
        img = img.transpose(_ROTATE_MAP[rotate])

    return img


def prepare_for_format(img: Image.Image, output_format: str) -> Image.Image:
    output_format = output_format.upper()
    if output_format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
        rgba = img.convert("RGBA")
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    if img.mode not in ("RGB", "RGBA"):
        return img.convert("RGB")
    return img


def encode_at_quality(img: Image.Image, output_format: str, quality: int) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=output_format.upper(), quality=quality)
    return buf.getvalue()


def compress_to_target(
    img: Image.Image,
    output_format: str,
    target_bytes: int,
    min_quality: int = 5,
    max_quality: int = 100,   # was 95
) -> Tuple[bytes, int]:
    img = prepare_for_format(img, output_format)

    lo, hi = min_quality, max_quality
    best_bytes, best_quality = None, lo

    while lo <= hi:
        mid = (lo + hi) // 2
        encoded = encode_at_quality(img, output_format, mid)
        if len(encoded) <= target_bytes:
            best_bytes, best_quality = encoded, mid
            lo = mid + 1
        else:
            hi = mid - 1

    if best_bytes is not None:
        return best_bytes, best_quality

    width, height = img.size
    while True:
        width, height = int(width * 0.9), int(height * 0.9)
        if width < 20 or height < 20:
            resized = img.resize((max(width, 1), max(height, 1)), Image.LANCZOS)
            return encode_at_quality(resized, output_format, min_quality), min_quality
        resized = img.resize((width, height), Image.LANCZOS)
        encoded = encode_at_quality(resized, output_format, min_quality)
        if len(encoded) <= target_bytes:
            return encoded, min_quality


def process_image(
    file_bytes: bytes,
    output_format: str,
    target_bytes: int,
    flip: Optional[str] = None,
    rotate: Optional[str] = None,
) -> Tuple[bytes, int]:
    img = load_image(file_bytes)
    img = apply_transforms(img, flip=flip, rotate=rotate)
    return compress_to_target(img, output_format, target_bytes)