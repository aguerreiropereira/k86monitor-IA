#!/usr/bin/env python3
"""K86 Display Studio - Native GTK 4 / Libadwaita Desktop Window.

Provides real-time interactive preview and complete preference controls for the
Attack Shark K86 240x128 color keyboard screen.
"""
from __future__ import annotations

import copy
import io
import os
from pathlib import Path
import sys
from typing import Any, Optional

# PyInstaller stores bundled GTK introspection data beside the executable.
if getattr(sys, "frozen", False):
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    typelib_dir = bundle_root / "girepository-1.0"
    if typelib_dir.is_dir():
        existing = os.environ.get("GI_TYPELIB_PATH", "")
        os.environ["GI_TYPELIB_PATH"] = os.pathsep.join(
            part for part in (str(typelib_dir), existing) if part
        )

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
gi.require_version("Gio", "2.0")

from gi.repository import Adw, Gdk, Gio, GLib, Gtk
from PIL import Image

from k86_config import DEFAULT_CONFIG, get_config_path, load_config, save_config
from k86_renderer import render_display
import k86_service

APP_ID: str = "io.github.codenotch.k86studio"
SERVICE_NAME: str = "k86-screen.service"
IS_LINUX: bool = sys.platform.startswith("linux")

CUSTOM_CSS: str = """
.k86-preview-frame {
    background: #0b0e14;
    border: 2px solid #232c3d;
    border-radius: 12px;
    padding: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45);
}

.k86-preview-bezel {
    border: 1px solid #1a2233;
    border-radius: 6px;
    background: #06080e;
}
"""


def _install_custom_css() -> None:
    """Inject custom styling for keyboard screen bezel and frame preview."""
    try:
        display = Gdk.Display.get_default()
        if display is not None:
            provider = Gtk.CssProvider()
            provider.load_from_string(CUSTOM_CSS)
            Gtk.StyleContext.add_provider_for_display(
                display,
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )
    except Exception as e:
        print(f"Warning: Failed to install custom CSS: {e}", file=sys.stderr)


