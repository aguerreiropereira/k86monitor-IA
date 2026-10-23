#!/usr/bin/env bash
set -e

# ==============================================================================
# K86 Display Studio - Uninstaller Script
# ==============================================================================

BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"

echo "🗑️ Desinstalando K86 Display Studio..."

# 1. Parar e desabilitar serviço systemd
systemctl --user stop k86-screen.service 2>/dev/null || true
systemctl --user disable k86-screen.service 2>/dev/null || true
rm -f "${SYSTEMD_USER_DIR}/k86-screen.service"
systemctl --user daemon-reload 2>/dev/null || true

# 2. Remover atalhos e executáveis
rm -f "${BIN_DIR}/k86-display-studio"
rm -f "${BIN_DIR}/k86-screen-daemon"
rm -f "${DESKTOP_DIR}/k86-display-studio.desktop"

# 3. Remover ícones
rm -f "${HOME}/.local/share/icons/hicolor/256x256/apps/k86-display-studio.png"
rm -f "${HOME}/.local/share/icons/hicolor/128x128/apps/k86-display-studio.png"
rm -f "${HOME}/.local/share/icons/hicolor/64x64/apps/k86-display-studio.png"
rm -f "${HOME}/.local/share/icons/hicolor/48x48/apps/k86-display-studio.png"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true
fi

echo "✅ K86 Display Studio desinstalado do usuário."
echo "Para remover as regras udev do sistema, execute manualmente:"
echo "   sudo rm -f /etc/udev/rules.d/99-k86.rules"
echo "   sudo udevadm control --reload-rules && sudo udevadm trigger"
