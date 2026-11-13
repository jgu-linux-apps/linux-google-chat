#!/bin/bash
# Buduje pakiet .deb: dist/linux-google-chat_<wersja>_all.deb
set -euo pipefail
cd "$(dirname "$0")/.."
PKG=linux-google-chat
APP_ID=io.github.jaro.LinuxGoogleChat
VERSION=$(sed -n 's/^VERSION = "\(.*\)"/\1/p' src/lgc/__init__.py)
ROOT=$(mktemp -d)
trap 'rm -rf "$ROOT"' EXIT

install -d "$ROOT/DEBIAN" "$ROOT/usr/bin" "$ROOT/usr/share/$PKG" "$ROOT/usr/share/applications" \
  "$ROOT/usr/share/icons/hicolor/scalable/apps" "$ROOT/etc/xdg/autostart" "$ROOT/usr/share/doc/$PKG"

cp -r src data "$ROOT/usr/share/$PKG/"
find "$ROOT/usr/share/$PKG" -name __pycache__ -prune -exec rm -rf {} +
rm -rf "$ROOT/usr/share/$PKG/data/applications" "$ROOT/usr/share/$PKG/data/autostart" "$ROOT/usr/share/$PKG/data/icons/hicolor"
install -m 755 bin/$PKG "$ROOT/usr/bin/$PKG"
install -m 644 data/applications/$APP_ID.desktop "$ROOT/usr/share/applications/"
install -m 644 data/autostart/$PKG-iconsync.desktop "$ROOT/etc/xdg/autostart/"
install -m 644 data/icons/hicolor/scalable/apps/$APP_ID.svg "$ROOT/usr/share/icons/hicolor/scalable/apps/"
install -m 644 README.md "$ROOT/usr/share/doc/$PKG/"
install -m 644 LICENSE "$ROOT/usr/share/doc/$PKG/copyright"

SIZE=$(du -sk "$ROOT/usr" "$ROOT/etc" | awk '{s+=$1} END {print s}')
cat > "$ROOT/DEBIAN/control" <<CTL
Package: $PKG
Version: $VERSION
Section: net
Priority: optional
Architecture: all
Installed-Size: $SIZE
Maintainer: Jaro <jaroslawguza83@gmail.com>
Homepage: https://github.com/jgu-linux-apps/linux-google-chat
Depends: python3 (>= 3.10), python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1 (>= 1.5), gir1.2-webkit-6.0, librsvg2-common
Recommends: hunspell-pl, hunspell-en-us, gnome-shell-extension-appindicator
Description: Linux Google Chat – desktop app for Google Chat (unofficial)
 Google Chat in its own window on Ubuntu (GTK4/libadwaita + WebKitGTK):
 stays signed in, tray icon with unread count, counter on the dock icon,
 GNOME notifications that open the conversation, Do Not Disturb, downloads
 to your Downloads folder, spell checking, zoom, themes (System, Aurora,
 Studio Pro), PL / EN, app icon that follows the light/dark system theme.
 Not affiliated with Google.
CTL

cat > "$ROOT/DEBIAN/postinst" <<'SH'
#!/bin/sh
set -e
if [ "$1" = "configure" ]; then
  command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -q -f /usr/share/icons/hicolor || true
  command -v update-desktop-database >/dev/null && update-desktop-database -q /usr/share/applications || true
fi
exit 0
SH
cat > "$ROOT/DEBIAN/postrm" <<'SH'
#!/bin/sh
set -e
command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -q -f /usr/share/icons/hicolor || true
command -v update-desktop-database >/dev/null && update-desktop-database -q /usr/share/applications || true
exit 0
SH
chmod 755 "$ROOT/DEBIAN/postinst" "$ROOT/DEBIAN/postrm"
echo "/etc/xdg/autostart/$PKG-iconsync.desktop" > "$ROOT/DEBIAN/conffiles"

mkdir -p dist
dpkg-deb --root-owner-group --build "$ROOT" "dist/${PKG}_${VERSION}_all.deb" >/dev/null
echo "dist/${PKG}_${VERSION}_all.deb"