class MainWindow(Adw.ApplicationWindow):
    """Main application window with live preview and preferences."""

    def __init__(
        self,
        *args: Any,
        config: Optional[dict[str, Any]] = None,
        config_path: Optional[Path | str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.set_title("K86 Display Studio")
        self.set_default_size(620, 840)

        self.config_path: Path = Path(config_path) if config_path else get_config_path()
        self.config: dict[str, Any] = (
            copy.deepcopy(config) if config is not None else load_config(self.config_path)
        )
        self._loading: bool = True

        _install_custom_css()
        self._build_ui()
        self.load_ui_from_config(self.config)
        self._loading = False

        self.update_service_status()
        self.update_preview()

    def _build_ui(self) -> None:
        """Construct the Libadwaita window layout."""
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toast_overlay.set_child(main_box)

        # Header Bar
        self.header_bar = Adw.HeaderBar()
        title_widget = Adw.WindowTitle(
            title="K86 Display Studio",
            subtitle="Attack Shark K86 Display Controls",
        )
        self.header_bar.set_title_widget(title_widget)

        self.btn_save = Gtk.Button(label="Salvar & Aplicar")
        self.btn_save.add_css_class("suggested-action")
        self.btn_save.connect("clicked", self.on_save_clicked)
        self.header_bar.pack_end(self.btn_save)

        main_box.append(self.header_bar)

        # Scrolled container with clamped width
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        main_box.append(scrolled)

        clamp = Adw.Clamp(maximum_size=600)
        scrolled.set_child(clamp)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(16)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(16)
        content_box.set_margin_end(16)
        clamp.set_child(content_box)

        # 1. Live Preview Section
        preview_group = Adw.PreferencesGroup(
            title="Pré-visualização em Tempo Real",
            description="Visor panorâmico Attack Shark K86 (240x128 @ 2x escala — Modo Foco automático com 1 modelo)",
        )
        content_box.append(preview_group)

        frame_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        frame_box.set_halign(Gtk.Align.CENTER)
        frame_box.add_css_class("k86-preview-frame")

        self.preview_picture = Gtk.Picture()
        self.preview_picture.set_size_request(480, 256)
        self.preview_picture.set_can_shrink(False)
        self.preview_picture.add_css_class("k86-preview-bezel")
        frame_box.append(self.preview_picture)
        preview_group.add(frame_box)

        # 2. Providers Preferences Group
        self.group_providers = Adw.PreferencesGroup(
            title="Provedores de IA",
            description="Selecione quais serviços monitorar (ao ativar apenas 1, o Modo Foco em tela cheia é acionado)",
        )
        content_box.append(self.group_providers)

        self.switch_claude = Adw.SwitchRow(
            title="Claude Code",
            subtitle="Sessão de 5 horas e limite semanal do Claude",
        )
        self.switch_claude.connect("notify::active", self._on_setting_changed)
        self.group_providers.add(self.switch_claude)

        self.switch_codex = Adw.SwitchRow(
            title="OpenAI Codex",
            subtitle="Janela primária de 5 horas e limite de 7 dias",
        )
        self.switch_codex.connect("notify::active", self._on_setting_changed)
        self.group_providers.add(self.switch_codex)

        self.switch_antigravity = Adw.SwitchRow(
            title="Antigravity",
            subtitle="Cotas Gemini e telemetria de modelos Antigravity",
        )
        self.switch_antigravity.connect("notify::active", self._on_setting_changed)
        self.group_providers.add(self.switch_antigravity)

        self.switch_copilot = Adw.SwitchRow(
            title="GitHub Copilot",
            subtitle="Interações premium e cotas mensais de chat/code",
        )
        self.switch_copilot.connect("notify::active", self._on_setting_changed)
        self.group_providers.add(self.switch_copilot)

        self.switch_cursor = Adw.SwitchRow(
            title="Cursor",
            subtitle="Requisições rápidas e janela de uso do Cursor",
        )
        self.switch_cursor.connect("notify::active", self._on_setting_changed)
        self.group_providers.add(self.switch_cursor)

        self.switch_opencode = Adw.SwitchRow(
            title="OpenCode",
            subtitle="Janela de chamadas e cotas da sessão OpenCode",
        )
        self.switch_opencode.connect("notify::active", self._on_setting_changed)
        self.group_providers.add(self.switch_opencode)

        self.switch_grok = Adw.SwitchRow(
            title="xAI Grok",
            subtitle="Estatísticas e limites de requisições Grok",
        )
        self.switch_grok.connect("notify::active", self._on_setting_changed)
        self.group_providers.add(self.switch_grok)

        self.switch_glm = Adw.SwitchRow(
            title="Z.ai GLM",
            subtitle="Plano Z.ai / GLM Coding e consumo de tokens",
        )
        self.switch_glm.connect("notify::active", self._on_setting_changed)
        self.group_providers.add(self.switch_glm)

        # 3. Metrics Preferences Group
        self.group_metrics = Adw.PreferencesGroup(
            title="Métricas &amp; Janelas",
            description="Exibição de barras de progresso e estatísticas de uso",
        )
        content_box.append(self.group_metrics)

        self.switch_5h = Adw.SwitchRow(
            title="Limite de 5 Horas",
            subtitle="Exibir barra de progresso da janela de 5 horas",
        )
        self.switch_5h.connect("notify::active", self._on_setting_changed)
        self.group_metrics.add(self.switch_5h)

        self.switch_weekly = Adw.SwitchRow(
            title="Limite Semanal",
            subtitle="Exibir barra de progresso da janela de 7 dias",
        )
        self.switch_weekly.connect("notify::active", self._on_setting_changed)
        self.group_metrics.add(self.switch_weekly)

        self.switch_system = Adw.SwitchRow(
            title="Métricas do Sistema",
            subtitle="Exibir slot com uso de CPU e RAM local",
        )
        self.switch_system.connect("notify::active", self._on_setting_changed)
        self.group_metrics.add(self.switch_system)

        # 4. Display & Service Group
        self.group_display = Adw.PreferencesGroup(
            title="Visor &amp; Serviço",
            description="Comportamento da tela física e daemon em segundo plano",
        )
        content_box.append(self.group_display)

        self.switch_clock = Adw.SwitchRow(
            title="Relógio no Visor",
            subtitle="Exibir hora digital no canto superior do visor",
        )
        self.switch_clock.connect("notify::active", self._on_setting_changed)
        self.group_display.add(self.switch_clock)

        self.switch_start_on_login = Adw.SwitchRow(
            title="Iniciar daemon ao entrar no sistema",
            subtitle="Manter a tela sincronizada após entrar na sua conta",
        )
        self.group_display.add(self.switch_start_on_login)

        self.row_service = Adw.ActionRow(
            title=(
                "Serviço k86-screen.service"
                if IS_LINUX
                else "Serviço de sincronização"
            ),
            subtitle="Status: Verificando...",
        )
        self.btn_restart_service = Gtk.Button(label="Reiniciar daemon")
        self.btn_restart_service.set_valign(Gtk.Align.CENTER)
        self.btn_restart_service.connect("clicked", self.on_restart_service_clicked)
        self.row_service.add_suffix(self.btn_restart_service)
        self.group_display.add(self.row_service)

    def load_ui_from_config(self, cfg: dict[str, Any]) -> None:
        """Populate UI switches from a configuration dictionary."""
        self._loading = True

        screen = cfg.get("screen", {})
        self.switch_clock.set_active(screen.get("show_clock", True))
        daemon = cfg.get("daemon", {})
        if not isinstance(daemon, dict):
            daemon = {}
        self.switch_start_on_login.set_active(
            daemon.get("start_on_login", k86_service.is_autostart_enabled())
        )

        providers = cfg.get("providers", {})
        provider_mappings = (
            ("claude", self.switch_claude, True),
            ("codex", self.switch_codex, True),
            ("antigravity", self.switch_antigravity, True),
            ("copilot", self.switch_copilot, False),
            ("cursor", self.switch_cursor, False),
            ("opencode", self.switch_opencode, False),
            ("grok", self.switch_grok, False),
            ("glm", self.switch_glm, False),
        )

        for key, switch, default_enabled in provider_mappings:
            p_cfg = providers.get(key, {})
            switch.set_active(p_cfg.get("enabled", default_enabled))

        # 5h and weekly enabled if any provider has them active
        show_5h = any(
            p.get("show_5h", True)
            for p in providers.values()
            if isinstance(p, dict)
        )
        show_wk = any(
            p.get("show_weekly", True)
            for p in providers.values()
            if isinstance(p, dict)
        )
        self.switch_5h.set_active(show_5h)
        self.switch_weekly.set_active(show_wk)

        sys_metrics = cfg.get("system_metrics", {})
        self.switch_system.set_active(sys_metrics.get("enabled", False))

        self._loading = False

    def extract_config(self) -> dict[str, Any]:
        """Extract configuration dictionary from current UI switch states."""
        cfg = copy.deepcopy(self.config)

        if "screen" not in cfg or not isinstance(cfg["screen"], dict):
            cfg["screen"] = copy.deepcopy(DEFAULT_CONFIG["screen"])
        cfg["screen"]["show_clock"] = self.switch_clock.get_active()

        if "providers" not in cfg or not isinstance(cfg["providers"], dict):
            cfg["providers"] = copy.deepcopy(DEFAULT_CONFIG["providers"])

        show_5h_val = self.switch_5h.get_active()
        show_wk_val = self.switch_weekly.get_active()

        for key, switch in (
            ("claude", self.switch_claude),
            ("codex", self.switch_codex),
            ("antigravity", self.switch_antigravity),
            ("copilot", self.switch_copilot),
            ("cursor", self.switch_cursor),
            ("opencode", self.switch_opencode),
            ("grok", self.switch_grok),
            ("glm", self.switch_glm),
        ):
            if key not in cfg["providers"] or not isinstance(cfg["providers"][key], dict):
                cfg["providers"][key] = {"enabled": False, "show_5h": True, "show_weekly": True}
            cfg["providers"][key]["enabled"] = switch.get_active()
            cfg["providers"][key]["show_5h"] = show_5h_val
            cfg["providers"][key]["show_weekly"] = show_wk_val

        if "system_metrics" not in cfg or not isinstance(cfg["system_metrics"], dict):
            cfg["system_metrics"] = copy.deepcopy(DEFAULT_CONFIG["system_metrics"])

        sys_enabled = self.switch_system.get_active()
        cfg["system_metrics"]["enabled"] = sys_enabled
        cfg["system_metrics"]["show_cpu"] = sys_enabled
        cfg["system_metrics"]["show_ram"] = sys_enabled

        if "daemon" not in cfg or not isinstance(cfg["daemon"], dict):
            cfg["daemon"] = copy.deepcopy(DEFAULT_CONFIG["daemon"])
        cfg["daemon"]["start_on_login"] = self.switch_start_on_login.get_active()

        return cfg

    def update_preview(self) -> Gdk.Texture:
        """Render current configuration state to a 480x256 Gdk.Texture in the UI."""
        cfg = self.extract_config()
        img_240 = render_display(cfg)

        # Scale 2x for sharp pixel-perfect preview
        img_480 = img_240.resize((480, 256), Image.Resampling.NEAREST)

        bio = io.BytesIO()
        img_480.save(bio, format="PNG")
        gbytes = GLib.Bytes.new(bio.getvalue())
        texture = Gdk.Texture.new_from_bytes(gbytes)

        self.preview_picture.set_paintable(texture)
        return texture

    def _on_setting_changed(self, widget: Any, param_spec: Any = None) -> None:
        """Handle real-time toggle changes by re-rendering the live preview."""
        if not self._loading:
            self.update_preview()

    def get_service_status(self) -> str:
        """Check status of the platform's user daemon."""
        return k86_service.status_label()

    def update_service_status(self) -> str:
        """Refresh the status label in the UI action row."""
        status = self.get_service_status()
        self.row_service.set_subtitle(f"Status: {status}")
        if status == "Running":
            self.btn_restart_service.set_label("Reiniciar daemon")
        else:
            self.btn_restart_service.set_label("Iniciar daemon")
        return status

    def trigger_hot_reload(self) -> bool:
        """Restart the platform daemon so it applies the current configuration."""
        try:
            k86_service.restart()
            return True
        except Exception as e:
            print(f"Warning: Daemon restart failed: {e}", file=sys.stderr)
            return False

    def on_restart_service_clicked(self, button: Optional[Gtk.Button] = None) -> None:
        """Restart k86-screen.service and show confirmation toast."""
        was_running = self.get_service_status() == "Running"
        restarted = self.trigger_hot_reload()
        self.update_service_status()
        action = "reiniciado" if was_running else "iniciado"
        message = f"Daemon {action}." if restarted else "Não foi possível iniciar o daemon."
        toast = Adw.Toast.new(message)
        self.toast_overlay.add_toast(toast)

    def on_save_clicked(self, button: Optional[Gtk.Button] = None) -> None:
        """Save configuration atomically, trigger reload, and display toast."""
        cfg = self.extract_config()
        self.config = cfg
        save_config(cfg, path=self.config_path)

        autostart_updated = True
        try:
            should_start_on_login = cfg["daemon"]["start_on_login"]
            if k86_service.is_autostart_enabled() != should_start_on_login:
                k86_service.set_autostart(should_start_on_login)
        except Exception as e:
            autostart_updated = False
            print(f"Warning: Failed to update login startup setting: {e}", file=sys.stderr)

        restarted = self.trigger_hot_reload()
        self.update_service_status()

        if restarted and autostart_updated:
            message = "Configurações salvas e aplicadas!"
        elif not restarted and not autostart_updated:
            message = "Configurações salvas, mas o daemon e a inicialização falharam."
        elif not restarted:
            message = "Configurações salvas. O daemon não iniciou."
        else:
            message = "Configurações aplicadas, mas a inicialização automática falhou."
        toast = Adw.Toast.new(message)
        self.toast_overlay.add_toast(toast)


class K86DisplayStudioApp(Adw.Application):
    """Main Adwaita application class."""

    def __init__(self, **kwargs: Any) -> None:
        if "application_id" not in kwargs:
            kwargs["application_id"] = APP_ID
        if "flags" not in kwargs:
            kwargs["flags"] = Gio.ApplicationFlags.DEFAULT_FLAGS
        super().__init__(**kwargs)
        self.config_path: Optional[Path] = None

    def do_activate(self) -> None:
        """Handle application activation."""
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

        win = self.props.active_window
        if not win:
            win = MainWindow(application=self, config_path=self.config_path)
        win.present()


def main() -> None:
    """CLI Entry point."""
    app = K86DisplayStudioApp()
    sys.exit(app.run(sys.argv))


if __name__ == "__main__":
    if "--k86-start-daemon" in sys.argv[1:]:
        k86_service.start()
    elif "--k86-run-daemon" in sys.argv[1:]:
        from k86_trio_daemon import main as run_daemon

        run_daemon()
    else:
        main()
