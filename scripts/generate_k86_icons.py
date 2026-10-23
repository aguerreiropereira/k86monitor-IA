#!/usr/bin/env python3
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_k86_icon():
    size = 512
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Ambient drop shadow for the icon
    shadow = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle([32, 44, 480, 468], radius=50, fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    img.paste(shadow, (0, 0), shadow)

    # Keyboard chassis body (Dark sleek casing with chamfered rim)
    draw.rounded_rectangle([32, 40, 480, 464], radius=46, fill=(30, 36, 48, 255), outline=(58, 70, 92, 255), width=3)
    draw.rounded_rectangle([36, 44, 476, 460], radius=42, fill=(18, 22, 30, 255))

    # Top status panel area / recessed tray
    draw.rounded_rectangle([50, 58, 462, 218], radius=24, fill=(11, 14, 20, 255), outline=(28, 35, 48, 255), width=2)

    # Rotary knob on the top right (Attack Shark K86 signature volume & menu dial)
    knob_cx, knob_cy = 405, 138
    knob_r = 44
    draw.ellipse([knob_cx - knob_r - 2, knob_cy - knob_r + 4, knob_cx + knob_r + 2, knob_cy + knob_r + 8], fill=(4, 6, 8, 200))
    # Metallic textured ring
    draw.ellipse([knob_cx - knob_r, knob_cy - knob_r, knob_cx + knob_r, knob_cy + knob_r], fill=(52, 60, 74, 255), outline=(82, 95, 114, 255), width=3)
    # Inner face
    draw.ellipse([knob_cx - knob_r + 8, knob_cy - knob_r + 8, knob_cx + knob_r - 8, knob_cy + knob_r - 8], fill=(24, 28, 36, 255))
    # Cyan indicator notch
    draw.line([knob_cx, knob_cy - 30, knob_cx, knob_cy - 12], fill=(0, 238, 255, 255), width=5)
    # Center metallic cap
    draw.ellipse([knob_cx - 7, knob_cy - 7, knob_cx + 7, knob_cy + 7], fill=(42, 50, 64, 255), outline=(70, 82, 100, 255), width=1)

    # TFT Color Display Screen (Attack Shark K86 smart screen)
    screen_box = [66, 74, 338, 202]
    # Screen bezel with subtle cyan outer aura
    draw.rounded_rectangle(screen_box, radius=14, fill=(5, 7, 10, 255), outline=(0, 180, 215, 140), width=2)
    lcd_box = [72, 80, 332, 196]
    draw.rounded_rectangle(lcd_box, radius=9, fill=(7, 16, 26, 255))

    # Screen UI Header
    draw.rectangle([76, 84, 328, 97], fill=(10, 28, 44, 255))
    # Battery icon on screen
    draw.rounded_rectangle([82, 87, 98, 94], radius=2, outline=(0, 220, 240, 220), width=1)
    draw.rectangle([84, 89, 94, 92], fill=(0, 255, 200, 255))
    draw.rectangle([98, 89, 100, 92], fill=(0, 220, 240, 220))
    # Wi-Fi / BT icon dots
    draw.ellipse([106, 91, 109, 94], fill=(0, 220, 240, 255))
    draw.arc([103, 87, 112, 96], 200, 340, fill=(0, 220, 240, 220), width=1)
    # Status LED dot (green)
    draw.ellipse([316, 88, 323, 95], fill=(0, 255, 170, 255))

    # Fonts
    try:
        font_k86 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 38)
        font_sub = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 13)
        font_tag = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 9)
    except Exception:
        font_k86 = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_tag = ImageFont.load_default()

    # K86 Logo text & Glowing display graphic
    draw.text((82, 106), 'K86', fill=(0, 240, 255, 255), font=font_k86)
    draw.text((84, 148), 'TFT DISPLAY', fill=(0, 180, 220, 200), font=font_tag)

    # Sub labels
    draw.text((184, 108), 'STUDIO', fill=(220, 240, 255, 250), font=font_sub)
    draw.text((184, 124), 'MONITOR', fill=(0, 215, 200, 220), font=font_tag)

    # Animated-style graphic equalizer / CPU & Token usage waveform bars on TFT screen
    bars = [12, 18, 28, 22, 38, 48, 55, 42, 32, 45, 52, 40, 26, 16]
    for idx, bar_h in enumerate(bars):
        bx = 184 + idx * 10
        by_bottom = 186
        # gradient color from cyan to bright white/cyan
        c_green = min(255, int(160 + bar_h * 1.8))
        draw.line([bx, by_bottom, bx, by_bottom - bar_h], fill=(0, c_green, 255, 250), width=6)
        # peak dot
        draw.point([bx, by_bottom - bar_h - 2], fill=(200, 255, 255, 255))

    # Keyboard keys layout
    key_rows = [
        (234, 34, [(44, 'ctrl'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (48, 'accent')]),
        (276, 34, [(50, 'accent'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (42, 'ctrl')]),
        (318, 34, [(60, 'ctrl'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n')]),
        (360, 34, [(72, 'ctrl'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'n'), (32, 'accent'), (56, 'accent')]),
        (402, 36, [(48, 'ctrl'), (40, 'ctrl'), (40, 'ctrl'), (176, 'space'), (40, 'ctrl'), (40, 'ctrl')])
    ]

    key_colors = {
        'n': ((36, 44, 58, 255), (24, 30, 40, 255), (66, 80, 102, 255)),
        'ctrl': ((28, 34, 46, 255), (18, 22, 30, 255), (52, 64, 82, 255)),
        'accent': ((0, 150, 175, 255), (0, 105, 125, 255), (0, 220, 245, 255)),
        'space': ((0, 170, 190, 255), (0, 125, 140, 255), (60, 235, 255, 255)),
    }

    for ry, rh, keys in key_rows:
        rx = 54
        for kw, ktype in keys:
            bg, shadow_c, edge_c = key_colors[ktype]
            draw.rounded_rectangle([rx, ry + 2, rx + kw, ry + rh + 2], radius=6, fill=shadow_c)
            draw.rounded_rectangle([rx, ry, rx + kw, ry + rh], radius=6, fill=bg, outline=edge_c, width=1)
            if ktype in ('accent', 'space'):
                draw.line([rx + 4, ry + 3, rx + kw - 4, ry + 3], fill=(210, 255, 255, 140), width=1)
            rx += kw + 7

    # Export sizes
    sizes = [
        (256, Path.home() / ".local/share/icons/hicolor/256x256/apps/k86-display-studio.png"),
        (128, Path.home() / ".local/share/icons/hicolor/128x128/apps/k86-display-studio.png"),
        (64, Path.home() / ".local/share/icons/hicolor/64x64/apps/k86-display-studio.png"),
        (48, Path.home() / ".local/share/icons/hicolor/48x48/apps/k86-display-studio.png"),
    ]

    for s, path in sizes:
        path.parent.mkdir(parents=True, exist_ok=True)
        scaled = img.resize((s, s), Image.Resampling.LANCZOS)
        scaled.save(path, format="PNG", optimize=True)
        print(f"Generated {path} ({s}x{s})")

if __name__ == '__main__':
    create_k86_icon()
