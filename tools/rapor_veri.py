"""Müteahhit pazar raporu için ilçe verisini özetler. Kullanım: python3 tools/rapor_veri.py Küçükçekmece"""
import re, json, sys, statistics as st, collections, datetime
import unicodedata
ILCE = unicodedata.normalize('NFC', sys.argv[1] if len(sys.argv) > 1 else 'Küçükçekmece')
I = json.load(open('data/ilan.json')); G = json.load(open('data/geo.json'))
SCRAPE = datetime.date(2026, 9, 26)
def brut(x):
    m = re.match(r'\s*([0-9.]+)', str(x.get('brut') or x.get('m2') or ''))
    if not m: return 0
    n = int(m.group(1).replace('.', ''))
    return n if 30 <= n <= 1000 else 0
def med(a): return round(st.median(a)) if a else None
def m2(x): return x['p'] / brut(x)
def yas_grp(y):
    if y.startswith('0 (Yap'): return 'Yapım aşamasında'
    if y.startswith('0'): return 'Sıfır (oturuma hazır)'
    if y in ('1','2','3','4','5'): return '1–5 yaş'
    if y in ('6-10',): return '6–10 yaş'
    return '11+ yaş'
def gun(x):
    try: return (SCRAPE - datetime.date.fromisoformat(x['tarih'])).days
    except: return None
A = [x for x in I if brut(x)]
K = [x for x in A if x['b'] == ILCE]
out = {'ilce': ILCE, 'n': len(K), 'tarama': str(SCRAPE)}
out['m2_med'] = med([m2(x) for x in K]); out['p_med'] = med([x['p'] for x in K]); out['brut_med'] = med([brut(x) for x in K])
yeni = [x for x in K if x['yeni']]; eski = [x for x in K if not x['yeni']]
out['yeni_n'] = len(yeni); out['yeni_m2'] = med([m2(x) for x in yeni]); out['eski_m2'] = med([m2(x) for x in eski])
s = [x for x in yeni if x['site']]; ns = [x for x in yeni if not x['site']]
out['yeni_site_m2'] = med([m2(x) for x in s]); out['yeni_nosite_m2'] = med([m2(x) for x in ns]); out['yeni_site_n']=len(s); out['yeni_nosite_n']=len(ns)
# yaş grupları
yg = collections.defaultdict(list)
for x in K: yg[yas_grp(x['yas'])].append(x)
order = ['Yapım aşamasında','Sıfır (oturuma hazır)','1–5 yaş','6–10 yaş','11+ yaş']
out['yas'] = [{'g': g, 'n': len(yg[g]), 'm2': med([m2(x) for x in yg[g]]), 'p': med([x['p'] for x in yg[g]]), 'brut': med([brut(x) for x in yg[g]])} for g in order]
# oda tipi (yeni binalar)
def oda_n(o): return {'Stüdyo (1+0)':'1+0'}.get(o, o)
og = collections.defaultdict(list)
for x in yeni: og[oda_n(x['oda'])].append(x)
out['oda_yeni'] = sorted([{'oda': o, 'n': len(v), 'm2': med([m2(x) for x in v]), 'p': med([x['p'] for x in v]), 'brut': med([brut(x) for x in v]),
    'net': med([int(re.match(r'\s*([0-9]+)', x['net']).group(1)) for x in v if re.match(r'\s*[0-9]+', x['net'])])} for o, v in og.items() if len(v) >= 3], key=lambda r: -r['n'])
# mahalleler
F = G['mah']['features']; mg = collections.defaultdict(list)
for x in K:
    if x['mk'] >= 0: mg[F[x['mk']]['properties']['n']].append(x)
rows = []
for n, v in mg.items():
    yv = [x for x in v if x['yeni']]
    rows.append({'mah': n.replace(' Mahallesi',''), 'n': len(v), 'm2': med([m2(x) for x in v]), 'yeni_n': len(yv), 'yeni_m2': med([m2(x) for x in yv]) if len(yv) >= 3 else None,
                 'sifir': sum(1 for x in v if x['yas'].startswith('0')), 'yapim': sum(1 for x in v if x['yas'].startswith('0 (Yap')),
                 'site': round(100*sum(x['site'] for x in v)/len(v)), 'gun': med([g for g in map(gun, v) if g is not None])})
out['mah'] = sorted(rows, key=lambda r: -(r['m2'] or 0))
# ilçe karşılaştırması
ig = collections.defaultdict(list)
for x in A: ig[x['b']].append(x)
out['ilceler'] = sorted([{'ilce': b, 'n': len(v), 'm2': med([m2(x) for x in v]), 'yeni_m2': med([m2(x) for x in v if x['yeni']]),
    'sifir_pay': round(100*sum(1 for x in v if x['yas'].startswith('0'))/len(v))} for b, v in ig.items()], key=lambda r: -r['m2'])
# ilan süresi
gs = [g for g in map(gun, K) if g is not None]
out['gun_med'] = med(gs); out['gun_yeni'] = med([g for g in map(gun, yeni) if g is not None]); out['gun_eski'] = med([g for g in map(gun, eski) if g is not None])
out['gun_dag'] = [{'g': lab, 'n': sum(1 for g in gs if lo <= g < hi)} for lab, lo, hi in [('0–30 gün',0,31),('31–90 gün',31,91),('91–180 gün',91,181),('180+ gün',181,99999)]]
# diğer özellikler
c = lambda f: collections.Counter(x.get(f) for x in K)
out['tapu'] = c('tapu').most_common(5); out['kul'] = c('kul').most_common(3); out['otop'] = c('otop').most_common(4); out['isi'] = c('isi').most_common(4)
out['sifir_bos'] = sum(1 for x in K if x['yas'].startswith('0') and x['kul'] == 'Boş')
out['yabanci'] = sum(1 for x in K if x['tapu'] == 'Yabancıdan')
out['kredi_uygun'] = round(100*sum(1 for x in K if x['kredi']=='Krediye Uygun')/len(K))
out['aidat_yeni_site'] = med([int(re.sub(r'[^0-9]', '', str(x['aidat']).split(',')[0])) for x in s if x.get('aidat') and re.search(r'[0-9]', str(x['aidat']))])
out['site_list'] = collections.Counter()
json.dump(out, open(sys.argv[2] if len(sys.argv)>2 else '/dev/stdout','w'), ensure_ascii=False, indent=1, default=list)
