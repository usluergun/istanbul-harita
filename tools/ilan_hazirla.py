#!/usr/bin/env python3
"""Tarama çıktısını (sehirler/<şehir>/_tarama/*_secili.json) haritanın ilan biçimine çevirir.

    python3 tools/ilan_hazirla.py izmir

- konumu olan ilanlar alınır, aynı dairenin tekrar ilanları birleştirilir (diğer linkler 'alt')
- uç fiyatlar (alt/üst %1) atılır, mahalle numarası (mk) verilir
- sehirler/<şehir>/ilan.json yazılır; config.json'da fiyat adımları ve tarama tarihleri,
  index.json'da şehrin durumu ('hazir') güncellenir
"""
import json, os, re, math, sys, glob, unicodedata, statistics
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mahalle_esle import esle  # noqa: E402

AY = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
ADIM = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3, 3.5, 4, 4.5, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 25, 30, 35, 40, 50, 60, 75, 100, 125, 150, 200, 300]
nfc = lambda s: unicodedata.normalize('NFC', s or '')


def main():
    sehir = sys.argv[1]
    kok = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sehirler', sehir)
    cfg = json.load(open(os.path.join(kok, 'config.json'), encoding='utf-8'))
    geo = json.load(open(os.path.join(kok, 'geo.json'), encoding='utf-8'))
    ad_by_key = {c['emlakjet'].split('-', 1)[1]: c['ad'] for c in cfg['ilceler']}
    out, tarih = [], {}
    for f in sorted(glob.glob(os.path.join(kok, '_tarama', '*_secili.json'))):
        key = os.path.basename(f)[:-len('_secili.json')]
        ad = ad_by_key.get(key)
        if not ad: continue
        seen = {}
        for x in json.load(open(f, encoding='utf-8')):
            if 'lat' not in x or not x.get('fiyat'): continue
            oz, dt = x.get('ozet', {}), x.get('detay', {})
            yas = oz.get('Bina Yaşı', '') or ''
            m = re.match(r'(\d+)', yas); yn = int(m.group(1)) if m else None
            lat, lng = x['lat'], x['lng']; k = (round(lat, 5), round(lng, 5))
            if k in seen: seen[k] += 1; ang = seen[k] * 2.1; lat += 0.00022 * math.sin(ang); lng += 0.00029 * math.cos(ang)
            else: seen[k] = 0
            tt = x['baslik'].replace('İ', 'i').replace('I', 'ı').lower()
            site = dt.get('Site İçerisinde') == 'Evet'; siteB = 0
            if not site and re.search(r'site i[çc]i|site i[çc]erisinde|sitesi|sitesinde|sitede|rezidans|residence', tt): site = True; siteB = 1
            if x.get('tarama'): tarih.setdefault(ad, set()).add(x['tarama'])
            o = {'b': ad, 'id': x['url'].rsplit('-', 1)[-1], 't': x['baslik'], 'u': x['url'], 'p': x['fiyat'],
                 'mh': nfc((x.get('Konum') or '').split(',')[0].strip()), 'oda': oz.get('Oda Sayısı') or x.get('Oda Sayısı'), 'm2': x.get('Metrekare'),
                 'brut': oz.get('Brüt'), 'net': oz.get('Net'), 'kat': oz.get('Bulunduğu Kat') or x.get('Kat'), 'katS': oz.get('Kat Sayısı'),
                 'yas': yas, 'yeni': yn is not None and yn <= 5, 'site': site, 'isi': dt.get('Isıtma Tipi'), 'otop': dt.get('Otopark'),
                 'asan': dt.get('Asansör'), 'kul': dt.get('Kullanım Durumu'), 'tapu': dt.get('Tapu Durumu'), 'aidat': dt.get('Aidat'),
                 'kredi': dt.get('Krediye Uygunluk'), 'tarih': x.get('tarih'), 'tip': dt.get('Kategori'),
                 'lat': round(lat, 6), 'lng': round(lng, 6)}
            if siteB: o['siteB'] = 1
            out.append(o)
    if not out: raise SystemExit('Tarama dosyası yok veya konumlu ilan yok.')
    # 1) aynı başlık + fiyat + m² → tek ilan
    seen, ded = {}, []
    for o in out:
        k = (o['b'], o['t'].strip().lower(), o['p'], o['brut'] or o['m2'])
        if k in seen: seen[k].setdefault('alt', []).append(o['u']); continue
        seen[k] = o; ded.append(o)
    n1 = len(out) - len(ded); out = ded
    # 2) farklı başlıkla verilmiş aynı daire
    grp = OrderedDict()
    for o in out: grp.setdefault((o['b'], o['mh'], o['p'], o['brut'] or o['m2'], o['oda'], o['kat'], o['yas']), []).append(o)
    ded = []
    for v in grp.values():
        r = v[0]
        if len(v) > 1:
            r['alt'] = r.get('alt', []) + [u for x in v[1:] for u in [x['u']] + x.get('alt', [])]
            r['site'] = any(x['site'] for x in v)
        ded.append(r)
    n2 = len(out) - len(ded); out = ded
    # uç fiyatları at (yanlış girilmiş kira, arsa vb.)
    ps = sorted(o['p'] for o in out); lo, hi = ps[int(len(ps) * .01)], ps[min(len(ps) - 1, int(len(ps) * .99))]
    n3 = len(out); out = [o for o in out if lo <= o['p'] <= hi]; n3 -= len(out)
    say = esle(out, geo)
    json.dump(out, open(os.path.join(kok, 'ilan.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    # fiyat adımları: verinin tamamını kapsasın
    pmin, pmax = min(o['p'] for o in out) / 1e6, max(o['p'] for o in out) / 1e6
    # uçlar verinin kendisi: en ucuz ilan aşağı, en pahalı ilan yukarı yuvarlanır (0,05 M₺ adım)
    lo_, hi_ = math.floor(pmin * 20) / 20, math.ceil(pmax * 20) / 20
    ara = [v for v in ADIM if lo_ * 1.08 < v < hi_ / 1.08]
    steps = [round(lo_, 2)] + ara + [round(hi_, 2)]
    cfg['fiyat'] = {'adimlar': steps, 'min': steps[0], 'max': steps[-1]}
    gun = sorted({d for s in tarih.values() for d in s})
    if gun:
        cfg['tarama'] = {'varsayilan': gun[-1], 'ilce': {b: max(s) for b, s in tarih.items()}}
        d0, d1 = [list(map(int, d.split('-'))) for d in (gun[0], gun[-1])]
        cfg['tarama']['metin'] = (f'{d0[2]} {AY[d0[1] - 1]} {d0[0]}' if gun[0] == gun[-1] else
                                  f'{d0[2]}–{d1[2]} {AY[d1[1] - 1]} {d1[0]}' if d0[:2] == d1[:2] else f'{d0[2]} {AY[d0[1] - 1]} – {d1[2]} {AY[d1[1] - 1]} {d1[0]}')
        cfg['kaynak_notu'] = (f"Kaynak: emlakjet.com, {cfg['tarama']['metin']}; her ilçenin satılık konut ilanlarından fiyat dağılımına yayılmış örnek alındı, "
                              "aynı dairenin tekrar ilanları birleştirildi. Konumlar ilan sahibinin girdiği noktadır. Resmî veriler: TÜİK, TCMB. "
                              "Sınırlar: HDX COD-AB-TUR, il açık verileri ve © OpenStreetMap katkıcıları. Harita: © Esri.")
    json.dump(cfg, open(os.path.join(kok, 'config.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    ip = os.path.join(kok, '..', 'index.json'); idx = json.load(open(ip, encoding='utf-8'))
    for c in idx['sehirler']:
        if c['id'] == sehir: c['durum'] = 'hazir'
    json.dump(idx, open(ip, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    per = {}
    for o in out: per[o['b']] = per.get(o['b'], 0) + 1
    print(f'{len(out)} ilan · tekrar {n1}+{n2} · uç fiyat {n3} · mahalle: konum {say["konum"]}, ad {say["ad"]}, yok {say["yok"]}')
    print('ilçe:', ', '.join(f'{b} {n}' for b, n in per.items()))
    print('fiyat adımları:', steps[0], '…', steps[-1], 'M₺ · medyan m²:',
          round(statistics.median(o['p'] / int(re.sub(r'\D', '', o['brut'] or o['m2'] or '0') or 1) for o in out if re.sub(r'\D', '', o['brut'] or o['m2'] or ''))))


if __name__ == '__main__':
    main()
