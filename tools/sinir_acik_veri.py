#!/usr/bin/env python3
"""İlçe ve mahalle sınırlarını açık veri setinden (github.com/ttezer/turkiye-harita-verisi) alıp
sehirler/<şehir>/geo.json dosyasını haritanın beklediği biçimde yazar. OpenStreetMap'e erişim gerekmez.

Kaynaklar (veri seti içinde belirtildiği gibi):
  ilçe sınırları   HDX COD-AB-TUR (OCHA), CC BY-IGO
  mahalle sınırları il bazında açık veri (ör. Gaziantep Açık Veri Platformu) ve veri setine eklenen KML dosyaları

Kullanım:
    git clone --depth 1 https://github.com/ttezer/turkiye-harita-verisi.git ../kaynak/turkiye-harita-verisi
    python3 tools/sinir_acik_veri.py izmir ../kaynak/turkiye-harita-verisi

Semt adları ve ana yollar bu veri setinde yok; o katmanlar boş kalır (altlık haritada yollar yine görünür).
tools/sinir_indir.py (OpenStreetMap) çalıştırılırsa onları da ekler.
"""
import json, os, sys, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sinir_indir import dp, r5, etiket_noktasi, kisa  # noqa: E402

PLAKA = {'İstanbul': '34', 'İzmir': '35', 'Aydın': '09', 'Gaziantep': '27', 'Ankara': '06', 'Antalya': '07', 'Muğla': '48', 'Bursa': '16'}


def nfc(s): return unicodedata.normalize('NFC', s or '')


def mp(geom):
    c = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    out = []
    for poly in c:
        rings = []
        for h in poly:
            h = [tuple(p[:2]) for p in h]
            if h[0] != h[-1]: h.append(h[0])
            s = dp(h)
            if len(s) >= 4: rings.append([r5(p) for p in s])
        if rings: out.append(rings)
    return out


def main():
    if len(sys.argv) < 3: raise SystemExit(__doc__)
    sehir, kaynak = sys.argv[1], sys.argv[2]
    kok = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sehirler', sehir)
    cfg = json.load(open(os.path.join(kok, 'config.json'), encoding='utf-8'))
    plaka = PLAKA[cfg['ad']]
    D = json.load(open(os.path.join(kaynak, 'dist', 'json', 'districts.json'), encoding='utf-8'))
    DG = {f['properties']['id']: f for f in json.load(open(os.path.join(kaynak, 'dist', 'geojson', 'districts.geojson'), encoding='utf-8'))['features']}
    geo = {'mah': {'type': 'FeatureCollection', 'features': []}, 'ilce': {'type': 'FeatureCollection', 'features': []},
           'labels': {'ilce': [], 'mah': [], 'semt': []}, 'roads': [[], [], [], []],
           'kaynak': 'İlçe: HDX COD-AB-TUR (OCHA, CC BY-IGO). Mahalle: il açık veri ve KML derlemesi, github.com/ttezer/turkiye-harita-verisi'}
    for c in cfg['ilceler']:
        ad = c['ad']
        d = next((x for x in D if x['plate_code'] == plaka and nfc(x['name']) == ad), None)
        if not d: print(f'! {ad} veri setinde bulunamadı', file=sys.stderr); continue
        g = mp(DG[d['id']]['geometry'])
        geo['ilce']['features'].append({'type': 'Feature', 'properties': {'n': ad}, 'geometry': {'type': 'MultiPolygon', 'coordinates': g}})
        geo['labels']['ilce'].append([ad, *etiket_noktasi(g)])
        f = os.path.join(kaynak, 'dist', 'geojson', 'mahalle-geometrileri-by-district', d['id'] + '.geojson')
        if not os.path.exists(f): print(f'! {ad}: mahalle sınırı yok', file=sys.stderr); continue
        n = 0
        for m in json.load(open(f, encoding='utf-8'))['features']:
            ad8 = nfc(m['properties']['name']).strip()
            if not ad8: continue
            full = ad8 if ('Mahalle' in ad8 or 'Köyü' in ad8) else ad8 + ' Mahallesi'
            k = mp(m['geometry'])
            if not k: continue
            geo['mah']['features'].append({'type': 'Feature', 'properties': {'n': full, 'i': ad}, 'geometry': {'type': 'MultiPolygon', 'coordinates': k}})
            geo['labels']['mah'].append([kisa(full), *etiket_noktasi(k)]); n += 1
        print(f'{ad}: {n} mahalle')
    yol = os.path.join(kok, 'geo.json')
    json.dump(geo, open(yol, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'Yazıldı: {yol} · {len(geo["ilce"]["features"])} ilçe, {len(geo["mah"]["features"])} mahalle, {os.path.getsize(yol) / 1e6:.2f} MB')


if __name__ == '__main__':
    main()
