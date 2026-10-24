#!/usr/bin/env python3
"""
Attack Shark K86 Screen Calibration Ruler
Draws a color-coded horizontal ruler from 0 to 240 pixels with marked intervals
to determine the exact physical width of the display.
"""
import time
from PIL import Image, ImageDraw
from k86_trio_monitor import K86ScreenDirect
from k86_fonts import load_font

SCREEN_W = 240
SCREEN_H = 128
REPORT_LEN = 64
OP_SCREEN_CANWRITE_16 = 165
OP_SCREEN_DATA_16 = 37
CHUNK = 56

def _get_font(size):
    return load_font("LiberationSans-Bold.ttf", size)


FONT = _get_font(10)
FONT_SM = _get_font(8)

def rgb565_be(r, g, b):
    v = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
    return bytes([(v >> 8) & 0xff, v & 0xff])

def frame_to_bytes(img):
    img = img.convert("RGB").resize((SCREEN_W, SCREEN_H))
    px = img.load()
    out = bytearray()
    for x in range(SCREEN_W):
        for y in range(SCREEN_H):
            r, g, b = px[x, y]
            out += rgb565_be(r, g, b)
    return bytes(out)

def send_frame(img, w=240, h=128):
    rgbs = frame_to_bytes(img)
    byte_len = len(rgbs)

    s = bytearray(REPORT_LEN)
    s[0] = OP_SCREEN_CANWRITE_16
    s[1] = 0
    s[2] = 1
    s[3] = 0
    s[4] = byte_len & 0xff
    s[5] = (byte_len >> 8) & 0xff
    s[8], s[9], s[10], s[11] = 0, 0, w & 0xff, h & 0xff
    s[12], s[13], s[14], s[15] = 0, 0, w >> 8, h >> 8
    s[16] = (byte_len >> 16) & 0xff
    s[17] = (byte_len >> 24) & 0xff
    s[18] = 0

    screen = K86ScreenDirect()
    try:
        screen.query(s, wait=0.06)

        total_chunks = (byte_len + CHUNK - 1) // CHUNK
        for c in range(total_chunks):
            data = rgbs[c * CHUNK:(c + 1) * CHUNK]
            flen = len(data)
            if flen < CHUNK:
                data = data + bytes(CHUNK - flen)
            pkt = bytearray(REPORT_LEN)
            pkt[0] = OP_SCREEN_DATA_16
            pkt[1] = 0
            pkt[2] = 1
            pkt[3] = 0
            pkt[4] = c & 0xff
            pkt[5] = (c >> 8) & 0xff
            pkt[6] = flen
            pkt[8:8 + CHUNK] = data
            screen.send_feature(pkt)
            time.sleep(0.001)
    finally:
        screen.close()

def make_ruler():
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), (10, 15, 25))
    draw = ImageDraw.Draw(img)

    # Color bands
    bands = [
        (0, 128, (20, 30, 45), "0-128"),
        (128, 160, (20, 50, 40), "160"),
        (160, 180, (50, 45, 20), "180"),
        (180, 200, (60, 30, 20), "200"),
        (200, 220, (50, 20, 50), "220"),
        (220, 240, (60, 20, 20), "240"),
    ]

    for x1, x2, col, label in bands:
        draw.rectangle([(x1, 0), (x2, SCREEN_H)], fill=col)
        draw.line([(x2, 0), (x2, SCREEN_H)], fill=(200, 220, 255), width=1)
        draw.text((x1 + 2, 8), label, fill=(240, 240, 240), font=FONT)

    # Ruler marks at bottom
    draw.rectangle([(0, 80), (SCREEN_W, 128)], fill=(15, 18, 26))
    for x in range(0, SCREEN_W + 1, 10):
        h_line = 10 if (x % 20 == 0) else 5
        draw.line([(x, 128 - h_line), (x, 128)], fill=(255, 255, 255), width=1)
        if x % 20 == 0 and x > 60:
            draw.text((x - 8, 100), str(x), fill=(255, 220, 100), font=FONT_SM)

    draw.text((8, 40), "CALIBRATION RULER", fill=(0, 230, 255), font=FONT)
    draw.text((8, 55), "Veja qual numero toca", fill=(200, 200, 200), font=FONT_SM)
    draw.text((8, 67), "a borda direita!", fill=(200, 200, 200), font=FONT_SM)

    return img

if __name__ == "__main__":
    img = make_ruler()
    preview_path = Path(__file__).resolve().parent / "assets" / "k86_ruler_preview.png"
    img.save(preview_path)
    print("Sending 240x128 ruler pattern to keyboard...")
    send_frame(img, 240, 128)
    print("Done! Check keyboard screen for the rightmost visible number.")
