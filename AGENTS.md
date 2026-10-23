# Repository Guidelines

## Project Structure & Module Organization

Application modules live in the repository root. `k86_display_studio.py` contains the GTK 4/Libadwaita interface, `k86_renderer.py` draws the 240×128 display, `k86_config.py` validates and persists settings, and `k86_trio_daemon.py` with `k86_trio_monitor.py` handles refresh and USB/HID output. Supporting utilities include `k86_screen_token.py` and `k86_calibrate_width.py`. Automated tests are in `tests/`, visual assets are in `assets/`, and design notes are in `docs/`. Keep new tests under `tests/` and reusable images or previews under `assets/`.

## Build, Test, and Development Commands

There is no separate build configuration; run the Python modules directly in an environment with their required system and Python dependencies installed.

- `python3 k86_display_studio.py` launches the desktop interface.
- `python3 k86_trio_daemon.py` starts the screen daemon; hardware output requires the K86 USB display and access to its HID device.
- `python3 -m unittest discover -s tests -p "test_*.py"` runs the full test suite without requiring a separate test framework.

## Coding Style & Naming Conventions

Follow the existing Python style: four-space indentation, `snake_case` for modules, functions, and variables, and `PascalCase` for classes. Keep module and public function docstrings descriptive. Prefer standard-library facilities and explicit type hints where the surrounding code uses them. No formatter or linter configuration is present, so keep changes consistent with neighboring code.

## Testing Guidelines

Use `unittest`; name test files `test_<area>.py`, test classes `Test<Area>`, and test methods `test_<behavior>`. Add focused tests for changed behavior, especially configuration validation, renderer output, daemon state changes, and UI actions. Use mocks or temporary paths for filesystem, service, and device interactions so unit tests do not depend on a running service or connected hardware.

## Commit & Pull Request Guidelines

Git history is unavailable in this checkout, so no repository-specific commit convention could be confirmed. Write concise, imperative commit subjects (for example, `Fix renderer slot spacing`). Pull requests should explain the behavior change, note relevant hardware or dependency assumptions, link an issue when applicable, and include screenshots for visible UI or display-rendering changes. Record the test command and its outcome.

## Configuration & Hardware Notes

User settings are stored at `~/.config/codenotch/k86_config.json`; do not commit personal configuration or device data. The display daemon communicates through Linux HID, so isolate device-specific behavior when making changes and keep configuration defaults safe for users without attached hardware.
