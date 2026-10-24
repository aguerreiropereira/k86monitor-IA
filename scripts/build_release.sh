#!/usr/bin/env bash
set -e

# ==============================================================================
# K86 Display Studio - Release Packaging Script
# Generates .deb (Debian/Ubuntu) and .tar.gz (Universal) release packages
# ==============================================================================

VERSION="${1:-1.0.0}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${REPO_DIR}/dist"
BUILD_DIR="${REPO_DIR}/build"
PKG_NAME="k86monitor-ia"

echo "📦 Construindo Release v${VERSION} de ${PKG_NAME}..."

rm -rf "${BUILD_DIR}"
mkdir -p "${DIST_DIR}" "${BUILD_DIR}"

# ------------------------------------------------------------------------------
# 1. Gerar Pacote Universal .tar.gz
# ------------------------------------------------------------------------------
echo "🗜️  Criando arquivo tar.gz..."
TAR_DIR="${BUILD_DIR}/${PKG_NAME}-${VERSION}"
mkdir -p "${TAR_DIR}"

cp -r "${REPO_DIR}/k86_display_studio.py" \
      "${REPO_DIR}/k86_renderer.py" \
      "${REPO_DIR}/k86_config.py" \
      "${REPO_DIR}/k86_fonts.py" \
      "${REPO_DIR}/k86_trio_daemon.py" \
      "${REPO_DIR}/k86_service.py" \
      "${REPO_DIR}/k86_trio_monitor.py" \
      "${REPO_DIR}/k86_screen_token.py" \
      "${REPO_DIR}/k86_calibrate_width.py" \
      "${REPO_DIR}/install.sh" \
      "${REPO_DIR}/uninstall.sh" \
      "${REPO_DIR}/README.md" \
      "${REPO_DIR}/requirements.txt" \
      "${REPO_DIR}/LICENSE" \
      "${REPO_DIR}/assets" \
      "${REPO_DIR}/scripts" \
      "${REPO_DIR}/packaging" \
      "${REPO_DIR}/systemd" \
      "${REPO_DIR}/udev" \
      "${TAR_DIR}/"

# Limpar caches residuais na pasta de build
find "${TAR_DIR}" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

tar -czf "${DIST_DIR}/${PKG_NAME}-${VERSION}.tar.gz" -C "${BUILD_DIR}" "${PKG_NAME}-${VERSION}"
echo "✅ Gerado: ${DIST_DIR}/${PKG_NAME}-${VERSION}.tar.gz"

# ------------------------------------------------------------------------------
# 2. Gerar Pacote Debian/Ubuntu .deb
# ------------------------------------------------------------------------------
if command -v dpkg-deb >/dev/null 2>&1; then
    echo "📦 Criando pacote Debian (.deb)..."
    DEB_ROOT="${BUILD_DIR}/deb/${PKG_NAME}_${VERSION}_all"
    mkdir -p "${DEB_ROOT}/DEBIAN" \
             "${DEB_ROOT}/usr/bin" \
             "${DEB_ROOT}/usr/lib/${PKG_NAME}" \
             "${DEB_ROOT}/usr/share/applications" \
             "${DEB_ROOT}/usr/share/icons/hicolor/128x128/apps" \
             "${DEB_ROOT}/usr/share/icons/hicolor/256x256/apps" \
             "${DEB_ROOT}/usr/share/icons/hicolor/64x64/apps" \
             "${DEB_ROOT}/usr/share/icons/hicolor/48x48/apps" \
             "${DEB_ROOT}/usr/lib/systemd/user" \
             "${DEB_ROOT}/lib/udev/rules.d"

    # Arquivo de controle DEBIAN/control
    cat <<EOF > "${DEB_ROOT}/DEBIAN/control"
