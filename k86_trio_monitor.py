#!/usr/bin/env python3
"""
Attack Shark K86 Screen - Panoramic 240x128 AI Monitor (Claude, Codex, Antigravity)
Calibrated for the full 240x128 physical panel width:
- Width = 240px, Height = 128px
- Official 24x24 brand icons
- 150px wide progress bars for 5h and Weekly limits
- Clock & Status indicators
"""
import os
import sys
import json
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from k86_config import get_data_dir
from k86_fonts import load_font

try:
    import fcntl
except ImportError:  # Windows and macOS use HIDAPI instead of Linux ioctl.
    fcntl = None

SCREEN_W = 240
SCREEN_H = 128
REPORT_LEN = 64
OP_SCREEN_CANWRITE_16 = 165
OP_SCREEN_DATA_16 = 37
CHUNK = 56

CONFIG_DIR = get_data_dir()
ICONS_DIR = CONFIG_DIR / "k86_icons"

# Fonts
def _get_font(filename: str, size: int) -> ImageFont.ImageFont:
    """Load a system font appropriate for the current platform."""
    return load_font(filename, size)


FONT_TITLE = _get_font("LiberationSans-Bold.ttf", 11)
FONT_SUB = _get_font("LiberationSans-Regular.ttf", 8)
FONT_LBL = _get_font("LiberationSans-Bold.ttf", 8)
FONT_VAL = _get_font("LiberationSans-Bold.ttf", 9)

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
    for x in range(SCREEN_W):
        for y in range(SCREEN_H):
            r, g, b = px[x, y]
            out += rgb565_be(r, g, b)
    return bytes(out)

def find_k86_hidraw() -> str:
    """Find the K86 screen interface through Linux hidraw."""
    if not sys.platform.startswith("linux"):
        raise RuntimeError("hidraw device discovery is only available on Linux")

    base = Path("/sys/class/hidraw")
    if base.is_dir():
        for hid in sorted(base.glob("hidraw*")):
            uevent = hid / "device" / "uevent"
            if uevent.is_file():
                try:
                    content = uevent.read_text(encoding="utf-8", errors="ignore")
                    if "00003151:00004015" in content and "input2" in content:
                        return f"/dev/{hid.name}"
                except OSError:
                    pass
    if os.path.exists("/dev/hidraw5"):
        return "/dev/hidraw5"
    return "/dev/hidraw6"


def find_k86_device() -> str | bytes:
    """Find the K86 screen-control HID interface on the current platform."""
    if sys.platform.startswith("linux"):
        return find_k86_hidraw()

    try:
        import hid
    except ImportError as exc:
        raise RuntimeError(
            "Cross-platform HID support requires the 'hidapi' Python package "
            "(install with: python -m pip install hidapi)."
        ) from exc

    devices = hid.enumerate(0x3151, 0x4015)
    for device in devices:
        if device.get("interface_number") == 2:
            return device["path"]

    raise OSError(
        "Attack Shark K86 screen interface (USB 3151:4015, interface 2) "
        "was not found. Check that the keyboard is connected."
    )


