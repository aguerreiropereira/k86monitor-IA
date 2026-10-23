"""Tests for k86_renderer module."""
import copy
import unittest
from PIL import Image

import k86_renderer


class TestK86Renderer(unittest.TestCase):
    def test_render_default_3_providers(self):
        """Verifies default rendering of 3 providers returns 240x128 RGB Image."""
        img = k86_renderer.render_display()
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (240, 128))
        self.assertEqual(img.size, (k86_renderer.SCREEN_W, k86_renderer.SCREEN_H))
        self.assertEqual(img.mode, "RGB")

    def test_render_2_providers(self):
        """Verifies rendering with 1 provider disabled returns 240x128 Image."""
        cfg = {
            "version": 1,
            "screen": {"width": 240, "height": 128, "show_clock": True, "brightness": 4},
            "providers": {
                "claude": {"enabled": True, "show_5h": True, "show_weekly": True},
                "codex": {"enabled": True, "show_5h": True, "show_weekly": False},
                "antigravity": {"enabled": False, "show_5h": False, "show_weekly": False},
            },
            "system_metrics": {"enabled": False, "show_cpu": False, "show_ram": False},
        }
        mock_stats = {
            "claude": {"h5": 42, "wk": 65},
            "codex": {"h5": 10, "wk": 20},
            "antigravity": {"h5": 0, "wk": 0},
        }
        img = k86_renderer.render_display(cfg=cfg, stats=mock_stats)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (240, 128))
        self.assertEqual(img.mode, "RGB")

    def test_render_1_provider(self):
        """Verifies rendering with exactly 1 provider invokes single-model focus mode."""
        cfg = {
            "version": 1,
            "screen": {"width": 240, "height": 128, "show_clock": True, "brightness": 4},
            "providers": {
                "claude": {"enabled": True, "show_5h": True, "show_weekly": True},
                "codex": {"enabled": False, "show_5h": False, "show_weekly": False},
                "antigravity": {"enabled": False, "show_5h": False, "show_weekly": False},
            },
            "system_metrics": {"enabled": False, "show_cpu": False, "show_ram": False},
        }
        mock_stats = {
            "claude": {"h5": 42, "wk": 78},
        }
        img = k86_renderer.render_display(cfg=cfg, stats=mock_stats)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (240, 128))
        self.assertEqual(img.mode, "RGB")

    def test_render_focus_mode_single_metric(self):
        """Verifies single-model focus mode when only 1 metric (5h) is active."""
        cfg = {
            "version": 1,
            "screen": {"width": 240, "height": 128, "show_clock": False, "brightness": 4},
            "providers": {
                "claude": {"enabled": False, "show_5h": False, "show_weekly": False},
                "codex": {"enabled": True, "show_5h": True, "show_weekly": False},
                "antigravity": {"enabled": False, "show_5h": False, "show_weekly": False},
            },
            "system_metrics": {"enabled": False, "show_cpu": False, "show_ram": False},
        }
        mock_stats = {
            "codex": {"h5": 85, "wk": 0},
        }
        img = k86_renderer.render_display(cfg=cfg, stats=mock_stats)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (240, 128))
        self.assertEqual(img.mode, "RGB")

    def test_render_focus_mode_all_providers(self):
        """Verifies focus mode can render each of the 8 providers individually."""
        for provider in ("claude", "codex", "antigravity", "copilot", "cursor", "opencode", "grok", "glm"):
            cfg = {
                "version": 1,
                "screen": {"width": 240, "height": 128, "show_clock": True, "brightness": 4},
                "providers": {
                    p: {"enabled": (p == provider), "show_5h": True, "show_weekly": True}
                    for p in ("claude", "codex", "antigravity", "copilot", "cursor", "opencode", "grok", "glm")
                },
                "system_metrics": {"enabled": False, "show_cpu": False, "show_ram": False},
            }
            mock_stats = {
                provider: {"h5": 50, "wk": 60},
            }
            img = k86_renderer.render_display(cfg=cfg, stats=mock_stats)
            self.assertIsInstance(img, Image.Image)
            self.assertEqual(img.size, (240, 128))

    def test_render_zero_providers_standby(self):
        """Verifies disabling all providers renders standby card without division-by-zero crash."""
        cfg = {
            "version": 1,
            "screen": {"width": 240, "height": 128, "show_clock": True, "brightness": 4},
            "providers": {
                "claude": {"enabled": False, "show_5h": False, "show_weekly": False},
                "codex": {"enabled": False, "show_5h": False, "show_weekly": False},
                "antigravity": {"enabled": False, "show_5h": False, "show_weekly": False},
            },
            "system_metrics": {"enabled": False, "show_cpu": False, "show_ram": False},
        }
        img = k86_renderer.render_display(cfg=cfg)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (240, 128))
        self.assertEqual(img.mode, "RGB")

    def test_frame_to_rgb565_length(self):
        """Verifies output length is strictly 240 * 128 * 2 = 61440 bytes."""
        img = Image.new("RGB", (240, 128), color=(20, 30, 40))
        buf = k86_renderer.frame_to_rgb565(img)
        self.assertIsInstance(buf, bytes)
        self.assertEqual(len(buf), 61440)

        # Non-standard image dimensions must auto-resize to 240x128
        img_resized = Image.new("RGB", (100, 50), color=(100, 150, 200))
        buf_resized = k86_renderer.frame_to_rgb565(img_resized)
        self.assertEqual(len(buf_resized), 61440)

    def test_frame_to_rgb565_column_major_and_big_endian(self):
        """Verifies buffer is big-endian and column-major."""
        img = Image.new("RGB", (240, 128))
        img.putpixel((0, 0), (255, 0, 0))    # (0, 0): index 0
        img.putpixel((0, 1), (0, 255, 0))    # (0, 1): index 1 in col-major -> byte offset 2
        img.putpixel((1, 0), (0, 0, 255))    # (1, 0): index 128 in col-major -> byte offset 256
        buf = k86_renderer.frame_to_rgb565(img)
        # Red in RGB565: 0xF800 -> big-endian: 0xF8, 0x00
        # Green in RGB565: 0x07E0 -> big-endian: 0x07, 0xE0
        # Blue in RGB565: 0x001F -> big-endian: 0x00, 0x1F
        self.assertEqual(buf[0:2], bytes([0xF8, 0x00]))
        self.assertEqual(buf[2:4], bytes([0x07, 0xE0]))
        self.assertEqual(buf[256:258], bytes([0x00, 0x1F]))

    def test_load_live_stats(self):
        """Verifies load_live_stats returns expected provider dictionary structure for all 8 providers."""
        stats = k86_renderer.load_live_stats()
        self.assertIsInstance(stats, dict)
        for provider in ("claude", "codex", "antigravity", "copilot", "cursor", "opencode", "grok", "glm"):
            self.assertIn(provider, stats)
            self.assertIn("h5", stats[provider])
            self.assertIn("wk", stats[provider])
            self.assertIsInstance(stats[provider]["h5"], int)
            self.assertIsInstance(stats[provider]["wk"], int)

    def test_render_new_providers(self):
        """Verifies rendering with newly added providers (copilot, cursor, opencode, grok, glm)."""
        cfg = {
            "version": 1,
            "screen": {"width": 240, "height": 128, "show_clock": True, "brightness": 4},
            "providers": {
                "claude": {"enabled": False, "show_5h": False, "show_weekly": False},
                "codex": {"enabled": False, "show_5h": False, "show_weekly": False},
                "antigravity": {"enabled": False, "show_5h": False, "show_weekly": False},
                "copilot": {"enabled": True, "show_5h": True, "show_weekly": True},
                "cursor": {"enabled": True, "show_5h": True, "show_weekly": True},
                "opencode": {"enabled": True, "show_5h": True, "show_weekly": True},
                "grok": {"enabled": True, "show_5h": True, "show_weekly": False},
                "glm": {"enabled": False, "show_5h": False, "show_weekly": False},
            },
            "system_metrics": {"enabled": False, "show_cpu": False, "show_ram": False},
        }
        mock_stats = {
            "copilot": {"h5": 55, "wk": 20},
            "cursor": {"h5": 30, "wk": 45},
            "opencode": {"h5": 10, "wk": 15},
            "grok": {"h5": 80, "wk": 0},
            "glm": {"h5": 0, "wk": 0},
        }
        img = k86_renderer.render_display(cfg=cfg, stats=mock_stats)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (240, 128))
        self.assertEqual(img.mode, "RGB")

    def test_load_live_stats_system_metrics(self):
        """Verifies system metrics inclusion when enabled."""
        cfg_sys = {
            "version": 1,
            "providers": {},
            "system_metrics": {"enabled": True, "show_cpu": True, "show_ram": True},
        }
        stats = k86_renderer.load_live_stats(cfg=cfg_sys)
        self.assertIn("system", stats)
        self.assertIn("cpu", stats["system"])
        self.assertIn("ram", stats["system"])


if __name__ == "__main__":
    unittest.main()
