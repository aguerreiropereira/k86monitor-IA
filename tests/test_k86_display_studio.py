"""Unit and integration tests for K86 Display Studio GTK 4 / Libadwaita application."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gtk

import k86_config
import k86_display_studio


class TestK86DisplayStudio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize Libadwaita / GTK once
        Adw.init()

    def setUp(self):
        self.test_cfg = {
            "version": 1,
            "screen": {
                "width": 240,
                "height": 128,
                "show_clock": True,
                "brightness": 4,
            },
            "providers": {
                "claude": {"enabled": True, "show_5h": True, "show_weekly": True},
                "codex": {"enabled": True, "show_5h": True, "show_weekly": False},
                "antigravity": {"enabled": False, "show_5h": False, "show_weekly": False},
            },
            "system_metrics": {
                "enabled": False,
                "show_cpu": False,
                "show_ram": False,
            },
            "daemon": {
                "refresh_seconds": 15,
            },
        }

    def test_app_initialization(self):
        """Verifies K86DisplayStudioApp application id and class hierarchy."""
        app = k86_display_studio.K86DisplayStudioApp()
        self.assertEqual(app.get_application_id(), "io.github.codenotch.k86studio")
        self.assertIsInstance(app, Adw.Application)

    def test_window_creation_and_widget_binding(self):
        """Verifies MainWindow creates all required preference groups and controls."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = Path(tmpdir) / "k86_config.json"
            k86_config.save_config(self.test_cfg, path=cfg_path)

            win = k86_display_studio.MainWindow(config=self.test_cfg, config_path=cfg_path)
            self.assertIsInstance(win, Adw.ApplicationWindow)
            self.assertEqual(win.get_title(), "K86 Display Studio")

            # Verify widget references
            self.assertTrue(hasattr(win, "switch_claude"))
            self.assertTrue(hasattr(win, "switch_codex"))
            self.assertTrue(hasattr(win, "switch_antigravity"))
            self.assertTrue(hasattr(win, "switch_copilot"))
            self.assertTrue(hasattr(win, "switch_cursor"))
            self.assertTrue(hasattr(win, "switch_opencode"))
            self.assertTrue(hasattr(win, "switch_grok"))
            self.assertTrue(hasattr(win, "switch_glm"))
            self.assertTrue(hasattr(win, "switch_5h"))
            self.assertTrue(hasattr(win, "switch_weekly"))
            self.assertTrue(hasattr(win, "switch_system"))
            self.assertTrue(hasattr(win, "switch_clock"))
            self.assertTrue(hasattr(win, "btn_save"))
            self.assertTrue(hasattr(win, "preview_picture"))

            # Verify initial switch values match test_cfg
            self.assertTrue(win.switch_claude.get_active())
            self.assertTrue(win.switch_codex.get_active())
            self.assertFalse(win.switch_antigravity.get_active())
            self.assertFalse(win.switch_copilot.get_active())
            self.assertFalse(win.switch_cursor.get_active())
            self.assertFalse(win.switch_opencode.get_active())
            self.assertFalse(win.switch_grok.get_active())
            self.assertFalse(win.switch_glm.get_active())
            self.assertTrue(win.switch_clock.get_active())
            self.assertFalse(win.switch_system.get_active())

    def test_state_extraction(self):
        """Verifies extracting configuration dictionary accurately reflects UI state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = Path(tmpdir) / "k86_config.json"
            win = k86_display_studio.MainWindow(config=self.test_cfg, config_path=cfg_path)

            # Mutate UI toggles
            win.switch_claude.set_active(False)
            win.switch_antigravity.set_active(True)
            win.switch_system.set_active(True)
            win.switch_clock.set_active(False)
            win.switch_5h.set_active(False)
            win.switch_weekly.set_active(True)

            extracted = win.extract_config()
            self.assertEqual(extracted["version"], 1)
            self.assertFalse(extracted["screen"]["show_clock"])
            self.assertFalse(extracted["providers"]["claude"]["enabled"])
            self.assertTrue(extracted["providers"]["antigravity"]["enabled"])
            self.assertTrue(extracted["system_metrics"]["enabled"])
            self.assertTrue(extracted["system_metrics"]["show_cpu"])
            self.assertTrue(extracted["system_metrics"]["show_ram"])

            # Verify metric switches applied across providers
            for p in ("claude", "codex", "antigravity", "copilot", "cursor", "opencode", "grok", "glm"):
                self.assertFalse(extracted["providers"][p]["show_5h"])
                self.assertTrue(extracted["providers"][p]["show_weekly"])

    def test_live_preview_rendering(self):
        """Verifies update_preview generates a valid 480x256 Gdk.Texture."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = Path(tmpdir) / "k86_config.json"
            win = k86_display_studio.MainWindow(config=self.test_cfg, config_path=cfg_path)

            texture = win.update_preview()
            self.assertIsInstance(texture, Gdk.Texture)
            self.assertEqual(texture.get_width(), 480)
            self.assertEqual(texture.get_height(), 256)

            paintable = win.preview_picture.get_paintable()
            self.assertIsNotNone(paintable)
            self.assertEqual(paintable.get_intrinsic_width(), 480)
            self.assertEqual(paintable.get_intrinsic_height(), 256)

    def test_save_and_apply_action(self):
        """Verifies saving config writes to disk and triggers toast notification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = Path(tmpdir) / "k86_config.json"
            win = k86_display_studio.MainWindow(config=self.test_cfg, config_path=cfg_path)

            # Change a setting
            win.switch_clock.set_active(False)
            win.switch_claude.set_active(False)

            with patch("k86_display_studio.MainWindow.trigger_hot_reload") as mock_reload:
                win.on_save_clicked(None)
                mock_reload.assert_called_once()

            # Verify file was written and loaded content matches
            self.assertTrue(cfg_path.exists())
            saved = k86_config.load_config(path=cfg_path)
            self.assertFalse(saved["screen"]["show_clock"])
            self.assertFalse(saved["providers"]["claude"]["enabled"])

    def test_toggle_triggers_update_preview(self):
        """Verifies that changing any switch immediately updates the preview."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = Path(tmpdir) / "k86_config.json"
            win = k86_display_studio.MainWindow(config=self.test_cfg, config_path=cfg_path)

            with patch.object(win, "update_preview") as mock_preview:
                win.switch_claude.set_active(not win.switch_claude.get_active())
                mock_preview.assert_called()

    def test_service_status_and_restart(self):
        """Verifies k86-screen.service status query and restart invocation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = Path(tmpdir) / "k86_config.json"
            win = k86_display_studio.MainWindow(config=self.test_cfg, config_path=cfg_path)

            with patch("subprocess.run") as mock_sub:
                # Test active status
                mock_sub.return_value = MagicMock(stdout="active\n", returncode=0)
                status = win.get_service_status()
                self.assertEqual(status, "Running")

                # Test inactive status
                mock_sub.return_value = MagicMock(stdout="inactive\n", returncode=3)
                status = win.get_service_status()
                self.assertEqual(status, "Stopped")

                # Test restart action
                mock_sub.return_value = MagicMock(stdout="", returncode=0)
                win.on_restart_service_clicked(None)
                mock_sub.assert_any_call(
                    ["systemctl", "--user", "restart", "k86-screen.service"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )


if __name__ == "__main__":
    unittest.main()
