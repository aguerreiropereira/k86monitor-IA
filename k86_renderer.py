"""Attack Shark K86 Screen - Dynamic Layout & Rendering Engine.

Generates pixel-perfect 240x128 RGB images and column-major RGB565 byte buffers
for the Attack Shark K86 physical display and live desktop preview.
"""
from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any, Optional

from PIL import Image, ImageDraw, ImageFont

from k86_config import get_data_dir, load_config
from k86_fonts import load_font

SCREEN_W: int = 240
SCREEN_H: int = 128

CONFIG_DIR: Path = get_data_dir()
ICONS_DIR: Path = CONFIG_DIR / "k86_icons"
ASSETS_DIR: Path = Path(__file__).resolve().parent / "assets"


def _get_font(font_name: str, size: int) -> ImageFont.ImageFont:
    """Load a system font appropriate for the current platform."""
    return load_font(font_name, size)


FONT_TITLE = _get_font("LiberationSans-Bold.ttf", 11)
FONT_SUB = _get_font("LiberationSans-Regular.ttf", 8)
FONT_LBL = _get_font("LiberationSans-Bold.ttf", 8)
FONT_VAL = _get_font("LiberationSans-Bold.ttf", 9)

FONT_FOCUS_TITLE = _get_font("LiberationSans-Bold.ttf", 11)
FONT_FOCUS_SUB = _get_font("LiberationSans-Regular.ttf", 8)
FONT_FOCUS_LBL = _get_font("LiberationSans-Bold.ttf", 9)
FONT_FOCUS_VAL = _get_font("LiberationSans-Bold.ttf", 14)
FONT_FOCUS_CLOCK = _get_font("LiberationSans-Bold.ttf", 10)


def load_live_stats(cfg: Optional[dict[str, Any]] = None) -> dict[str, dict[str, int]]:
    """Read live provider quotas and system metrics from Codenotch cache.

    Returns percentage values (0-100) for rolling windows (5h, weekly).
    Only samples system CPU/RAM if system_metrics is enabled.
    """
    stats: dict[str, dict[str, int]] = {
        "claude": {"h5": 0, "wk": 0},
        "codex": {"h5": 0, "wk": 0},
        "antigravity": {"h5": 0, "wk": 0},
        "copilot": {"h5": 0, "wk": 0},
        "cursor": {"h5": 0, "wk": 0},
        "opencode": {"h5": 0, "wk": 0},
        "grok": {"h5": 0, "wk": 0},
        "glm": {"h5": 0, "wk": 0},
    }

    # 1. Claude
    try:
        usage_file = CONFIG_DIR / "usage.json"
        if usage_file.is_file():
            c = json.loads(usage_file.read_text(encoding="utf-8"))
            for w in c.get("windows", []):
                if w.get("id") == "session":
                    stats["claude"]["h5"] = int(round(w.get("used", 0) * 100))
                elif w.get("id") == "weekly_all":
                    stats["claude"]["wk"] = int(round(w.get("used", 0) * 100))
    except Exception:
        pass

    # 2. Codex
    try:
        codex_file = CONFIG_DIR / "codex.json"
        if codex_file.is_file():
            cx = json.loads(codex_file.read_text(encoding="utf-8"))
            for w in cx.get("windows", []):
                if w.get("id") == "primary":
                    stats["codex"]["h5"] = int(round(w.get("used", 0) * 100))
                elif w.get("id") == "secondary":
                    stats["codex"]["wk"] = int(round(w.get("used", 0) * 100))
    except Exception:
        pass

    # 3. Antigravity (Gemini)
    try:
        ag_file = CONFIG_DIR / "antigravity.json"
        if ag_file.is_file():
            ag = json.loads(ag_file.read_text(encoding="utf-8"))
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

    # 4. GitHub Copilot
    try:
        cp_file = CONFIG_DIR / "copilot.json"
        if cp_file.is_file():
            cp = json.loads(cp_file.read_text(encoding="utf-8"))
            windows = cp.get("windows", [])
            for w in windows:
                if w.get("id") == "premium_interactions":
                    stats["copilot"]["h5"] = int(round(w.get("used", 0) * 100))
                elif w.get("id") == "chat":
                    stats["copilot"]["wk"] = int(round(w.get("used", 0) * 100))
            if not stats["copilot"]["h5"] and windows:
                stats["copilot"]["h5"] = int(round(windows[0].get("used", 0) * 100))
    except Exception:
        pass

    # 5. Cursor
    try:
        cs_file = CONFIG_DIR / "cursor.json"
        if cs_file.is_file():
            cs = json.loads(cs_file.read_text(encoding="utf-8"))
            windows = cs.get("windows", [])
            if len(windows) > 0:
                stats["cursor"]["h5"] = int(round(windows[0].get("used", 0) * 100))
            if len(windows) > 1:
                stats["cursor"]["wk"] = int(round(windows[1].get("used", 0) * 100))
    except Exception:
        pass

    # 6. OpenCode
    try:
        oc_file = CONFIG_DIR / "opencode-usage.json"
        if oc_file.is_file():
            oc = json.loads(oc_file.read_text(encoding="utf-8"))
            windows = oc.get("windows", [])
            if len(windows) > 0:
                stats["opencode"]["h5"] = int(round(windows[0].get("used", 0) * 100))
            if len(windows) > 1:
                stats["opencode"]["wk"] = int(round(windows[1].get("used", 0) * 100))
    except Exception:
        pass

    # 7. xAI Grok
    try:
        gk_file = CONFIG_DIR / "grok.json"
        if gk_file.is_file():
            gk = json.loads(gk_file.read_text(encoding="utf-8"))
            windows = gk.get("windows", [])
            if len(windows) > 0:
                stats["grok"]["h5"] = int(round(windows[0].get("used", 0) * 100))
            if len(windows) > 1:
                stats["grok"]["wk"] = int(round(windows[1].get("used", 0) * 100))
    except Exception:
        pass

    # 8. Z.ai GLM
    try:
        glm_file = CONFIG_DIR / "glm-usage.json"
        if glm_file.is_file():
            gl = json.loads(glm_file.read_text(encoding="utf-8"))
            windows = gl.get("windows", [])
            if len(windows) > 0:
                stats["glm"]["h5"] = int(round(windows[0].get("used", 0) * 100))
            if len(windows) > 1:
                stats["glm"]["wk"] = int(round(windows[1].get("used", 0) * 100))
    except Exception:
        pass

    # 4. Optional System Metrics (CPU / RAM)
    effective_cfg = cfg if cfg is not None else load_config()
    if effective_cfg.get("system_metrics", {}).get("enabled", False):
        try:
            import psutil
            cpu = int(round(psutil.cpu_percent(interval=None)))
            ram = int(round(psutil.virtual_memory().percent))
            stats["system"] = {"cpu": cpu, "ram": ram}
            stats["system_metrics"] = {"cpu": cpu, "ram": ram}
        except Exception:
            stats["system"] = {"cpu": 0, "ram": 0}
            stats["system_metrics"] = {"cpu": 0, "ram": 0}

    return stats


