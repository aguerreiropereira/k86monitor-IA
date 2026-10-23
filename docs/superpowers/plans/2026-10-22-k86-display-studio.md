# K86 Display Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a native GTK 4 / Libadwaita desktop configuration application (`K86 Display Studio`) with real-time live preview for the Attack Shark K86 240x128 display, integrated with Codenotch and the systemd background daemon.

**Architecture:** A standalone GTK 4/Libadwaita GUI interacts with a configuration store (`k86_config.json`) and a modular rendering engine (`k86_renderer.py`). Toggling options updates both the on-screen live preview and the configuration file, which hot-reloads the hardware daemon (`k86-screen.service`) to immediately update the physical keyboard screen.

**Tech Stack:** Python 3, PyGObject (GTK 4.0, Libadwaita 1), Pillow (PIL), USB HID ioctl (`/dev/hidraw6`), systemd user service.

**Spec:** `docs/superpowers/specs/2026-10-22-k86-display-studio-design.md`

## Global Constraints

- Display hardware resolution: strictly `240x128` pixels (RGB565 big-endian column-major).
- GUI Framework: PyGObject with `gi.require_version('Gtk', '4.0')` and `gi.require_version('Adw', '1')`.
- Target files: stored in user space (`~/.config/codenotch/`, `~/.local/bin/`, `~/.local/share/applications/`).
- System compatibility: Ubuntu Linux / GNOME Wayland & X11 with zero external compilation dependencies.

## Review Focus

1. Corrupted or missing `k86_config.json`: Must fall back to safe default configuration without crashing.
2. Zero providers selected in GUI: Preview and keyboard must render a clean placeholder/standby card rather than dividing by zero.
3. Rapid toggling in GUI: Must debounce/protect screen updates without UI freeze or HID bus collision.
4. Daemon hot-reloading: Saving in GUI must update physical hardware without requiring manual service restarts.
5. System metrics (CPU/RAM) disabled: Must not invoke psutil or read `/proc/stat` needlessly.

---

### Task 1: Configuration Management (`k86_config.py`)

**Files:**
- Create: `k86_config.py`
- Test: `tests/test_k86_config.py`

**Interfaces:**
- Produces: `DEFAULT_CONFIG: dict`, `load_config() -> dict`, `save_config(cfg: dict) -> None`, `get_config_path() -> Path`.

- [ ] **Step 1: Write test for configuration loading, saving, and defaults**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `k86_config.py` with default schema, error handling, and JSON serialization**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Verify default configuration file is generated at `~/.config/codenotch/k86_config.json`**

---

### Task 2: Dynamic Layout & Renderer (`k86_renderer.py`)

**Files:**
- Create: `k86_renderer.py`
- Test: `tests/test_k86_renderer.py`

**Interfaces:**
- Consumes: `load_config()` from Task 1.
- Produces: `render_display(cfg: dict, stats: dict = None) -> PIL.Image`, `frame_to_rgb565(img: PIL.Image) -> bytes`.
- Supports dynamic $N$ slot allocation (1 to 3 items, CPU/RAM stats, 5h & Wkly bars, clock).

- [ ] **Step 1: Write test verifying rendering for 1, 2, and 3 active providers**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `k86_renderer.py` with dynamic height calculation, icon compositing, and bar scaling**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Generate sample test images for 1, 2, and 3 slots and verify visual fidelity**

---

### Task 3: Daemon Hot-Reload Bridge (`k86_trio_daemon.py`)

**Files:**
- Modify: `k86_trio_daemon.py`
- Consumes: `load_config()` from Task 1, `render_display()` from Task 2.

- [ ] **Step 1: Update daemon loop to monitor `k86_config.json` file modification time**
- [ ] **Step 2: Connect daemon to `render_display(cfg)` instead of hardcoded trio screen**
- [ ] **Step 3: Test modifying configuration and verify daemon immediately repaints keyboard display**
- [ ] **Step 4: Restart `k86-screen.service` to apply changes**

---

### Task 4: GTK 4 / Libadwaita Desktop Window (`k86_display_studio.py`)

**Files:**
- Create: `k86_display_studio.py`

**Interfaces:**
- Consumes: `k86_config.py`, `k86_renderer.py`.
- Produces: Native desktop application window `K86DisplayStudioApp`.

- [ ] **Step 1: Implement GTK 4 / Adw application shell with HeaderBar and "Salvar & Aplicar" button**
- [ ] **Step 2: Implement Live Preview component: displays 240x128 image scaled 2x (480x256) inside a styled keyboard card**
- [ ] **Step 3: Implement `Adw.PreferencesGroup` for Providers (Claude, Codex, Antigravity) with live preview updates on toggle**
- [ ] **Step 4: Implement `Adw.PreferencesGroup` for Metrics (5h limit, Weekly limit, CPU/RAM metrics)**
- [ ] **Step 5: Implement `Adw.PreferencesGroup` for Daemon Controls (Service Status, Restart button)**
- [ ] **Step 6: Test launching GUI, toggling switches, verifying real-time preview updates, and saving settings**

---

### Task 5: Desktop Launcher & System Integration

**Files:**
- Create: `~/.local/bin/k86-display-studio`
- Create: `~/.local/share/applications/k86-display-studio.desktop`
- Create: `~/.local/share/icons/hicolor/128x128/apps/k86-display-studio.png`

- [ ] **Step 1: Generate high-resolution desktop application icon (128x128 PNG)**
- [ ] **Step 2: Create launcher script in `~/.local/bin/k86-display-studio` with executable permissions**
- [ ] **Step 3: Install `.desktop` entry in `~/.local/share/applications/`**
- [ ] **Step 4: Run `update-desktop-database ~/.local/share/applications/`**
- [ ] **Step 5: Verify application appears in system desktop launcher and opens successfully**
