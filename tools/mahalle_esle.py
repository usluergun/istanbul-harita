#!/usr/bin/env python3
"""İlanlara mahalle numarası (mk) verir: ilanın konumu hangi mahalle sınırının içindeyse o mahalle.
Konum hiçbir sınırın içinde değilse, aynı ilçede ilanın yazdığı mahalle adıyla eşleştirir; o da yoksa mk = -1.

Kullanım:
    python3 tools/mahalle_esle.py izmir            # sehirler/izmir/ilan.json içindeki mk alanlarını yeniler
    python3 tools/mahalle_esle.py izmir --kontrol  # yalnızca rapor, dosyaya yazmaz
"""
import json, os, sys, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sinir_indir import icinde  # noqa: E402


def nfc(s): return unicodedata.normalize('NFC', s or '')


def anahtar(s): return nfc(s).replace(' Mahallesi', '').replace(' Mah.', '').strip().casefold()


def esle(I, G):
    """İlan listesine yerinde mk yazar; özet sayıları döndürür."""
    F = G['mah']['features']
    kutu = []
    for f in F:
        xs = [p[0] for poly in f['geometry']['coordinates'] for p in poly[0]]; ys = [p[1] for poly in f['geometry']['coordinates'] for p in poly[0]]
        kutu.append((min(xs), min(ys), max(xs), max(ys)))
    adla = {(nfc(f['properties']['i']), anahtar(f['properties']['n'])): k for k, f in enumerate(F)}
    say = {'konum': 0, 'ad': 0, 'yok': 0, 'degisen': 0}
    for x in I:
        x['b'] = nfc(x['b']); eski = x.get('mk'); mk = -1
        for k, f in enumerate(F):
            a, b, c, d = kutu[k]
            if not (a <= x['lng'] <= c and b <= x['lat'] <= d): continue
            if any(icinde((x['lng'], x['lat']), poly[0]) and not any(icinde((x['lng'], x['lat']), h) for h in poly[1:]) for poly in f['geometry']['coordinates']):
                mk = k; break
        if mk >= 0: say['konum'] += 1
        else:
            mk = adla.get((x['b'], anahtar(x.get('mh'))), -1)
            say['ad' if mk >= 0 else 'yok'] += 1
        if eski is not None and eski != mk: say['degisen'] += 1
        x['mk'] = mk
    return say


def main():
    sehir = sys.argv[1]; kontrol = '--kontrol' in sys.argv
    kok = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sehirler', sehir)
    I = json.load(open(os.path.join(kok, 'ilan.json'), encoding='utf-8'))
    G = json.load(open(os.path.join(kok, 'geo.json'), encoding='utf-8'))
    say = esle(I, G)
    print(f'{len(I)} ilan · konumdan {say["konum"]} · mahalle adından {say["ad"]} · eşleşmeyen {say["yok"]} · önceki değerden farklı {say["degisen"]}')
    if not kontrol:
        json.dump(I, open(os.path.join(kok, 'ilan.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        print('ilan.json güncellendi')


if __name__ == '__main__':
    main()
