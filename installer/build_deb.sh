#!/bin/bash
#
# FlowAudit DEB Package Builder
# Erstellt ein .deb Paket für Ubuntu/Debian Installation
#

set -e

# Konfiguration
PACKAGE_NAME="flowaudit-installer"
VERSION="3.0.0"
MAINTAINER="FlowAudit Team <support@flowaudit.de>"
DESCRIPTION="FlowAudit Universal GUI Installer - KI-gestützte Rechnungsprüfung"
ARCHITECTURE="all"  # Python ist plattformunabhängig

# Verzeichnisse
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
PACKAGE_DIR="${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}"

echo "================================================"
echo "  FlowAudit DEB Package Builder"
echo "  Version: ${VERSION}"
echo "================================================"
echo ""

# Aufräumen
echo "[1/6] Räume alte Build-Artefakte auf..."
rm -rf "${BUILD_DIR}"
mkdir -p "${PACKAGE_DIR}"

# Verzeichnisstruktur erstellen
echo "[2/6] Erstelle Verzeichnisstruktur..."
mkdir -p "${PACKAGE_DIR}/DEBIAN"
mkdir -p "${PACKAGE_DIR}/usr/share/flowaudit"
mkdir -p "${PACKAGE_DIR}/usr/share/applications"
mkdir -p "${PACKAGE_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${PACKAGE_DIR}/usr/bin"
mkdir -p "${PACKAGE_DIR}/usr/share/doc/flowaudit-installer"

# DEBIAN/control erstellen
echo "[3/6] Erstelle Control-Datei..."
cat > "${PACKAGE_DIR}/DEBIAN/control" << EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCHITECTURE}
Depends: python3 (>= 3.10), python3-tk, git, curl
Recommends: python3-pil, docker-ce | docker.io
Suggests: nvidia-container-toolkit
Maintainer: ${MAINTAINER}
Homepage: https://github.com/janpow77/flowinvoice
Description: ${DESCRIPTION}
 FlowAudit ist ein KI-gestütztes System zur automatischen
 Prüfung von Rechnungen auf Förderfähigkeit.
 .
 Dieses Paket enthält den GUI-Installer, der:
  - Docker und Docker Compose einrichtet
  - Das FlowAudit Repository klont
  - Alle Services konfiguriert und startet
  - Einen Admin-Benutzer erstellt
  - Optional lokale KI-Modelle herunterlädt
 .
 Optimiert für ASUS NUC 15 mit NVIDIA RTX GPU.
EOF

# Post-Install Script
echo "[4/6] Erstelle Install-Scripts..."
cat > "${PACKAGE_DIR}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

echo ""
echo "=============================================="
echo "  FlowAudit Installer erfolgreich installiert!"
echo "=============================================="
echo ""
echo "Starte den Installer mit:"
echo "  flowaudit-installer"
echo ""
echo "Oder über das Anwendungsmenü:"
echo "  Anwendungen → Büro → FlowAudit Installer"
echo ""

# Desktop-Datenbank aktualisieren (falls vorhanden)
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database -q /usr/share/applications 2>/dev/null || true
fi

# Icon-Cache aktualisieren (falls vorhanden)
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor 2>/dev/null || true
fi

exit 0
EOF
chmod 755 "${PACKAGE_DIR}/DEBIAN/postinst"

# Pre-Remove Script
cat > "${PACKAGE_DIR}/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e
# Nichts zu tun - Container bleiben bestehen
exit 0
EOF
chmod 755 "${PACKAGE_DIR}/DEBIAN/prerm"

# Installer-Datei kopieren
echo "[5/6] Kopiere Dateien..."
cp "${SCRIPT_DIR}/flowaudit_installer.py" "${PACKAGE_DIR}/usr/share/flowaudit/"

# Dokumentation kopieren
cp "${SCRIPT_DIR}/README.md" "${PACKAGE_DIR}/usr/share/doc/flowaudit-installer/"
cp "${SCRIPT_DIR}/NUC_SETUP_GUIDE.md" "${PACKAGE_DIR}/usr/share/doc/flowaudit-installer/" 2>/dev/null || true

