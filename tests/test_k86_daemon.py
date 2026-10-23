"""Tests for k86_trio_daemon module."""
import os
import signal
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from PIL import Image

import k86_trio_daemon


class TestK86Daemon(unittest.TestCase):
    def test_watched_files_list(self):
        """Verifies watched files include k86_config.json and all provider quota files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            cfg_path = base_dir / "k86_config.json"
            watched = k86_trio_daemon.get_watched_files(config_dir=base_dir, config_path=cfg_path)
            watched_names = [p.name for p in watched]
            self.assertIn("k86_config.json", watched_names)
            self.assertIn("usage.json", watched_names)
            self.assertIn("codex.json", watched_names)
            self.assertIn("antigravity.json", watched_names)
            self.assertIn("copilot.json", watched_names)
            self.assertIn("cursor.json", watched_names)
            self.assertIn("opencode-usage.json", watched_names)
            self.assertIn("grok.json", watched_names)
            self.assertIn("glm-usage.json", watched_names)
            self.assertEqual(len(watched), 9)

    def test_find_k86_hidraw(self):
        """Verifies dynamic detection of K86 interface 2 hidraw device."""
        detected = k86_trio_daemon.find_k86_hidraw()
        self.assertTrue(detected.startswith("/dev/hidraw"))

    def test_compute_state_hash_config_change(self):
        """Verifies state hash changes when k86_config.json is modified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            cfg_path = base_dir / "k86_config.json"
            cfg_path.write_text('{"daemon": {"refresh_seconds": 15}}', encoding="utf-8")

            hash1 = k86_trio_daemon.compute_state_hash(config_dir=base_dir, config_path=cfg_path, cur_minute="12:00")

            # Update mtime of k86_config.json
            new_time = time.time() + 10
            os.utime(cfg_path, (new_time, new_time))

            hash2 = k86_trio_daemon.compute_state_hash(config_dir=base_dir, config_path=cfg_path, cur_minute="12:00")
            self.assertNotEqual(hash1, hash2)

    def test_compute_state_hash_quota_change(self):
        """Verifies state hash changes when quota files change."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            cfg_path = base_dir / "k86_config.json"
            cfg_path.write_text('{}', encoding="utf-8")
            usage_path = base_dir / "usage.json"
            usage_path.write_text('{}', encoding="utf-8")

            hash1 = k86_trio_daemon.compute_state_hash(config_dir=base_dir, config_path=cfg_path, cur_minute="12:00")

            new_time = time.time() + 10
            os.utime(usage_path, (new_time, new_time))

            hash2 = k86_trio_daemon.compute_state_hash(config_dir=base_dir, config_path=cfg_path, cur_minute="12:00")
            self.assertNotEqual(hash1, hash2)

    def test_compute_state_hash_clock_toggle(self):
        """Verifies minute affects hash only when show_clock is True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            cfg_path = base_dir / "k86_config.json"

            # Case A: show_clock is True
            cfg_clock_on = {"screen": {"show_clock": True}}
            hash_on_min1 = k86_trio_daemon.compute_state_hash(
                cfg=cfg_clock_on, config_dir=base_dir, config_path=cfg_path, cur_minute="12:00"
            )
            hash_on_min2 = k86_trio_daemon.compute_state_hash(
                cfg=cfg_clock_on, config_dir=base_dir, config_path=cfg_path, cur_minute="12:01"
            )
            self.assertNotEqual(hash_on_min1, hash_on_min2)

            # Case B: show_clock is False
            cfg_clock_off = {"screen": {"show_clock": False}}
            hash_off_min1 = k86_trio_daemon.compute_state_hash(
                cfg=cfg_clock_off, config_dir=base_dir, config_path=cfg_path, cur_minute="12:00"
            )
            hash_off_min2 = k86_trio_daemon.compute_state_hash(
                cfg=cfg_clock_off, config_dir=base_dir, config_path=cfg_path, cur_minute="12:01"
            )
            self.assertEqual(hash_off_min1, hash_off_min2)

    def test_run_iteration_updates_screen_on_change(self):
        """Verifies run_iteration calls renderer and writes to screen on state change."""
        mock_screen = MagicMock()
        mock_screen_factory = MagicMock(return_value=mock_screen)
        dummy_img = Image.new("RGB", (240, 128))
        mock_renderer = MagicMock(return_value=dummy_img)

        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            cfg_path = base_dir / "k86_config.json"
            cfg_path.write_text('{"daemon": {"refresh_seconds": 15}}', encoding="utf-8")

            new_state, updated = k86_trio_daemon.run_iteration(
                last_state=None,
                device_path="/dev/test_hidraw",
                config_path=cfg_path,
                config_dir=base_dir,
                screen_factory=mock_screen_factory,
                renderer_func=mock_renderer,
            )

            self.assertTrue(updated)
            self.assertIsNotNone(new_state)
            mock_renderer.assert_called_once()
            mock_screen_factory.assert_called_once_with("/dev/test_hidraw")
            mock_screen.write_screen.assert_called_once_with(dummy_img)
            mock_screen.close.assert_called_once()

    def test_run_iteration_skips_when_unchanged(self):
        """Verifies run_iteration does not re-render or re-write if state has not changed."""
        mock_screen = MagicMock()
        mock_screen_factory = MagicMock(return_value=mock_screen)
        dummy_img = Image.new("RGB", (240, 128))
        mock_renderer = MagicMock(return_value=dummy_img)

        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            cfg_path = base_dir / "k86_config.json"
            cfg_path.write_text('{"daemon": {"refresh_seconds": 15}}', encoding="utf-8")

            with patch("time.strftime", return_value="12:00"):
                # First iteration to get current state
                state1, updated1 = k86_trio_daemon.run_iteration(
                    last_state=None,
                    device_path="/dev/test_hidraw",
                    config_path=cfg_path,
                    config_dir=base_dir,
                    screen_factory=mock_screen_factory,
                    renderer_func=mock_renderer,
                )
                self.assertTrue(updated1)

                mock_renderer.reset_mock()
                mock_screen_factory.reset_mock()

                # Second iteration with the same state and no file changes
                state2, updated2 = k86_trio_daemon.run_iteration(
                    last_state=state1,
                    device_path="/dev/test_hidraw",
                    config_path=cfg_path,
                    config_dir=base_dir,
                    screen_factory=mock_screen_factory,
                    renderer_func=mock_renderer,
                )

                self.assertFalse(updated2)
                self.assertEqual(state1, state2)
                mock_renderer.assert_not_called()
                mock_screen_factory.assert_not_called()

    def test_run_iteration_handles_screen_error_gracefully(self):
        """Verifies device write errors log warning without crashing daemon."""
        mock_screen = MagicMock()
        mock_screen.write_screen.side_effect = OSError("Device busy or disconnected")
        mock_screen_factory = MagicMock(return_value=mock_screen)
        dummy_img = Image.new("RGB", (240, 128))
        mock_renderer = MagicMock(return_value=dummy_img)

        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            cfg_path = base_dir / "k86_config.json"
            cfg_path.write_text('{}', encoding="utf-8")

            # Should not raise exception
            new_state, updated = k86_trio_daemon.run_iteration(
                last_state="prev_state",
                device_path="/dev/test_hidraw",
                config_path=cfg_path,
                config_dir=base_dir,
                screen_factory=mock_screen_factory,
                renderer_func=mock_renderer,
            )

            self.assertFalse(updated)
            self.assertEqual(new_state, "prev_state")
            mock_screen.close.assert_called_once()

    def test_get_refresh_interval(self):
        """Verifies refresh interval extraction with fallbacks and minimums."""
        self.assertEqual(k86_trio_daemon.get_refresh_interval({"daemon": {"refresh_seconds": 30}}), 30)
        self.assertEqual(k86_trio_daemon.get_refresh_interval({"daemon": {"refresh_seconds": 5}}), 5)
        # Default fallback
        self.assertEqual(k86_trio_daemon.get_refresh_interval({}), 15)
        self.assertEqual(k86_trio_daemon.get_refresh_interval(None), 15)
        # Clamped minimum to avoid 0 or negative busy loops
        self.assertEqual(k86_trio_daemon.get_refresh_interval({"daemon": {"refresh_seconds": -10}}), 1)

    def test_signal_handling(self):
        """Verifies signal handler marks daemon running flag False."""
        k86_trio_daemon._running = True
        k86_trio_daemon._signal_handler(signal.SIGTERM, None)
        self.assertFalse(k86_trio_daemon._running)

        k86_trio_daemon._running = True
        k86_trio_daemon._signal_handler(signal.SIGINT, None)
        self.assertFalse(k86_trio_daemon._running)


if __name__ == "__main__":
    unittest.main()
