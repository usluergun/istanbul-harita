#!/usr/bin/env python3
"""Bir şehrin ilçe ve mahalle sınırlarını, semt adlarını ve ana yollarını OpenStreetMap'ten (Overpass) indirip
sehirler/<şehir>/geo.json dosyasını haritanın beklediği biçimde yazar.

Kullanım (internet erişimi olan bir bilgisayarda, ör. Mac):
    python3 tools/sinir_indir.py izmir
    python3 tools/sinir_indir.py gaziantep --yollar-yok     # yolları atla (daha hızlı)

Yalnızca Python 3 standart kütüphanesi kullanılır. İlçe listesi sehirler/<şehir>/config.json dosyasından okunur.
Aydın gibi il adı config'teki 'ad' alanından gelir (il sınırı admin_level=4).

Çıktı biçimi (sehirler/istanbul/geo.json ile aynı):
  mah:   GeoJSON FeatureCollection, properties {n: 'X Mahallesi', i: 'İlçe'}, MultiPolygon
  ilce:  GeoJSON FeatureCollection, properties {n: 'İlçe'}, MultiPolygon
  labels: {ilce: [[ad, lat, lng]], mah: [[kısa ad, lat, lng]], semt: [[ad, lat, lng]]}
  roads: [otoyol, ana yol, birincil, ikincil] → her biri [[lng, lat, lng, lat, ...], ...]
"""
import json, os, sys, time, urllib.request, urllib.parse, unicodedata

UC = ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter',
      'https://maps.mail.ru/osm/tools/overpass/api/interpreter']
YOL = {'motorway': 0, 'motorway_link': 0, 'trunk': 1, 'trunk_link': 1, 'primary': 2, 'secondary': 3}
TOL = 0.00004   # sadeleştirme toleransı (derece, ~4 m)


def nfc(s): return unicodedata.normalize('NFC', s or '')


def overpass(q, deneme=3):
    veri = urllib.parse.urlencode({'data': q}).encode()
    son = None
    for i in range(deneme):
        for u in UC:
            try:
                r = urllib.request.Request(u, data=veri, headers={'User-Agent': 'mahalle-fiyat-haritasi/1.0'})
                with urllib.request.urlopen(r, timeout=360) as f:
                    return json.loads(f.read().decode('utf-8'))
            except Exception as e:  # sunucu meşgulse diğerini dene
                son = e; print(f'  · {u.split("/")[2]} yanıt vermedi ({e}); başka sunucu deneniyor', file=sys.stderr)
        time.sleep(20 * (i + 1))
    raise SystemExit(f'Overpass erişilemedi: {son}')


# --- geometri yardımcıları -------------------------------------------------------------
def halkalar(parcalar):
    """Uçları birbirine değen yol parçalarını kapalı halkalara birleştirir. parcalar: [[(lng,lat),...], ...]"""
    kalan = [list(p) for p in parcalar if len(p) >= 2]
    out = []
    while kalan:
        h = kalan.pop(0)
        degisti = True
        while h[0] != h[-1] and degisti:
            degisti = False
            for i, p in enumerate(kalan):
                if p[0] == h[-1]: h += p[1:]
                elif p[-1] == h[-1]: h += p[::-1][1:]
                elif p[-1] == h[0]: h = p + h[1:]
                elif p[0] == h[0]: h = p[::-1] + h[1:]
                else: continue
                kalan.pop(i); degisti = True; break
        if h[0] == h[-1] and len(h) >= 4: out.append(h)
    return out


def icinde(pt, halka):
    x, y = pt; ic = False
    for i in range(len(halka) - 1):
        (x1, y1), (x2, y2) = halka[i], halka[i + 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: ic = not ic
    return ic


def alan(h): return sum(h[i][0] * h[i + 1][1] - h[i + 1][0] * h[i][1] for i in range(len(h) - 1)) / 2


def dp(pts, tol=TOL):
    """Douglas-Peucker sadeleştirme (yinelemeli)."""
    if len(pts) < 5: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True
    st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop(); (x1, y1), (x2, y2) = pts[a], pts[b]; dx, dy = x2 - x1, y2 - y1; L = (dx * dx + dy * dy) or 1e-18
        mi, md = -1, 0
        for i in range(a + 1, b):
            x, y = pts[i]; t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / L))
            d = (x - x1 - t * dx) ** 2 + (y - y1 - t * dy) ** 2
            if d > md: mi, md = i, d
        if mi > 0 and md > tol * tol: keep[mi] = True; st += [(a, mi), (mi, b)]
    out = [p for p, k in zip(pts, keep) if k]
    return out if len(out) >= 4 else pts


def r5(p): return [round(p[0], 5), round(p[1], 5)]


def multipoligon(rel):
    dis = [[(n['lon'], n['lat']) for n in m['geometry']] for m in rel.get('members', []) if m.get('type') == 'way' and m.get('role') in ('outer', '') and m.get('geometry')]
    ic = [[(n['lon'], n['lat']) for n in m['geometry']] for m in rel.get('members', []) if m.get('type') == 'way' and m.get('role') == 'inner' and m.get('geometry')]
    D, I = halkalar(dis), halkalar(ic)
    if not D: return None
    pol = [[h] for h in sorted(D, key=lambda h: -abs(alan(h)))]
    for h in I:
        for p in pol:
            if icinde(h[0], p[0]): p.append(h); break
    return [[[r5(q) for q in dp(h)] for h in p] for p in pol]