Package: ${PKG_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-pil, python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1
Maintainer: Anderson Guerreiro <aguerreiropereira@proton.me>
Description: Attack Shark K86 Keyboard Display Studio & AI Quota Monitor
 Native GTK 4 and Libadwaita control panel and background daemon for the
 Attack Shark K86 240x128 color LCD screen.
EOF

    # Script postinst (executado após a instalação)
    cat <<'EOF' > "${DEB_ROOT}/DEBIAN/postinst"
#!/bin/sh
set -e
if command -v udevadm >/dev/null 2>&1; then
    udevadm control --reload-rules 2>/dev/null || true
    udevadm trigger 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database 2>/dev/null || true
fi
exit 0
EOF
    chmod 755 "${DEB_ROOT}/DEBIAN/postinst"

    # Script postrm (executado após a remoção)
    cat <<'EOF' > "${DEB_ROOT}/DEBIAN/postrm"
#!/bin/sh
set -e
if command -v udevadm >/dev/null 2>&1; then
    udevadm control --reload-rules 2>/dev/null || true
    udevadm trigger 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database 2>/dev/null || true
fi
exit 0
EOF
    chmod 755 "${DEB_ROOT}/DEBIAN/postrm"

    # Código do app em /usr/lib/k86monitor-ia
    cp -r "${REPO_DIR}/k86_display_studio.py" \
          "${REPO_DIR}/k86_renderer.py" \
          "${REPO_DIR}/k86_config.py" \
          "${REPO_DIR}/k86_fonts.py" \
          "${REPO_DIR}/k86_trio_daemon.py" \
          "${REPO_DIR}/k86_service.py" \
          "${REPO_DIR}/k86_trio_monitor.py" \
          "${REPO_DIR}/k86_screen_token.py" \
          "${REPO_DIR}/k86_calibrate_width.py" \
          "${REPO_DIR}/assets" \
          "${DEB_ROOT}/usr/lib/${PKG_NAME}/"

    # Executáveis em /usr/bin
    cat <<EOF > "${DEB_ROOT}/usr/bin/k86-display-studio"
#!/bin/sh
exec /usr/bin/python3 /usr/lib/${PKG_NAME}/k86_display_studio.py "\$@"
EOF
    chmod 755 "${DEB_ROOT}/usr/bin/k86-display-studio"

    cat <<EOF > "${DEB_ROOT}/usr/bin/k86-screen-daemon"
#!/bin/sh
exec /usr/bin/python3 /usr/lib/${PKG_NAME}/k86_trio_daemon.py "\$@"
EOF
    chmod 755 "${DEB_ROOT}/usr/bin/k86-screen-daemon"

    # Desktop entry em /usr/share/applications
    cat <<EOF > "${DEB_ROOT}/usr/share/applications/k86-display-studio.desktop"
[Desktop Entry]
Name=K86 Display Studio
Comment=Configurador do Visor do Teclado Attack Shark K86
Exec=/usr/bin/k86-display-studio
Icon=k86-display-studio
Terminal=false
Type=Application
Categories=Utility;Settings;HardwareSettings;
StartupNotify=true
StartupWMClass=io.github.codenotch.k86studio
Keywords=attack;shark;k86;keyboard;display;screen;tft;ai;claude;codex;antigravity;
EOF

    # Ícones
    if [ -f "${HOME}/.local/share/icons/hicolor/128x128/apps/k86-display-studio.png" ]; then
        cp "${HOME}/.local/share/icons/hicolor/128x128/apps/k86-display-studio.png" "${DEB_ROOT}/usr/share/icons/hicolor/128x128/apps/"
        cp "${HOME}/.local/share/icons/hicolor/256x256/apps/k86-display-studio.png" "${DEB_ROOT}/usr/share/icons/hicolor/256x256/apps/"
        cp "${HOME}/.local/share/icons/hicolor/64x64/apps/k86-display-studio.png" "${DEB_ROOT}/usr/share/icons/hicolor/64x64/apps/"
        cp "${HOME}/.local/share/icons/hicolor/48x48/apps/k86-display-studio.png" "${DEB_ROOT}/usr/share/icons/hicolor/48x48/apps/"
    fi

    # Udev rule
    cp "${REPO_DIR}/udev/99-k86.rules" "${DEB_ROOT}/lib/udev/rules.d/99-k86.rules"

    # Systemd service
    cat <<EOF > "${DEB_ROOT}/usr/lib/systemd/user/k86-screen.service"
[Unit]
Description=Attack Shark K86 Screen AI Quota Monitor Daemon
After=default.target

[Service]
Type=simple
ExecStart=/usr/bin/k86-screen-daemon
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

    # Construir .deb
    dpkg-deb --build --root-owner-group "${DEB_ROOT}" "${DIST_DIR}/${PKG_NAME}_${VERSION}_all.deb"
    echo "✅ Gerado: ${DIST_DIR}/${PKG_NAME}_${VERSION}_all.deb"
fi

rm -rf "${BUILD_DIR}"
echo "🎉 Build de release v${VERSION} finalizado com sucesso em ${DIST_DIR}/!"
