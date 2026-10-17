#!/bin/zsh
# Haftalık ilan yenileme (Mac). launchd ile her pazar 03:00'te çalışır: tools/haftalik_kur.sh
# 1) depoyu günceller  2) her şehrin ilanlarını yeniden tarar  3) haritanın ilan dosyalarını üretir  4) GitHub'a gönderir
set -u
cd "$(dirname "$0")/.." || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
LOG="log/haftalik-$(date +%Y%m%d).log"; mkdir -p log
exec >>"$LOG" 2>&1
echo "== $(date) başladı"
git pull -q --rebase origin cok-sehir || echo "git pull başarısız, yerel kopya ile devam"
SEHIRLER=(${=HAFTALIK_SEHIRLER:-istanbul izmir aydin mugla gaziantep hatay})
for s in $SEHIRLER; do
  [ -f "sehirler/$s/config.json" ] || continue
  [ -d "sehirler/$s/_tarama" ] && mv "sehirler/$s/_tarama" "sehirler/$s/_tarama_$(date +%Y%m%d)"
  echo "-- $s taranıyor"
  caffeinate -i python3 tools/tara_sehir.py "$s" --detay "${HAFTALIK_DETAY:-400}" && python3 tools/ilan_hazirla.py "$s"
done
git add sehirler/*/ilan.json sehirler/*/config.json sehirler/index.json
git commit -q -m "Haftalık ilan yenileme $(date +%Y-%m-%d)" && git push -q origin cok-sehir && echo "gönderildi" || echo "gönderilecek değişiklik yok veya push başarısız"
# eski tarama klasörlerinden yalnızca son 4 haftayı tut
for s in $SEHIRLER; do ls -d sehirler/$s/_tarama_* 2>/dev/null | sort | head -n -4 | while read d; do mkdir -p _arsiv && mv "$d" _arsiv/; done; done
echo "== $(date) bitti"
