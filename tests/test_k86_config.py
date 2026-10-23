"""Tests for k86_config module."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import k86_config


class TestK86Config(unittest.TestCase):
    def test_default_config(self):
        """Verifies default schema structure and values."""
        cfg = k86_config.DEFAULT_CONFIG
        self.assertIsInstance(cfg, dict)
        self.assertEqual(cfg.get("version"), 1)

        screen = cfg.get("screen", {})
        self.assertEqual(screen.get("width"), 240)
        self.assertEqual(screen.get("height"), 128)
        self.assertIs(screen.get("show_clock"), True)
        self.assertEqual(screen.get("brightness"), 4)

        providers = cfg.get("providers", {})
        for name in ("claude", "codex", "antigravity"):
            self.assertIn(name, providers)
            self.assertIs(providers[name].get("enabled"), True)
            self.assertIs(providers[name].get("show_5h"), True)
            self.assertIs(providers[name].get("show_weekly"), True)

        for name in ("copilot", "cursor", "opencode", "grok", "glm"):
            self.assertIn(name, providers)
            self.assertIs(providers[name].get("enabled"), False)
            self.assertIs(providers[name].get("show_5h"), True)
            self.assertIs(providers[name].get("show_weekly"), True)

        sys_metrics = cfg.get("system_metrics", {})
        self.assertIs(sys_metrics.get("enabled"), False)
        self.assertIs(sys_metrics.get("show_cpu"), False)
        self.assertIs(sys_metrics.get("show_ram"), False)

        daemon = cfg.get("daemon", {})
        self.assertEqual(daemon.get("refresh_seconds"), 15)

        # Check get_config_path
        expected_path = Path.home() / ".config" / "codenotch" / "k86_config.json"
        self.assertEqual(k86_config.get_config_path(), expected_path)

    def test_save_and_load(self):
        """Verifies saved config persists and matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "k86_config.json"

            # Create modified config
            custom_cfg = {
                "version": 1,
                "screen": {
                    "width": 240,
                    "height": 128,
                    "show_clock": False,
                    "brightness": 2,
                },
                "providers": {
                    "claude": {"enabled": False, "show_5h": False, "show_weekly": False},
                    "codex": {"enabled": True, "show_5h": True, "show_weekly": False},
                    "antigravity": {"enabled": True, "show_5h": False, "show_weekly": True},
                },
                "system_metrics": {
                    "enabled": True,
                    "show_cpu": True,
                    "show_ram": True,
                },
                "daemon": {
                    "refresh_seconds": 30,
                },
            }

            k86_config.save_config(custom_cfg, path=test_path)
            self.assertTrue(test_path.exists())

            loaded = k86_config.load_config(path=test_path)
            self.assertEqual(loaded, custom_cfg)

    def test_load_corrupted_fallback(self):
        """Verifies invalid JSON falls back gracefully to DEFAULT_CONFIG."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "k86_corrupt.json"

            # Write corrupted JSON string
            with open(test_path, "w", encoding="utf-8") as f:
                f.write("{ invalid json content ...")

            loaded = k86_config.load_config(path=test_path)
            self.assertEqual(loaded, k86_config.DEFAULT_CONFIG)

            # Write valid JSON that is not a dictionary (e.g. a list)
            with open(test_path, "w", encoding="utf-8") as f:
                f.write("[1, 2, 3]")

            loaded_list = k86_config.load_config(path=test_path)
            self.assertEqual(loaded_list, k86_config.DEFAULT_CONFIG)

            # Missing file fallback
            missing_path = Path(tmpdir) / "non_existent.json"
            loaded_missing = k86_config.load_config(path=missing_path)
            self.assertEqual(loaded_missing, k86_config.DEFAULT_CONFIG)

            # Mutation isolation check
            loaded_missing["version"] = 999
            self.assertEqual(k86_config.DEFAULT_CONFIG["version"], 1)

    def test_default_path_mock(self):
        """Verifies load_config and save_config work with get_config_path default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_default_path = Path(tmpdir) / "subdir" / "k86_config.json"
            with patch("k86_config.get_config_path", return_value=mock_default_path):
                # When file doesn't exist
                initial = k86_config.load_config()
                self.assertEqual(initial, k86_config.DEFAULT_CONFIG)

                # Save without explicit path
                custom = {"version": 1, "test_key": "test_val"}
                k86_config.save_config(custom)
                self.assertTrue(mock_default_path.exists())

                # Load without explicit path
                reloaded = k86_config.load_config()
                self.assertEqual(reloaded, custom)


if __name__ == "__main__":
    unittest.main()
