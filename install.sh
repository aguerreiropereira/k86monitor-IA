#!/usr/bin/env bash
set -e

# ==============================================================================
# K86 Display Studio - Installer Script
# ==============================================================================

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"
SYSTEMD_USER_DIR="${HOME}/.config/systemd/user"

echo "🦈 Instalando K86 Display Studio..."
echo "📂 Repositório: ${REPO_DIR}"

mkdir -p "${BIN_DIR}" "${DESKTOP_DIR}" "${SYSTEMD_USER_DIR}"

# 1. Launcher da Interface Gráfica
echo "📦 Criando atalho em ${BIN_DIR}/k86-display-studio..."
cat <<EOF > "${BIN_DIR}/k86-display-studio"
#!/usr/bin/env bash
exec /usr/bin/python3 "${REPO_DIR}/k86_display_studio.py" "\$@"
EOF
chmod +x "${BIN_DIR}/k86-display-studio"

# 2. Launcher do Daemon
echo "📦 Criando launcher do daemon em ${BIN_DIR}/k86-screen-daemon..."
cat <<EOF > "${BIN_DIR}/k86-screen-daemon"
#!/usr/bin/env bash
exec /usr/bin/python3 "${REPO_DIR}/k86_trio_daemon.py" "\$@"
EOF
chmod +x "${BIN_DIR}/k86-screen-daemon"

# 3. Gerar ícones do aplicativo
echo "🎨 Gerando ícones do aplicativo..."
python3 "${REPO_DIR}/scripts/generate_k86_icons.py"

# 4. Criar entrada .desktop no menu de aplicativos
echo "🖥️  Instalando lançador de aplicativos..."
cat <<EOF > "${DESKTOP_DIR}/k86-display-studio.desktop"
[Desktop Entry]
Name=K86 Display Studio
Comment=Configurador do Visor do Teclado Attack Shark K86
Exec=${BIN_DIR}/k86-display-studio
Icon=k86-display-studio
Terminal=false
Type=Application
Categories=Utility;Settings;HardwareSettings;
StartupNotify=true
StartupWMClass=io.github.codenotch.k86studio
Keywords=attack;shark;k86;keyboard;display;screen;tft;ai;claude;codex;antigravity;
EOF
chmod +x "${DESKTOP_DIR}/k86-display-studio.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true
fi

# 5. Instalar serviço de usuário systemd
echo "⚙️  Instalando serviço systemd do usuário..."
cp "${REPO_DIR}/systemd/k86-screen.service" "${SYSTEMD_USER_DIR}/k86-screen.service"
systemctl --user daemon-reload 2>/dev/null || true

# 6. Informações sobre udev rules
echo ""
echo "✅ Instalação de usuário concluída com sucesso!"
echo ""
echo "📌 Próximos passos:"
echo "1. Para ativar o daemon de sincronização em segundo plano:"
echo "   systemctl --user enable --now k86-screen.service"
echo ""
echo "2. Se o teclado ainda não tiver permissão USB (hidraw):"
echo "   sudo cp \"${REPO_DIR}/udev/99-k86.rules\" /etc/udev/rules.d/"
echo "   sudo udevadm control --reload-rules && sudo udevadm trigger"
echo ""
echo "3. Você já pode abrir o 'K86 Display Studio' pelo menu ou rodando 'k86-display-studio'!"
