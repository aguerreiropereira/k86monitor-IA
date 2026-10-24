# PyInstaller spec shared by the Windows and macOS release builders.
import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent
APP_NAME = "K86 Display Studio"

hidden_imports = [
    "gi.repository.Adw",
    "gi.repository.Gdk",
    "gi.repository.Gio",
    "gi.repository.GLib",
    "gi.repository.Gtk",
    "hid",
    "psutil",
    "k86_trio_daemon",
    "k86_service",
    "k86_fonts",
    "k86_config",
    "k86_renderer",
    "k86_trio_monitor",
]
datas = [(str(ROOT / "assets"), "assets")]
binaries = []
if sys.platform == "win32":
    hidapi_dll = Path(sys.prefix) / "bin" / "libhidapi-0.dll"
    if hidapi_dll.is_file():
        binaries.append((str(hidapi_dll), "."))

a = Analysis(
    [str(ROOT / "k86_display_studio.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={
        "gi": {
            "icons": ["Adwaita", "hicolor"],
            "themes": ["Adwaita"],
            "languages": ["en"],
        }
    },
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    executable = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    app = BUNDLE(
        executable,
        name=f"{APP_NAME}.app",
        bundle_identifier="io.github.codenotch.k86studio",
        info_plist={
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": APP_NAME,
            "CFBundleVersion": "1.0.0",
            "LSMinimumSystemVersion": "12.0",
            "NSHighResolutionCapable": True,
        },
    )
else:
    executable = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
    )
    package = COLLECT(
        executable,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name=APP_NAME,
    )