class K86ScreenDirect:
    def __init__(self, device_path=None):
        if device_path is None:
            device_path = find_k86_device()
        self.path = device_path
        self.fd = None
        self.device = None

        if sys.platform.startswith("linux"):
            if fcntl is None:
                raise RuntimeError("Linux hidraw support requires the fcntl module")
            self.fd = os.open(device_path, os.O_RDWR)
        else:
            try:
                import hid
            except ImportError as exc:
                raise RuntimeError(
                    "Cross-platform HID support requires the 'hidapi' Python "
                    "package (install with: python -m pip install hidapi)."
                ) from exc
            if hasattr(hid, "device"):
                self.device = hid.device()
                self.device.open_path(device_path)
            elif hasattr(hid, "Device"):
                self.device = hid.Device(path=device_path)
            else:
                raise RuntimeError(
                    "The installed HIDAPI Python package exposes no supported device API."
                )

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        if self.device is not None:
            self.device.close()
            self.device = None

    def send_feature(self, cmd_bytes):
        payload = encode_bit7(cmd_bytes)
        req = bytearray([0x00]) + payload
        if self.device is not None:
            result = self.device.send_feature_report(req)
            if result < 0:
                raise OSError("HID feature report write failed")
        else:
            fcntl.ioctl(self.fd, HIDIOCSFEATURE(65), req)

    def query(self, cmd_bytes, wait=0.06):
        self.send_feature(cmd_bytes)
        time.sleep(wait)
        resp = bytearray(65)
        resp[0] = 0x00
        if self.device is not None:
            response = self.device.get_feature_report(0, 65)
            if not response:
                raise OSError("HID feature report read returned no data")
            resp[:min(len(response), len(resp))] = bytes(response[:len(resp)])
        else:
            fcntl.ioctl(self.fd, HIDIOCGFEATURE(65), resp)
        return bytes(resp)

    def write_screen(self, img):
        rgbs = frame_to_bytes(img)
        byte_len = len(rgbs) # 240 * 128 * 2 = 61440
        pos = (0, 0, SCREEN_W, SCREEN_H)

        s = bytearray(REPORT_LEN)
        s[0] = OP_SCREEN_CANWRITE_16
        s[1] = 0
        s[2] = 1
        s[3] = 0
        s[4] = byte_len & 0xff
        s[5] = (byte_len >> 8) & 0xff
        s[8], s[9], s[10], s[11] = pos[0] & 0xff, pos[1] & 0xff, pos[2] & 0xff, pos[3] & 0xff
        s[12], s[13], s[14], s[15] = pos[0] >> 8, pos[1] >> 8, pos[2] >> 8, pos[3] >> 8
        s[16] = (byte_len >> 16) & 0xff
        s[17] = (byte_len >> 24) & 0xff
        s[18] = 0

        ready = False
        for _ in range(15):
            resp = self.query(s, wait=0.06)
            if len(resp) > 2 and resp[2] == 1:
                ready = True
                break
            time.sleep(0.05)

        if not ready:
            raise RuntimeError("Screen handshake failed.")

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
            self.send_feature(pkt)
            time.sleep(0.001)

def load_provider_stats():
    stats = {
        "claude": {"h5": 0, "wk": 0},
        "codex": {"h5": 0, "wk": 0},
        "antigravity": {"h5": 0, "wk": 0},
    }

    try:
        c = json.loads((CONFIG_DIR / "usage.json").read_text())
        for w in c.get("windows", []):
            if w.get("id") == "session":
                stats["claude"]["h5"] = int(round(w.get("used", 0) * 100))
            elif w.get("id") == "weekly_all":
                stats["claude"]["wk"] = int(round(w.get("used", 0) * 100))
    except Exception:
        pass

    try:
        cx = json.loads((CONFIG_DIR / "codex.json").read_text())
        for w in cx.get("windows", []):
            if w.get("id") == "primary":
                stats["codex"]["h5"] = int(round(w.get("used", 0) * 100))
            elif w.get("id") == "secondary":
                stats["codex"]["wk"] = int(round(w.get("used", 0) * 100))
    except Exception:
        pass

    try:
        ag = json.loads((CONFIG_DIR / "antigravity.json").read_text())
        for w in ag.get("windows", []):
            gid = w.get("id", "")
            grp = w.get("group", "")
            if "Gemini" in gid or "Gemini" in grp:
                if "Five Hour" in gid or "5-hour" in w.get("label", ""):
                    stats["antigravity"]["h5"] = int(round(w.get("used", 0) * 100))
                elif "Weekly" in gid or "Weekly" in w.get("label", ""):
                    stats["antigravity"]["wk"] = int(round(w.get("used", 0) * 100))
    except Exception:
        pass

    return stats

