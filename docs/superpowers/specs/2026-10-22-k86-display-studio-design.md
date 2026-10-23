# K86 Display Studio — Design Specification

**Date:** 2026-10-22  
**Target Hardware:** Attack Shark K86 (ROYUAN OEM `0x3151:0x4015`, 240x128 TFT IPS screen)  
**Host Platform:** Linux (Ubuntu with GNOME, GTK 4, Libadwaita, Python 3)  
**Status:** Approved  

---

## 1. Overview & Objective

The **K86 Display Studio** is a native Linux desktop application built with Python, GTK 4, and Libadwaita. It allows the user to visually configure what metrics and providers are monitored on the Attack Shark K86's 240x128 color screen.

The application provides:
- A live visual preview replicating the physical keyboard display in real time.
- Toggles to enable/disable specific AI quota providers (Claude Code, OpenAI Codex, Antigravity/Gemini).
- Toggles for display metrics (5-Hour rolling limit, Weekly limit, System CPU/RAM usage).
- Display preferences (digital clock, update frequency, background service control).
- Automatic persistence and hot-reloading for the background hardware daemon.

---

## 2. Architecture & Data Flow

```
┌────────────────────────────────────────────────────────┐
│  K86 Display Studio (GTK 4 / Libadwaita Window)        │
│  - Live Preview Widget (Gtk.Picture / Gtk.Image)       │
│  - Adw.PreferencesGroup for Providers & Metrics        │
│  - Action buttons: "Salvar & Aplicar", Daemon Control  │
└───────────────────────────┬────────────────────────────┘
                            │ Writes on Save / Toggle
                            ▼
           ~/.config/codenotch/k86_config.json
                            ▲
                            │ Reads config & updates
┌───────────────────────────┴────────────────────────────┐
│  k86-screen.service (Systemd User Daemon)              │
│  - Reads: ~/.config/codenotch/*.json (Codenotch cache) │
│  - Renders: 240x128 RGB565 Column-Major Frame          │
│  - Transmits: USB HID via /dev/hidraw6 (Interface 2)   │
└────────────────────────────────────────────────────────┘
```

### 2.1 Configuration Schema (`k86_config.json`)

Stored at `~/.config/codenotch/k86_config.json`:

```json
{
  "version": 1,
  "screen": {
    "width": 240,
    "height": 128,
    "show_clock": true,
    "brightness": 4
  },
  "providers": {
    "claude": { "enabled": true, "show_5h": true, "show_weekly": true },
    "codex": { "enabled": true, "show_5h": true, "show_weekly": true },
    "antigravity": { "enabled": true, "show_5h": true, "show_weekly": true }
  },
  "system_metrics": {
    "enabled": false,
    "show_cpu": false,
    "show_ram": false
  },
  "daemon": {
    "refresh_seconds": 15
  }
}
```

---

## 3. Component Details

### 3.1 Live Preview Component
- Reuses the core image rendering engine from `k86_trio_monitor.py`.
- Generates a 240x128 PIL `Image` based on the active UI settings and live data from Codenotch cache.
- Scales the image cleanly (e.g. 2x to 480x256) inside a styled container card simulating the keyboard's bezel.
- Updates in real-time as the user toggles switches or sliders in the UI.

### 3.2 Preferences Interface (Libadwaita)
- **HeaderBar:** Title `K86 Display Studio`, "Salvar & Aplicar" primary button, service status indicator.
- **Preview Section:** Centered live display preview card.
- **Providers Group (`Adw.PreferencesGroup`):**
  - Claude Code switch row (`Adw.SwitchRow`) with icon.
  - OpenAI Codex switch row (`Adw.SwitchRow`) with icon.
  - Antigravity / Gemini switch row (`Adw.SwitchRow`) with icon.
- **Metrics Group (`Adw.PreferencesGroup`):**
  - "Janela de 5 Horas" (`show_5h`) toggle.
  - "Cota Semanal" (`show_weekly`) toggle.
  - "Métricas do Sistema (CPU/RAM)" toggle.
- **System & Daemon Group (`Adw.PreferencesGroup`):**
  - "Exibir Relógio no Display" toggle.
  - "Status do Serviço k86-screen" (Ativo / Inativo) with Start/Stop buttons.

### 3.3 Dynamic Layout Engine (`k86_renderer.py`)
- Given $N$ enabled slots (1 to 3 items):
  - Automatically calculates row height: `slot_h = 128 // N`.
  - Distributes vertical spacing and aligns 24x24 brand icons, title text, and 150px progress bars.
  - Renders to both PIL image (for preview) and RGB565 byte buffer (for hardware transmission).

### 3.4 Desktop Integration
- **CLI / Executable:** `~/.local/bin/k86-display-studio`.
- **Desktop Entry:** `~/.local/share/applications/k86-display-studio.desktop`.
- **App Icon:** Uses a 64x64 / 128x128 keyboard display icon installed to `~/.local/share/icons/hicolor/`.

---

## 4. Verification & Testing Plan

1. **Standalone GUI Launch:** Verify the GTK4/Libadwaita window opens cleanly without warnings and renders the 240x128 preview accurately.
2. **Settings Persistence:** Toggle providers/metrics, click save, verify `~/.config/codenotch/k86_config.json` is updated with valid JSON.
3. **Hardware Hot-Reload:** Verify that saving settings in the GUI triggers the background daemon (`k86-screen.service`) to update `/dev/hidraw6` within 1 second.
4. **Desktop Launcher:** Verify the application appears in GNOME app search and launches properly from the application menu.
