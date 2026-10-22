#!/bin/sh
# Baut die Doppelklick-App "Sherlock Demo.app" im Projektordner (nur macOS):
# AppleScript kompilieren, eigenes Symbol einsetzen, ad hoc signieren.
# Aufruf aus dem Projektordner: sh scripts/build_demo_app.sh
set -e
cd "$(dirname "$0")/.."
APP="Sherlock Demo.app"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

rm -rf "$APP"
osacompile -o "$APP" scripts/sherlock_demo.applescript
.venv/bin/python scripts/make_demo_icon.py "$TMP/Sherlock.iconset"
iconutil -c icns "$TMP/Sherlock.iconset" -o "$APP/Contents/Resources/applet.icns"
# Symbol aus applet.icns statt aus dem Standard-Asset-Katalog
rm -f "$APP/Contents/Resources/Assets.car"
plutil -remove CFBundleIconName "$APP/Contents/Info.plist" 2>/dev/null || true
# Erweiterte Attribute (Finder-Infos) verhindern sonst das Signieren
xattr -cr "$APP"
codesign --force --sign - "$APP"
codesign --verify "$APP"
touch "$APP"
echo "gebaut: $APP"