# Launcher-Script erstellen
cat > "${PACKAGE_DIR}/usr/bin/flowaudit-installer" << 'EOF'
#!/bin/bash
# FlowAudit Installer Launcher
exec python3 /usr/share/flowaudit/flowaudit_installer.py "$@"
EOF
chmod 755 "${PACKAGE_DIR}/usr/bin/flowaudit-installer"

# Desktop-Entry erstellen
cat > "${PACKAGE_DIR}/usr/share/applications/flowaudit-installer.desktop" << EOF
[Desktop Entry]
Name=FlowAudit Installer
Comment=KI-gestützte Rechnungsprüfung installieren
Exec=flowaudit-installer
Icon=flowaudit
Terminal=false
Type=Application
Categories=Office;Utility;
Keywords=invoice;audit;docker;ai;
StartupNotify=true
EOF

# Icon erstellen (einfaches SVG)
cat > "${PACKAGE_DIR}/usr/share/icons/hicolor/256x256/apps/flowaudit.svg" << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <defs>
    <linearGradient id="fishGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#3b82f6"/>
      <stop offset="50%" style="stop-color:#06b6d4"/>
      <stop offset="100%" style="stop-color:#10b981"/>
    </linearGradient>
  </defs>
  <circle cx="128" cy="128" r="120" fill="#f0f9ff" stroke="#3b82f6" stroke-width="4"/>
  <path d="M60 128 Q90 80 140 90 Q180 95 200 128 Q180 161 140 166 Q90 176 60 128 Z"
        fill="url(#fishGrad)" opacity="0.9"/>
  <circle cx="170" cy="120" r="12" fill="#1e3a5f"/>
  <circle cx="173" cy="117" r="4" fill="white"/>
  <path d="M45 128 L20 100 L20 156 Z" fill="url(#fishGrad)" opacity="0.8"/>
</svg>
EOF

# Copyright-Datei
cat > "${PACKAGE_DIR}/usr/share/doc/flowaudit-installer/copyright" << EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: flowaudit-installer
Source: https://github.com/janpow77/flowinvoice

Files: *
Copyright: 2024-2025 FlowAudit Team
License: MIT
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:
 .
 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.
 .
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.
EOF

# Changelog erstellen
cat > "${PACKAGE_DIR}/usr/share/doc/flowaudit-installer/changelog.Debian" << EOF
flowaudit-installer (${VERSION}) stable; urgency=medium

  * Initial release
  * GUI-Installer mit Thread-sicherem Logging
  * Docker Compose Abstraktion
  * NVIDIA GPU Unterstützung
  * Cloudflare Tunnel Integration
  * Ollama Model Pull

 -- FlowAudit Team <support@flowaudit.de>  $(date -R)
EOF
gzip -9 "${PACKAGE_DIR}/usr/share/doc/flowaudit-installer/changelog.Debian"

# DEB-Paket bauen
echo "[6/6] Baue DEB-Paket..."
dpkg-deb --build --root-owner-group "${PACKAGE_DIR}"

# Aufräumen und Ergebnis zeigen
mv "${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}.deb" "${SCRIPT_DIR}/"
rm -rf "${BUILD_DIR}"

DEB_FILE="${SCRIPT_DIR}/${PACKAGE_NAME}_${VERSION}.deb"
DEB_SIZE=$(du -h "${DEB_FILE}" | cut -f1)

echo ""
echo "================================================"
echo "  DEB-Paket erfolgreich erstellt!"
echo "================================================"
echo ""
echo "  Datei: ${PACKAGE_NAME}_${VERSION}.deb"
echo "  Größe: ${DEB_SIZE}"
echo ""
echo "Installation:"
echo "  sudo dpkg -i ${PACKAGE_NAME}_${VERSION}.deb"
echo "  sudo apt-get install -f  # Falls Abhängigkeiten fehlen"
echo ""
echo "Oder mit apt:"
echo "  sudo apt install ./${PACKAGE_NAME}_${VERSION}.deb"
echo ""
echo "Deinstallation:"
echo "  sudo apt remove ${PACKAGE_NAME}"
echo ""