def etiket_noktasi(mp):
    """En büyük parçanın içinde kalan bir nokta: ağırlık merkezi içerdeyse o, değilse o enlemdeki en geniş iç aralığın ortası."""
    dis = max((p[0] for p in mp), key=lambda h: abs(alan(h)))
    A = alan(dis) or 1e-12
    cx = sum((dis[i][0] + dis[i + 1][0]) * (dis[i][0] * dis[i + 1][1] - dis[i + 1][0] * dis[i][1]) for i in range(len(dis) - 1)) / (6 * A)
    cy = sum((dis[i][1] + dis[i + 1][1]) * (dis[i][0] * dis[i + 1][1] - dis[i + 1][0] * dis[i][1]) for i in range(len(dis) - 1)) / (6 * A)
    if icinde((cx, cy), dis): return round(cy, 5), round(cx, 5)
    xs = sorted((x1 + (cy - y1) * (x2 - x1) / (y2 - y1)) for (x1, y1), (x2, y2) in zip(dis, dis[1:]) if (y1 > cy) != (y2 > cy))
    if len(xs) >= 2:
        a, b = max(zip(xs[::2], xs[1::2]), key=lambda t: t[1] - t[0]); return round(cy, 5), round((a + b) / 2, 5)
    return round(dis[0][1], 5), round(dis[0][0], 5)


def kisa(n): return nfc(n).replace(' Mahallesi', '').replace(' Mah.', '').strip()


# --- ana iş --------------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2: raise SystemExit(__doc__)
    sehir = sys.argv[1]; yollar = '--yollar-yok' not in sys.argv
    kok = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sehirler', sehir)
    cfg = json.load(open(os.path.join(kok, 'config.json'), encoding='utf-8'))
    il, ilceler = cfg['ad'], [c['ad'] for c in cfg['ilceler']]
    geo = {'mah': {'type': 'FeatureCollection', 'features': []}, 'ilce': {'type': 'FeatureCollection', 'features': []},
           'labels': {'ilce': [], 'mah': [], 'semt': []}, 'roads': [[], [], [], []]}
    for ad in ilceler:
        print(f'{il} / {ad}: indiriliyor…')
        alan_q = f'area["name"="{il}"]["admin_level"="4"]["boundary"="administrative"]->.il;\nrel(area.il)["boundary"="administrative"]["admin_level"="6"]["name"="{ad}"]->.r;\n.r map_to_area->.a;\n'
        d = overpass(f'[out:json][timeout:300];\n{alan_q}(.r; rel(area.a)["boundary"="administrative"]["admin_level"="8"];);\nout geom;\n'
                     f'node(area.a)["place"~"^(suburb|quarter)$"]["name"];\nout;')
        rels = [e for e in d['elements'] if e['type'] == 'relation']
        ir = next((e for e in rels if e['tags'].get('admin_level') == '6'), None)
        if not ir: print(f'  ! {ad} ilçe sınırı bulunamadı (OSM adını kontrol edin)', file=sys.stderr); continue
        mp = multipoligon(ir)
        if mp:
            geo['ilce']['features'].append({'type': 'Feature', 'properties': {'n': ad}, 'geometry': {'type': 'MultiPolygon', 'coordinates': mp}})
            geo['labels']['ilce'].append([ad, *etiket_noktasi(mp)])
        n = 0
        for e in rels:
            if e['tags'].get('admin_level') != '8': continue
            m = multipoligon(e)
            if not m: continue
            ad8 = nfc(e['tags'].get('name', ''))
            if not ad8: continue
            if 'Mahalle' not in ad8 and 'Köyü' not in ad8: ad8 += ' Mahallesi'
            # ilçe dışına taşan komşu mahalleleri ayıkla: etiket noktası ilçe içinde olmalı
            lat, lng = etiket_noktasi(m)
            if mp and not any(icinde((lng, lat), p[0]) for p in mp): continue
            geo['mah']['features'].append({'type': 'Feature', 'properties': {'n': ad8, 'i': ad}, 'geometry': {'type': 'MultiPolygon', 'coordinates': m}})
            geo['labels']['mah'].append([kisa(ad8), lat, lng]); n += 1
        for e in d['elements']:
            if e['type'] == 'node': geo['labels']['semt'].append([nfc(e['tags']['name']), round(e['lat'], 5), round(e['lon'], 5)])
        print(f'  {n} mahalle, {sum(1 for e in d["elements"] if e["type"] == "node")} semt')
        if yollar:
            y = overpass(f'[out:json][timeout:300];\n{alan_q}way(area.a)["highway"~"^(motorway|motorway_link|trunk|trunk_link|primary|secondary)$"];\nout geom;')
            for w in y['elements']:
                c = YOL.get(w.get('tags', {}).get('highway'))
                if c is None or not w.get('geometry'): continue
                pts = dp([(g['lon'], g['lat']) for g in w['geometry']], TOL * 1.5) if len(w['geometry']) > 4 else [(g['lon'], g['lat']) for g in w['geometry']]
                geo['roads'][c].append([v for p in pts for v in r5(p)])
        time.sleep(5)  # sunucuya nazik ol
    if not geo['mah']['features']: raise SystemExit('Hiç mahalle sınırı gelmedi; dosya yazılmadı.')
    yol = os.path.join(kok, 'geo.json')
    json.dump(geo, open(yol, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'Yazıldı: {yol} · {len(geo["ilce"]["features"])} ilçe, {len(geo["mah"]["features"])} mahalle, '
          f'{len(geo["labels"]["semt"])} semt, {sum(map(len, geo["roads"]))} yol parçası, {os.path.getsize(yol) / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
