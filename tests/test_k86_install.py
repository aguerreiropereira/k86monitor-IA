#!/usr/bin/env python3
import os
import stat
import subprocess
import unittest
from pathlib import Path
from PIL import Image

LAUNCHER_PATH = Path.home() / ".local" / "bin" / "k86-display-studio"
DESKTOP_PATH = Path.home() / ".local" / "share" / "applications" / "k86-display-studio.desktop"
ICON_PATH = Path.home() / ".local" / "share" / "icons" / "hicolor" / "128x128" / "apps" / "k86-display-studio.png"

class TestK86Installation(unittest.TestCase):
    def setUp(self):
        if not LAUNCHER_PATH.exists():
            self.skipTest(f"K86 Display Studio is not installed at {LAUNCHER_PATH}; skip install verification.")
    def test_01_launcher_exists_and_executable(self):
        self.assertTrue(LAUNCHER_PATH.exists(), f"Launcher script does not exist at {LAUNCHER_PATH}")
        self.assertTrue(LAUNCHER_PATH.is_file(), f"{LAUNCHER_PATH} is not a regular file")
        mode = os.stat(LAUNCHER_PATH).st_mode
        self.assertTrue(bool(mode & stat.S_IXUSR), f"{LAUNCHER_PATH} is not executable by owner")
        content = LAUNCHER_PATH.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("#!"), "Launcher should have a shebang line")
        self.assertIn("k86_display_studio.py", content, "Launcher script should reference k86_display_studio.py")

    def test_02_icon_validity(self):
        self.assertTrue(ICON_PATH.exists(), f"Icon file does not exist at {ICON_PATH}")
        self.assertTrue(ICON_PATH.is_file(), f"{ICON_PATH} is not a regular file")
        
        # Verify PNG header
        with open(ICON_PATH, "rb") as f:
            header = f.read(8)
        self.assertEqual(header, b"\x89PNG\r\n\x1a\n", "Icon file does not have a valid PNG header")
        
        # Verify image properties using PIL
        with Image.open(ICON_PATH) as img:
            self.assertEqual(img.format, "PNG", f"Expected PNG format, got {img.format}")
            self.assertEqual(img.size, (128, 128), f"Expected 128x128 dimensions, got {img.size}")

    def test_03_desktop_entry_properties_and_validation(self):
        self.assertTrue(DESKTOP_PATH.exists(), f"Desktop file does not exist at {DESKTOP_PATH}")
        self.assertTrue(DESKTOP_PATH.is_file(), f"{DESKTOP_PATH} is not a regular file")
        
        content = DESKTOP_PATH.read_text(encoding="utf-8")
        self.assertIn("[Desktop Entry]", content, "Missing [Desktop Entry] section")
        
        # Parse basic INI-style desktop entry fields
        fields = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("["):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                fields[k.strip()] = v.strip()

        self.assertEqual(fields.get("Name"), "K86 Display Studio")
        self.assertEqual(fields.get("Exec"), str(LAUNCHER_PATH))
        self.assertEqual(fields.get("Icon"), "k86-display-studio")
        self.assertEqual(fields.get("Type"), "Application")
        self.assertEqual(fields.get("Terminal"), "false")
        self.assertIn("HardwareSettings", fields.get("Categories", ""))

        # Validate with desktop-file-validate if installed
        res = subprocess.run(["desktop-file-validate", str(DESKTOP_PATH)], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"desktop-file-validate failed: {res.stderr}\n{res.stdout}")

    def test_04_launcher_execution(self):
        self.assertTrue(LAUNCHER_PATH.exists(), f"Launcher does not exist at {LAUNCHER_PATH}")
        cmd = [str(LAUNCHER_PATH), "--help"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        self.assertEqual(res.returncode, 0, f"Launcher execution failed with code {res.returncode}: {res.stderr}")
        combined = (res.stdout + res.stderr).lower()
        self.assertTrue(
            "k86_display_studio" in combined or "ajuda" in combined or "help" in combined,
            f"Expected help text in launcher output, got: {res.stdout}"
        )

if __name__ == "__main__":
    unittest.main()