def _render_single_focus_screen(item: dict[str, Any], show_clock: bool) -> Image.Image:
    """Render an immersive full-screen 240x128 Focus Mode layout for a single provider."""
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), color=(8, 10, 16))
    draw = ImageDraw.Draw(img)

    # Left colored accent line
    draw.rectangle([(0, 0), (3, SCREEN_H - 1)], fill=item["c_h5"])

    # Header bar (y: 0..23)
    draw.rectangle([(0, 0), (SCREEN_W - 1, 23)], fill=(14, 18, 28))
    draw.line([(0, 23), (SCREEN_W - 1, 23)], fill=(32, 42, 60))

    # Header left badge & Title
    draw.rectangle([(8, 6), (10, 17)], fill=item["c_h5"])
    draw.text((16, 5), item["title"], fill=(255, 255, 255), font=FONT_FOCUS_TITLE)
    bbox = FONT_FOCUS_TITLE.getbbox(item["title"])
    t_w = bbox[2] - bbox[0]
    draw.text((16 + t_w + 8, 7), item["sub"], fill=(120, 135, 165), font=FONT_FOCUS_SUB)

    # Header right: clock & live dot
    if show_clock:
        cur_time = time.strftime("%H:%M")
        draw.text((192, 6), cur_time, fill=(140, 160, 190), font=FONT_FOCUS_CLOCK)
    draw.ellipse([(226, 8), (232, 14)], fill=(0, 230, 140))

    # Body left: 48x48 Logo Card (x: 8..64, y: 30..120)
    draw.rectangle([(8, 30), (64, 120)], fill=(13, 17, 26), outline=(35, 48, 70))
    icon_pasted = False

    # Look for 48x48 icon with robust fallbacks
    candidates = [
        ICONS_DIR / f"{item['key']}_48.png",
        ASSETS_DIR / f"{item['key']}_48.png",
    ]
    if item.get("icon_file"):
        candidates.append(ICONS_DIR / item["icon_file"].replace(".png", "_48.png"))
        candidates.append(ASSETS_DIR / item["icon_file"].replace(".png", "_48.png"))
        candidates.append(ICONS_DIR / f"{item['key']}.png")
        candidates.append(ASSETS_DIR / f"{item['key']}.png")
        candidates.append(ICONS_DIR / item["icon_file"])
        candidates.append(ASSETS_DIR / item["icon_file"])

    for p in candidates:
        if p and p.is_file():
            try:
                im_icon = Image.open(p).convert("RGBA")
                if im_icon.size != (48, 48):
                    im_icon = im_icon.resize((48, 48), Image.Resampling.LANCZOS)
                img.paste(im_icon, (12, 38), im_icon)
                icon_pasted = True
                break
            except Exception:
                pass

    if not icon_pasted:
        # Fallback initials inside card
        draw.text((22, 50), item["title"][:2], fill=item["c_h5"], font=FONT_FOCUS_VAL)

    # Status badge under logo
    draw.rectangle([(16, 96), (56, 112)], fill=(22, 28, 42), outline=(42, 52, 74))
    badge_txt = "PRO" if item["key"] in ("claude", "codex") else "FOCO"
    b_box = FONT_SUB.getbbox(badge_txt)
    b_w = b_box[2] - b_box[0]
    draw.text((36 - b_w // 2, 99), badge_txt, fill=item["c_h5"], font=FONT_SUB)

    # Collect active bars
    bars: list[dict[str, Any]] = []
    if item["show_5h"]:
        lbl_1 = "SESSÃO 5 HORAS" if item["lbl_5h"] == "5h" else item["lbl_5h"]
        bars.append({"lbl": lbl_1, "val": item["val_5h"], "color": item["c_h5"]})
    if item["show_weekly"]:
        lbl_2 = "LIMITE SEMANAL" if item["lbl_wk"] == "Wk" else item["lbl_wk"]
        bars.append({"lbl": lbl_2, "val": item["val_wk"], "color": item["c_wk"]})

    b_x1, b_x2 = 74, 230

    if len(bars) == 2:
        # Top metric
        draw.text((b_x1, 32), bars[0]["lbl"], fill=(140, 155, 180), font=FONT_FOCUS_LBL)
        v1_str = f"{bars[0]['val']}%"
        v1_bbox = FONT_FOCUS_VAL.getbbox(v1_str)
        v1_w = v1_bbox[2] - v1_bbox[0]
        draw.text((b_x2 - v1_w, 28), v1_str, fill=bars[0]["color"], font=FONT_FOCUS_VAL)

        draw.rectangle([(b_x1, 47), (b_x2, 56)], fill=(20, 26, 38), outline=(42, 52, 74))
        if bars[0]["val"] > 0:
            fill1_ratio = min(100, max(2, bars[0]["val"])) / 100.0
            fill1_w = b_x1 + int((b_x2 - b_x1) * fill1_ratio)
            draw.rectangle([(b_x1 + 1, 48), (fill1_w, 55)], fill=bars[0]["color"])

        # Bottom metric
        draw.text((b_x1, 68), bars[1]["lbl"], fill=(140, 155, 180), font=FONT_FOCUS_LBL)
        v2_str = f"{bars[1]['val']}%"
        v2_bbox = FONT_FOCUS_VAL.getbbox(v2_str)
        v2_w = v2_bbox[2] - v2_bbox[0]
        draw.text((b_x2 - v2_w, 64), v2_str, fill=bars[1]["color"], font=FONT_FOCUS_VAL)

        draw.rectangle([(b_x1, 83), (b_x2, 92)], fill=(20, 26, 38), outline=(42, 52, 74))
        if bars[1]["val"] > 0:
            fill2_ratio = min(100, max(2, bars[1]["val"])) / 100.0
            fill2_w = b_x1 + int((b_x2 - b_x1) * fill2_ratio)
            draw.rectangle([(b_x1 + 1, 84), (fill2_w, 91)], fill=bars[1]["color"])

        # Footer
        draw.text((b_x1, 104), "Attack Shark K86 • Modo Foco", fill=(75, 90, 115), font=FONT_SUB)

    elif len(bars) == 1:
        # Centered single metric with extra thick 14px bar
        draw.text((b_x1, 42), bars[0]["lbl"], fill=(150, 170, 200), font=FONT_FOCUS_TITLE)
        v_str = f"{bars[0]['val']}%"
        v_bbox = FONT_FOCUS_VAL.getbbox(v_str)
        v_w = v_bbox[2] - v_bbox[0]
        draw.text((b_x2 - v_w, 38), v_str, fill=bars[0]["color"], font=FONT_FOCUS_VAL)

        draw.rectangle([(b_x1, 62), (b_x2, 76)], fill=(20, 26, 38), outline=(42, 52, 74))
        if bars[0]["val"] > 0:
            fill_ratio = min(100, max(2, bars[0]["val"])) / 100.0
            fill_w = b_x1 + int((b_x2 - b_x1) * fill_ratio)
            draw.rectangle([(b_x1 + 1, 63), (fill_w, 75)], fill=bars[0]["color"])

        draw.text((b_x1, 92), "Monitoramento contínuo em tempo real", fill=(85, 100, 125), font=FONT_SUB)

    else:
        # 0 metrics enabled
        draw.text((b_x1, 60), "Modo Foco Ativo • Limites Ocultos", fill=(100, 120, 150), font=FONT_FOCUS_TITLE)

    # Outer perimeter frame
    draw.rectangle([(0, 0), (SCREEN_W - 1, SCREEN_H - 1)], outline=(45, 58, 80))

    return img


def _render_standby_screen(show_clock: bool) -> Image.Image:
    """Render an elegant standby/idle display when no items are active."""
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), color=(10, 14, 22))
    draw = ImageDraw.Draw(img)

    # Outer perimeter frame
    draw.rectangle([(0, 0), (SCREEN_W - 1, SCREEN_H - 1)], outline=(50, 70, 100))

    # Digital Clock
    if show_clock:
        cur_time = time.strftime("%H:%M")
        draw.text((205, 6), cur_time, fill=(130, 145, 175), font=FONT_VAL)

    # Standby Title & Subtitle centered
    title = "K86 DISPLAY STUDIO"
    sub = "Standby • No Active Providers"

    bbox_t = FONT_TITLE.getbbox(title)
    w_t = bbox_t[2] - bbox_t[0]
    draw.text(((SCREEN_W - w_t) // 2, 44), title, fill=(250, 252, 255), font=FONT_TITLE)

    bbox_s = FONT_SUB.getbbox(sub)
    w_s = bbox_s[2] - bbox_s[0]
    draw.text(((SCREEN_W - w_s) // 2, 64), sub, fill=(100, 115, 145), font=FONT_SUB)

    # Status dot centered
    dot_x = (SCREEN_W - 6) // 2
    draw.ellipse([(dot_x, 86), (dot_x + 5, 91)], fill=(0, 230, 140))

    return img


def render_display(
    cfg: Optional[dict[str, Any]] = None,
    stats: Optional[dict[str, dict[str, int]]] = None,
) -> Image.Image:
    """Render a 240x128 RGB Image dynamically based on active configuration."""
    if cfg is None:
        cfg = load_config()
    if stats is None:
        stats = load_live_stats(cfg)

    show_clock = cfg.get("screen", {}).get("show_clock", True)
    providers_cfg = cfg.get("providers", {})

    provider_defs = [
        ("claude", "claude.png", "CLAUDE", "Claude Code", (251, 191, 36), (245, 158, 11)),
        ("codex", "codex.png", "CODEX", "OpenAI Plus", (52, 211, 153), (16, 185, 129)),
        ("antigravity", "gemini.png", "ANTIGRAVITY", "Gemini", (56, 189, 248), (2, 132, 199)),
        ("copilot", "copilot.png", "COPILOT", "GitHub Copilot", (168, 85, 247), (139, 92, 246)),
        ("cursor", "cursor.png", "CURSOR", "Cursor", (34, 211, 238), (6, 182, 212)),
        ("opencode", "opencode.png", "OPENCODE", "OpenCode", (56, 189, 248), (14, 165, 233)),
        ("grok", "grok.png", "GROK", "xAI Grok", (241, 245, 249), (203, 213, 225)),
        ("glm", "glm.png", "GLM", "Z.ai GLM", (59, 130, 246), (37, 99, 235)),
    ]

    items: list[dict[str, Any]] = []

    for key, icon_file, title, sub, c_h5, c_wk in provider_defs:
        p_cfg = providers_cfg.get(key, {})
        if p_cfg.get("enabled", True):
            p_stats = stats.get(key, {})
            items.append({
                "key": key,
                "icon_file": icon_file,
                "title": title,
                "sub": sub,
                "c_h5": c_h5,
                "c_wk": c_wk,
                "show_5h": p_cfg.get("show_5h", True),
                "show_weekly": p_cfg.get("show_weekly", True),
                "val_5h": p_stats.get("h5", 0),
                "val_wk": p_stats.get("wk", 0),
                "lbl_5h": "5h",
                "lbl_wk": "Wk",
            })

    # Optional System Metrics card
    sys_cfg = cfg.get("system_metrics", {})
    if sys_cfg.get("enabled", False):
        s_stats = stats.get("system", stats.get("system_metrics", {}))
        items.append({
            "key": "system",
            "icon_file": None,
            "title": "SYSTEM",
            "sub": "CPU / RAM",
            "c_h5": (168, 85, 247),
            "c_wk": (147, 51, 234),
            "show_5h": sys_cfg.get("show_cpu", True),
            "show_weekly": sys_cfg.get("show_ram", True),
            "val_5h": s_stats.get("cpu", 0),
            "val_wk": s_stats.get("ram", 0),
            "lbl_5h": "CPU",
            "lbl_wk": "RAM",
        })

    # 0 items active: return Standby/Idle screen safely
    if not items:
        return _render_standby_screen(show_clock)

    # 1 item active: return full-screen immersive Focus Mode layout
    if len(items) == 1:
        return _render_single_focus_screen(items[0], show_clock)

    n_items = len(items)
    slot_h = SCREEN_H // n_items

    img = Image.new("RGB", (SCREEN_W, SCREEN_H), color=(6, 8, 14))
    draw = ImageDraw.Draw(img)

    for idx, item in enumerate(items):
        y0 = idx * slot_h
        y1 = SCREEN_H if idx == n_items - 1 else (idx + 1) * slot_h
        current_h = y1 - y0

        # Slot card background
        draw.rectangle([(0, y0), (SCREEN_W - 1, y1 - 1)], fill=(13, 16, 25))

        # Colored left accent
        draw.rectangle([(0, y0), (2, y1 - 1)], fill=item["c_h5"])

        # Icon positioning (24x24 or scaled if slot < 24)
        icon_pasted = False
        if item["icon_file"]:
            icon_path = ICONS_DIR / item["icon_file"]
            if not icon_path.is_file():
                icon_path = ASSETS_DIR / item["icon_file"]
            if icon_path.is_file():
                try:
                    icon_img = Image.open(icon_path).convert("RGBA")
                    if current_h < 26:
                        target_size = max(12, current_h - 4)
                        icon_img = icon_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
                        icon_y = y0 + (current_h - target_size) // 2
                    else:
                        icon_y = y0 + max(2, (current_h - 24) // 2)
                    img.paste(icon_img, (6, icon_y), icon_img)
                    icon_pasted = True
                except Exception:
                    pass

        if not icon_pasted:
            # Fallback stylized indicator box for items without icon
            icon_y = y0 + max(2, (current_h - 24) // 2)
            draw.rectangle([(8, icon_y + 4), (24, icon_y + 20)], fill=(22, 28, 42), outline=item["c_h5"])
            draw.text((12, icon_y + 6), item["title"][:2], fill=item["c_h5"], font=FONT_LBL)

        # Collect active bars for this item
        bars: list[dict[str, Any]] = []
        if item["show_5h"]:
            bars.append({
                "lbl": item["lbl_5h"],
                "val": item["val_5h"],
                "color": item["c_h5"],
            })
        if item["show_weekly"]:
            bars.append({
                "lbl": item["lbl_wk"],
                "val": item["val_wk"],
                "color": item["c_wk"],
            })

        # Calculate dynamic text and bar layout based on slot height and number of bars
        if n_items >= 5:
            y_title = y0 + 1
            y_sub = y0 + 2
            clock_y = y0 + 1
            dot_y = y0 + 3
            bar_h = 3
            if len(bars) == 2:
                bar_y_offsets = [y0 + 11, y0 + 17]
            elif len(bars) == 1:
                bar_y_offsets = [y0 + 13]
            else:
                bar_y_offsets = []
        elif n_items == 4:
            y_title = y0 + 1
            y_sub = y0 + 3
            clock_y = y0 + 1
            dot_y = y0 + 4
            bar_h = 4
            if len(bars) == 2:
                bar_y_offsets = [y0 + 14, y0 + 22]
            elif len(bars) == 1:
                bar_y_offsets = [y0 + 18]
            else:
                bar_y_offsets = []
        elif n_items == 3:
            y_title = y0 + 2
            y_sub = y0 + 4
            clock_y = y0 + 2
            dot_y = y0 + 5
            bar_h = 6
            if len(bars) == 2:
                bar_y_offsets = [y0 + 17, y0 + 28]
            elif len(bars) == 1:
                bar_y_offsets = [y0 + 22]
            else:
                bar_y_offsets = []
        elif n_items == 2:
            y_title = y0 + 6
            y_sub = y0 + 8
            clock_y = y0 + 6
            dot_y = y0 + 8
            bar_h = 7
            if len(bars) == 2:
                bar_y_offsets = [y0 + 25, y0 + 43]
            elif len(bars) == 1:
                bar_y_offsets = [y0 + 34]
            else:
                bar_y_offsets = []
        else:  # n_items == 1
            y_title = y0 + 16
            y_sub = y0 + 19
            clock_y = y0 + 16
            dot_y = y0 + 18
            bar_h = 9
            if len(bars) == 2:
                bar_y_offsets = [y0 + 52, y0 + 82]
            elif len(bars) == 1:
                bar_y_offsets = [y0 + 66]
            else:
                bar_y_offsets = []

        # Title & Subtitle
        draw.text((36, y_title), item["title"], fill=(250, 252, 255), font=FONT_TITLE)
        bbox = FONT_TITLE.getbbox(item["title"])
        w_title = bbox[2] - bbox[0]
        draw.text((36 + w_title + 6, y_sub), item["sub"], fill=(100, 115, 145), font=FONT_SUB)

        # Top right: Clock on first item if enabled, else active status dot
        if idx == 0 and show_clock:
            cur_time = time.strftime("%H:%M")
            draw.text((205, clock_y), cur_time, fill=(130, 145, 175), font=FONT_VAL)
        else:
            draw.ellipse([(228, dot_y), (233, dot_y + 5)], fill=(0, 230, 140))

        # Progress bars: x=52 to x=202 (150px wide)
        b_x1, b_x2 = 52, 202
        for b_idx, bar in enumerate(bars):
            y_b = bar_y_offsets[b_idx]
            val = bar["val"]
            color = bar["color"]
            lbl = bar["lbl"]

            # Label (36, y_b - 1)
            draw.text((36, y_b - 1), lbl, fill=(140, 155, 180), font=FONT_LBL)

            # Bar track
            draw.rectangle([(b_x1, y_b), (b_x2, y_b + bar_h)], fill=(22, 28, 42), outline=(42, 52, 74))

            # Bar fill
            if val > 0:
                fill_ratio = min(100, max(2, val)) / 100.0
                fill_w = b_x1 + int((b_x2 - b_x1) * fill_ratio)
                draw.rectangle([(b_x1 + 1, y_b + 1), (fill_w, y_b + bar_h - 1)], fill=color)

            # Percentage text
            draw.text((208, y_b - 2), f"{val}%", fill=color, font=FONT_VAL)

        # Horizontal divider line between items
        if idx < n_items - 1:
            draw.line([(0, y1 - 1), (SCREEN_W - 1, y1 - 1)], fill=(28, 35, 52))

    # Outer perimeter frame
    draw.rectangle([(0, 0), (SCREEN_W - 1, SCREEN_H - 1)], outline=(50, 70, 100))

    return img


def frame_to_rgb565(img: Image.Image) -> bytes:
    """Convert a PIL Image to big-endian column-major RGB565 byte array.

    Output length is strictly SCREEN_W * SCREEN_H * 2 = 61440 bytes.
    """
    img = img.convert("RGB")
    if img.size != (SCREEN_W, SCREEN_H):
        img = img.resize((SCREEN_W, SCREEN_H))

    # Transpose swaps (x, y) so row-major byte iteration corresponds to column-major of original
    transposed = img.transpose(Image.Transpose.TRANSPOSE)
    raw = transposed.tobytes()

    out = bytearray(SCREEN_W * SCREEN_H * 2)
    r_bytes = raw[0::3]
    g_bytes = raw[1::3]
    b_bytes = raw[2::3]

    for i in range(len(r_bytes)):
        r, g, b = r_bytes[i], g_bytes[i], b_bytes[i]
        v = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
        out[i * 2] = (v >> 8) & 0xFF
        out[i * 2 + 1] = v & 0xFF

    return bytes(out)
