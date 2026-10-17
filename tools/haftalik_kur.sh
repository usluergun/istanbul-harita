#!/bin/zsh
# Haftalık taramayı Mac'te launchd ile kurar (her pazar 03:00). Kaldırmak için: tools/haftalik_kur.sh kaldir
DIR="$(cd "$(dirname "$0")/.." && pwd)"; PL="$HOME/Library/LaunchAgents/com.brossglobal.haftalik-tarama.plist"
if [ "${1:-}" = "kaldir" ]; then launchctl unload "$PL" 2>/dev/null; rm -f "$PL"; echo "kaldırıldı"; exit 0; fi
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PL" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.brossglobal.haftalik-tarama</string>
  <key>ProgramArguments</key><array><string>/bin/zsh</string><string>$DIR/tools/haftalik.sh</string></array>
  <key>StartCalendarInterval</key><dict><key>Weekday</key><integer>0</integer><key>Hour</key><integer>3</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>$DIR/log/launchd.log</string>
  <key>StandardErrorPath</key><string>$DIR/log/launchd.log</string>
</dict></plist>
PLIST
launchctl unload "$PL" 2>/dev/null; launchctl load "$PL" && echo "kuruldu: her pazar 03:00 · $PL"
