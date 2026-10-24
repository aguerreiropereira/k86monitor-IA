"""Platform-aware font lookup for the small K86 display."""
from __future__ import annotations

import os
from pathlib import Path

from PIL import ImageFont


def load_font(filename: str, size: int) -> ImageFont.ImageFont:
    """Load a matching system sans font, falling back to Pillow's bitmap font."""
    bold = "bold" in filename.lower()
    candidates: list[Path] = []

    if os.name == "nt":
        fonts_dir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        candidates.append(fonts_dir / ("arialbd.ttf" if bold else "arial.ttf"))
    elif os.uname().sysname == "Darwin":
        fonts_dir = Path("/System/Library/Fonts/Supplemental")
        candidates.append(fonts_dir / ("Arial Bold.ttf" if bold else "Arial.ttf"))

    candidates.extend(
        [
            Path("/usr/share/fonts/truetype/liberation") / filename,
            Path("/usr/share/fonts/truetype/dejavu")
            / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
        ]
    )

    for font_path in candidates:
        try:
            if font_path.is_file():
                return ImageFont.truetype(str(font_path), size)
        except OSError:
            continue
    return ImageFont.load_default()
