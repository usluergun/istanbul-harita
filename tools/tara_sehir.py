#!/usr/bin/env python3
"""emlakjet satılık konut taraması (şehir ayar dosyasındaki ilçeler için). İnternet erişimi olan bilgisayarda çalışır.

Kullanım:
    python3 tools/tara_sehir.py izmir                 # tüm ilçeler
    python3 tools/tara_sehir.py izmir --ilce Urla     # tek ilçe
    python3 tools/tara_sehir.py izmir --detay 300 --bekle 1.5

1. aşama: ilçenin tüm liste sayfaları (fiyat sınırı yok; ~50 sayfa sınırına takılırsa mahalle sayfalarıyla tamamlanır)
          → sehirler/<şehir>/_tarama/<ilçe>_tum.json
2. aşama: fiyat dağılımına eşit yayılmış en çok --detay ilanın detay sayfası (konum, bina yaşı, site, brüt/net …)
          → sehirler/<şehir>/_tarama/<ilçe>_secili.json  (yarıda kesilirse kaldığı yerden devam eder)
robots.txt: /satilik-konut/…?sayfa= ve /ilan/ izinli; istekler arasında bekleme yapılır.
"""
import re, json, time, html, sys, os, urllib.request, argparse, datetime, unicodedata

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36'
ap = argparse.ArgumentParser()
ap.add_argument('sehir'); ap.add_argument('--ilce'); ap.add_argument('--detay', type=int, default=300)
ap.add_argument('--bekle', type=float, default=1.5)
A = ap.parse_args()
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sehirler', A.sehir)
CFG = json.load(open(os.path.join(KOK, 'config.json'), encoding='utf-8'))
OUT = os.path.join(KOK, '_tarama'); os.makedirs(OUT, exist_ok=True)
nfc = lambda s: unicodedata.normalize('NFC', s or '')


def log(*a): print(datetime.datetime.now().strftime('%H:%M:%S'), *a, flush=True)


def get(url):
    for a in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'tr-TR,tr'})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            log('tekrar', url, e); time.sleep(5 * (a + 1))
    return None


def lds(t):
    out = []
    for b in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', t, re.S):
        try: out.append(json.loads(b))
        except Exception: pass
    return out


def add_items(t, items):
    for j in lds(t):
        for g in j.get('@graph', []) if isinstance(j, dict) else []:
            if g.get('@type') != 'RealEstateListing': continue
            props = {x['name']: x['value'] for x in g.get('additionalProperty', [])}
            items[g['url']] = {'baslik': g['name'], 'url': g['url'], 'fiyat': g.get('offers', {}).get('price'),
                               'resim': g.get('image'), 'tarih': g.get('datePosted'), **props}


def crawl(base, items, label):
    first = get(base)
    if not first: return None, ''
    m = re.search(r'total_item\\\\?":\\\\?"(\d+)', first)
    total = int(m.group(1)) if m else None
    last = max([int(x) for x in re.findall(r'\?sayfa=(\d+)"', first)] + [1])
    for p in range(1, last + 1):
        t = first if p == 1 else get(f'{base}?sayfa={p}')
        if t: add_items(t, items)
        if p % 10 == 0 or p == last: log(label, 'sayfa', p, '/', last, len(items))
        time.sleep(A.bekle)
    return total, first


def detay(x):
    t = get(x['url']); time.sleep(A.bekle)
    if not t: return
    def walk(o):
        if isinstance(o, dict):
            for pv in o.get('additionalProperty', []) or []:
                x.setdefault('detay', {})[pv['name']] = pv['value']
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    for j in lds(t): walk(j)
    for val, lab in re.findall(r'font-semibold[^>]*>([^<]{1,60})</p><p[^>]*>([^<]{1,40})</p>', t):
        x.setdefault('ozet', {}).setdefault(html.unescape(lab).strip(), html.unescape(val).strip())
    m = re.search(r'\\"coordinates\\":\{\\"lat\\":([\d.]+),\\"lng\\":([\d.]+)\}', t)
    if m: x['lat'], x['lng'] = float(m.group(1)), float(m.group(2))
    x['tarama'] = datetime.date.today().isoformat()


for il in CFG['ilceler']:
    ad, slug = il['ad'], il['emlakjet']
    if A.ilce and nfc(A.ilce) != ad: continue
    key = slug.split('-', 1)[1]
    ft, fs = os.path.join(OUT, f'{key}_tum.json'), os.path.join(OUT, f'{key}_secili.json')
    base = f'https://www.emlakjet.com/satilik-konut/{slug}'
    if os.path.exists(ft):
        items = {x['url']: x for x in json.load(open(ft, encoding='utf-8'))}
        log(ad, 'liste önceden alınmış:', len(items))
    else:
        items = {}
        total, first = crawl(base, items, ad)
        log(ad, 'site toplam', total, 'toplanan', len(items))
        if total and len(items) < total * 0.98:
            slugs = sorted(set(re.findall(rf'href="/satilik-konut/{re.escape(slug)}-([a-z0-9-]+-mahallesi)"', first)))
            log(ad, 'mahalle sayfaları', len(slugs))
            for sl in slugs: crawl(f'{base}-{sl}', items, f'{ad}/{sl}')
            log(ad, 'site toplam', total, 'toplanan', len(items))
        json.dump(list(items.values()), open(ft, 'w', encoding='utf-8'), ensure_ascii=False)
    fiyatli = sorted((x for x in items.values() if x.get('fiyat') and x['fiyat'] >= 300_000), key=lambda x: x['fiyat'])
    n = min(A.detay, len(fiyatli))
    sec = [fiyatli[round(i * (len(fiyatli) - 1) / max(n - 1, 1))] for i in range(n)] if n else []
    sec = list({x['url']: x for x in sec}.values())
    onceki = {y['url']: y for y in json.load(open(fs, encoding='utf-8'))} if os.path.exists(fs) else {}
    log(ad, 'detay alınacak', len(sec), '(önceden', sum(1 for x in sec if x['url'] in onceki and 'lat' in onceki[x['url']]), ')')
    for i, x in enumerate(sec):
        if x['url'] in onceki and 'lat' in onceki[x['url']]: sec[i] = onceki[x['url']]; continue
        detay(x)
        if (i + 1) % 25 == 0:
            json.dump(sec[:i + 1], open(fs, 'w', encoding='utf-8'), ensure_ascii=False)
            log(ad, 'detay', i + 1, '/', len(sec))
    json.dump(sec, open(fs, 'w', encoding='utf-8'), ensure_ascii=False)
    log(ad, 'BİTTİ', len(sec), 'ilan, konumlu', sum(1 for x in sec if 'lat' in x))
log('ŞEHİR BİTTİ', A.sehir)
