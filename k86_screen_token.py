#!/usr/bin/env python3
"""
Attack Shark K86 Screen AI Token Monitor
Uses direct Linux hidraw ioctl communication on Interface 2.
"""
import os
import sys
import fcntl
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SCREEN_W = 128
SCREEN_H = 128
REPORT_LEN = 64
OP_SCREEN_CANWRITE_16 = 165
OP_SCREEN_DATA_16 = 37
CHUNK = 56

def HIDIOCSFEATURE(length):
    return (3 << 30) | (ord('H') << 8) | 0x06 | (length << 16)

def HIDIOCGFEATURE(length):
    return (3 << 30) | (ord('H') << 8) | 0x07 | (length << 16)

def encode_bit7(cmd_bytes):
    buf = bytearray(REPORT_LEN)
    buf[:len(cmd_bytes)] = bytes(cmd_bytes)
    buf[7] = (255 - (sum(buf[0:7]) & 0xff)) & 0xff
    return buf

def rgb565_be(r, g, b):
    v = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
    return bytes([(v >> 8) & 0xff, v & 0xff])

def frame_to_bytes(img):
    img = img.convert("RGB").resize((SCREEN_W, SCREEN_H))
    px = img.load()
    out = bytearray()
    # Column-major order: for x in 0..W-1: for y in 0..H-1:
    for x in range(SCREEN_W):
        for y in range(SCREEN_H):
            r, g, b = px[x, y]
            out += rgb565_be(r, g, b)
    return bytes(out)

class K86ScreenDirect:
    def __init__(self, device_path="/dev/hidraw6"):
        self.fd = os.open(device_path, os.O_RDWR)
        self.path = device_path

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def send_feature(self, cmd_bytes):
        payload = encode_bit7(cmd_bytes)
        req = bytearray([0x00]) + payload
        fcntl.ioctl(self.fd, HIDIOCSFEATURE(65), req)

    def query(self, cmd_bytes, wait=0.06):
        self.send_feature(cmd_bytes)
        time.sleep(wait)
        resp = bytearray(65)
        resp[0] = 0x00
        fcntl.ioctl(self.fd, HIDIOCGFEATURE(65), resp)
        return bytes(resp)

    def write_screen(self, img):
        rgbs = frame_to_bytes(img)
        byte_len = len(rgbs) # 32768
        pos = (0, 0, SCREEN_W, SCREEN_H)

        # Handshake packet
        s = bytearray(REPORT_LEN)
        s[0] = OP_SCREEN_CANWRITE_16
        s[1] = 0 # frame_index
        s[2] = 1 # all_frames
        s[3] = 0 # delay
        s[4] = byte_len & 0xff
        s[5] = (byte_len >> 8) & 0xff
        s[8], s[9], s[10], s[11] = pos[0] & 0xff, pos[1] & 0xff, pos[2] & 0xff, pos[3] & 0xff
        s[12], s[13], s[14], s[15] = pos[0] >> 8, pos[1] >> 8, pos[2] >> 8, pos[3] >> 8
        s[16] = (byte_len >> 16) & 0xff
        s[17] = (byte_len >> 24) & 0xff
        s[18] = 0 # layer / slot

        print("Executing screen handshake...")
        ready = False
        for attempt in range(1, 16):
            resp = self.query(s, wait=0.06)
            if len(resp) > 2 and resp[2] == 1:
                ready = True
                print(f"Handshake accepted on attempt {attempt}!")
                break
            time.sleep(0.05)

        if not ready:
            raise RuntimeError(f"Handshake rejected. Last response: {list(resp[:10])}")

        total_chunks = (byte_len + CHUNK - 1) // CHUNK
        print(f"Streaming {byte_len} bytes in {total_chunks} chunks...")

        for c in range(total_chunks):
            data = rgbs[c * CHUNK:(c + 1) * CHUNK]
            flen = len(data)
            if flen < CHUNK:
                data = data + bytes(CHUNK - flen)

            pkt = bytearray(REPORT_LEN)
            pkt[0] = OP_SCREEN_DATA_16
            pkt[1] = 0 # frame_index
            pkt[2] = 1 # all_frames
            pkt[3] = 0 # delay
            pkt[4] = c & 0xff
            pkt[5] = (c >> 8) & 0xff
            pkt[6] = flen
            pkt[8:8 + CHUNK] = data
            self.send_feature(pkt)
            time.sleep(0.001)

        print("All chunks sent successfully!")

def render_token_dashboard(model_name="GEMINI 3.8", total_tokens="42.8k", in_tokens="34,120", out_tokens="8,680", cost_str="$0.0142"):
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), color=(11, 14, 22))
    draw = ImageDraw.Draw(img)

    # Header bar
    draw.rectangle([(0, 0), (128, 22)], fill=(24, 30, 48))
    draw.line([(0, 22), (128, 22)], fill=(0, 210, 255), width=1)
    draw.text((6, 4), f"AI: {model_name}", fill=(0, 230, 255))

    # Total Tokens
    draw.text((6, 26), "TOTAL TOKENS", fill=(130, 145, 175))
    draw.text((6, 38), total_tokens, fill=(255, 255, 255))

    # Bar chart frame
    draw.rectangle([(6, 56), (122, 63)], outline=(50, 60, 85), fill=(18, 22, 34))
    # Active bar
    draw.rectangle([(7, 57), (78, 62)], fill=(0, 230, 160))

    # Input / Output
    draw.text((6, 68), f"In:  {in_tokens}", fill=(175, 190, 215))
    draw.text((6, 82), f"Out: {out_tokens}", fill=(175, 190, 215))

    # Footer separator & Cost
    draw.line([(6, 99), (122, 99)], fill=(40, 50, 70), width=1)
    draw.text((6, 104), f"Cost: {cost_str}", fill=(255, 195, 70))
    # Small status indicator dot
    draw.ellipse([(114, 108), (120, 114)], fill=(0, 255, 120))

    return img

if __name__ == "__main__":
    img = render_token_dashboard()
    preview_path = Path(__file__).resolve().parent / "assets" / "token_dashboard_preview.png"
    img.save(preview_path)

    screen = K86ScreenDirect("/dev/hidraw6")
    try:
        screen.write_screen(img)
        print("Done! Image successfully transmitted to Attack Shark K86 screen!")
    finally:
        screen.close()
