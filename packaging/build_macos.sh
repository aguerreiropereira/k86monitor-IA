#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-1.0.0}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${REPO_DIR}/dist"
ARCH="$(uname -m)"

cd "${REPO_DIR}"
python3 -m PyInstaller packaging/k86-display-studio.spec --noconfirm --clean

DMG_PATH="${DIST_DIR}/K86DisplayStudio-${VERSION}-macOS-${ARCH}.dmg"
STAGING_DIR="$(mktemp -d)"
rm -f "${DMG_PATH}"
trap 'rm -rf "${STAGING_DIR}"' EXIT
cp -R "${DIST_DIR}/K86 Display Studio.app" "${STAGING_DIR}/"
ln -s /Applications "${STAGING_DIR}/Applications"
hdiutil create \
  -volname "K86 Display Studio" \
  -srcfolder "${STAGING_DIR}" \
  -ov \
  -format UDZO \
  "${DMG_PATH}"
echo "Created ${DMG_PATH}"
