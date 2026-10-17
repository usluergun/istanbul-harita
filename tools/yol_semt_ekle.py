#!/usr/bin/env python3
"""Mevcut geo.json'daki ilçe ve mahalle sınırlarına dokunmadan OpenStreetMap'ten semt adlarını ve ana yolları ekler.
Sınırları açık veriden gelen şehirlerde (İzmir, Aydın, Muğla, Gaziantep) haritanın Yollar ve Semtler katmanlarını
İstanbul'daki gibi doldurmak için kullanılır. İnternet erişimi olan bilgisayarda çalışır (ör. Mac).

    python3 tools/yol_semt_ekle.py izmir
    python3 tools/yol_semt_ekle.py izmir aydin mugla gaziantep
"""
import json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sinir_indir import overpass, dp, r5, nfc, icinde, YOL, TOL  # noqa: E402


def ekle(sehir):
    kok = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sehirler', sehir)
    cfg = json.load(open(os.path.join(kok, 'config.json'), encoding='utf-8'))
    yol = os.path.join(kok, 'geo.json'); geo = json.load(open(yol, encoding='utf-8'))
    ilce_mp = {f['properties']['n']: f['geometry']['coordinates'] for f in geo['ilce']['features']}
    semt, roads, gor = [], [[], [], [], []], set()
    for c in cfg['ilceler']:
        ad, il = c['ad'], c.get('il', cfg['ad'])
        print(f'{il} / {ad}: semt ve yollar…', flush=True)
        alan_q = (f'area["name"="{il}"]["admin_level"="4"]["boundary"="administrative"]->.il;\n'
                  f'rel(area.il)["boundary"="administrative"]["admin_level"="6"]["name"="{ad}"]->.r;\n.r map_to_area->.a;\n')
        d = overpass(f'[out:json][timeout:300];\n{alan_q}node(area.a)["place"~"^(suburb|quarter)$"]["name"];\nout;')
        mp = ilce_mp.get(ad)
        for e in d['elements']:
            k = (nfc(e['tags']['name']), round(e['lat'], 4), round(e['lon'], 4))
            if k in gor: continue
            if mp and not any(icinde((e['lon'], e['lat']), p[0]) for p in mp): continue
            gor.add(k); semt.append([k[0], round(e['lat'], 5), round(e['lon'], 5)])
        y = overpass(f'[out:json][timeout:300];\n{alan_q}way(area.a)["highway"~"^(motorway|motorway_link|trunk|trunk_link|primary|secondary)$"];\nout geom;')
        for w in y['elements']:
            cc = YOL.get(w.get('tags', {}).get('highway'))
            if cc is None or not w.get('geometry'): continue
            pts = [(g['lon'], g['lat']) for g in w['geometry']]
            if len(pts) > 4: pts = dp(pts, TOL * 1.5)
            roads[cc].append([v for p in pts for v in r5(p)])
        time.sleep(4)
    if not semt and not any(roads): raise SystemExit(f'{sehir}: OSM boş döndü, dosya değiştirilmedi.')
    geo['labels']['semt'] = semt; geo['roads'] = roads
    json.dump(geo, open(yol, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'{sehir}: {len(semt)} semt, {sum(map(len, roads))} yol parçası eklendi · {os.path.getsize(yol) / 1e6:.1f} MB', flush=True)


if __name__ == '__main__':
    if len(sys.argv) < 2: raise SystemExit(__doc__)
    for s in sys.argv[1:]: ekle(s)
