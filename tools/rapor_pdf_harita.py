#!/usr/bin/env python3
"""Haritadaki Müteahhit pazar raporunu her şehir ve ilçe için A4 PDF olarak kaydeder.
Raporun kendisi haritanın içinde üretilir; bu araç onu tarayıcıda açıp yazdırma görünümüyle PDF'e çevirir,
böylece PDF ile ekrandaki rapor her zaman aynıdır.

    python3 tools/rapor_pdf_harita.py izmir                 # şehrin tüm ilçeleri
    python3 tools/rapor_pdf_harita.py istanbul Avcılar Esenyurt
    python3 tools/rapor_pdf_harita.py hepsi                 # ilanı olan bütün şehirler

Çıktı: pdf/<şehir>/muteahhit-raporu-<ilçe>.pdf   (Playwright + Chromium gerekir)
"""
import json, os, sys, threading, http.server, functools, unicodedata, re
from playwright.sync_api import sync_playwright

KOK = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
TR = str.maketrans('çğıöşüâîûÇĞİÖŞÜ', 'cgiosuaiuCGIOSU')
slug = lambda s: re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFC', s).translate(TR).lower()).strip('-')


def sunucu():
    class Sessiz(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    h = functools.partial(Sessiz, directory=KOK)
    s = http.server.ThreadingHTTPServer(('127.0.0.1', 0), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def main():
    if len(sys.argv) < 2: raise SystemExit(__doc__)
    idx = json.load(open(os.path.join(KOK, 'sehirler', 'index.json'), encoding='utf-8'))
    sehirler = [c['id'] for c in idx['sehirler'] if c['durum'] == 'hazir'] if sys.argv[1] == 'hepsi' else [sys.argv[1]]
    secili = [unicodedata.normalize('NFC', a) for a in sys.argv[2:]]
    srv = sunucu(); port = srv.server_address[1]
    with sync_playwright() as p:
        b = p.chromium.launch()
        for sh in sehirler:
            if not os.path.exists(os.path.join(KOK, 'sehirler', sh, 'ilan.json')):
                print(sh, ': ilan verisi yok, atlandı'); continue
            pg = b.new_page(viewport={'width': 1200, 'height': 900})
            pg.route('**/arcgisonline.com/**', lambda r: r.abort())  # harita karoları PDF'e girmez
            hata = []; pg.on('pageerror', lambda e: hata.append(str(e)))
            pg.goto(f'http://127.0.0.1:{port}/index.html?sehir={sh}')
            try:
                pg.wait_for_function('!!window.__mutRap', timeout=30000, polling=500)
            except Exception:
                print(sh, ': rapor yüklenemedi', hata); pg.close(); continue
            pg.wait_for_timeout(1500)
            ilceler = secili or pg.evaluate("[...document.querySelectorAll('#bolgeler .bolge')].map(b => b.dataset.b).filter(b => b !== 'Tümü')")
            os.makedirs(os.path.join(KOK, 'pdf', sh), exist_ok=True)
            for il in ilceler:
                pg.evaluate('il => window.__mutRap(il)', il); pg.wait_for_timeout(400)
                yol = os.path.join(KOK, 'pdf', sh, f'muteahhit-raporu-{slug(il)}.pdf')
                pg.emulate_media(media='print')
                pg.pdf(path=yol, format='A4', print_background=True, margin={'top': '10mm', 'bottom': '10mm', 'left': '10mm', 'right': '10mm'})
                pg.emulate_media(media='screen')
                print('yazıldı', os.path.relpath(yol, KOK))
            pg.close()
        b.close()
    srv.shutdown()


if __name__ == '__main__':
    main()