def render_panoramic_screen():
    stats = load_provider_stats()
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), color=(6, 8, 14))
    draw = ImageDraw.Draw(img)

    models_config = [
        ("claude", "claude.png", "CLAUDE", "Claude Code", (251, 191, 36), (245, 158, 11)),
        ("codex", "codex.png", "CODEX", "OpenAI Plus", (52, 211, 153), (16, 185, 129)),
        ("antigravity", "gemini.png", "ANTIGRAVITY", "Gemini", (56, 189, 248), (2, 132, 199)),
    ]

    y_starts = [0, 43, 86]

    for idx, (key, icon_file, title, sub, c_h5, c_wk) in enumerate(models_config):
        y0 = y_starts[idx]
        h5_pct = stats[key]["h5"]
        wk_pct = stats[key]["wk"]

        # Card background (0 to 239)
        draw.rectangle([(0, y0), (239, y0 + 41)], fill=(13, 16, 25))

        # Colored left accent
        draw.rectangle([(0, y0), (2, y0 + 41)], fill=c_h5)

        # 24x24 Icon
        icon_path = ICONS_DIR / icon_file
        if icon_path.exists():
            icon_img = Image.open(icon_path)
            img.paste(icon_img, (6, y0 + 9), icon_img)

        # Title & Sub
        draw.text((36, y0 + 2), title, fill=(250, 252, 255), font=FONT_TITLE)
        bbox = FONT_TITLE.getbbox(title)
        w_title = bbox[2] - bbox[0]
        draw.text((36 + w_title + 6, y0 + 4), sub, fill=(100, 115, 145), font=FONT_SUB)

        # Top right: Clock on first card, active status dot on others
        if idx == 0:
            cur_time = time.strftime("%H:%M")
            draw.text((205, y0 + 2), cur_time, fill=(130, 145, 175), font=FONT_VAL)
        else:
            draw.ellipse([(228, y0 + 5), (233, y0 + 10)], fill=(0, 230, 140))

        # Progress bars: from x=52 to x=202 (150px wide!)
        b_x1, b_x2 = 52, 202

        # 5h row
        draw.text((36, y0 + 16), "5h", fill=(140, 155, 180), font=FONT_LBL)
        draw.rectangle([(b_x1, y0 + 17), (b_x2, y0 + 23)], fill=(22, 28, 42), outline=(42, 52, 74))
        if h5_pct > 0:
            fill_w = b_x1 + int((b_x2 - b_x1) * (min(100, max(2, h5_pct)) / 100.0))
            draw.rectangle([(b_x1 + 1, y0 + 18), (fill_w, y0 + 22)], fill=c_h5)
        draw.text((208, y0 + 15), f"{h5_pct}%", fill=c_h5, font=FONT_VAL)

        # Weekly row
        draw.text((36, y0 + 27), "Wk", fill=(140, 155, 180), font=FONT_LBL)
        draw.rectangle([(b_x1, y0 + 28), (b_x2, y0 + 34)], fill=(22, 28, 42), outline=(42, 52, 74))
        if wk_pct > 0:
            fill_w = b_x1 + int((b_x2 - b_x1) * (min(100, max(2, wk_pct)) / 100.0))
            draw.rectangle([(b_x1 + 1, y0 + 29), (fill_w, y0 + 33)], fill=c_wk)
        draw.text((208, y0 + 26), f"{wk_pct}%", fill=c_wk, font=FONT_VAL)

        # Divider line
        if idx < 2:
            draw.line([(0, y0 + 42), (239, y0 + 42)], fill=(28, 35, 52))

    # Outer perimeter frame
    draw.rectangle([(0, 0), (239, 127)], outline=(50, 70, 100))

    return img

if __name__ == "__main__":
    img = render_panoramic_screen()
    preview_path = Path(__file__).resolve().parent / "assets" / "k86_panoramic_preview.png"
    img.save(preview_path)

    screen = K86ScreenDirect()
    try:
        screen.write_screen(img)
        print("Panoramic 240x128 Dashboard sent to Attack Shark K86 successfully!")
    finally:
        screen.close()
