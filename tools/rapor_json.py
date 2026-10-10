"""Tüm ilçeler için rapor veri setlerini (ilce sütunlu JSON) üretir. Kullanım: python3 tools/rapor_json.py <cikis_klasoru>"""
import json, subprocess, sys, os
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
ILCELER = ['Avcılar', 'Bağcılar', 'Başakşehir', 'Beylikdüzü', 'Esenyurt', 'Güngören', 'Küçükçekmece']
sets = {k: [] for k in ['ozet', 'yas', 'oda', 'mahalle', 'bekleme']}
for il in ILCELER:
    tmp = os.path.join(OUT, '_tmp.json')
    subprocess.run([sys.executable, 'tools/rapor_veri.py', il, tmp], check=True)
    a = json.load(open(tmp)); y = {r['g']: r for r in a['yas']}
    sifir = y['Yapım aşamasında']['n'] + y['Sıfır (oturuma hazır)']['n']
    sets['ozet'].append({'ilce': il, 'ilan': a['n'], 'm2_medyan': a['m2_med'], 'fiyat_medyan': a['p_med'], 'brut_medyan': a['brut_med'],
        'sifir_ilan': sifir, 'sifir_bos': a['sifir_bos'], 'yapimda_ilan': y['Yapım aşamasında']['n'], 'yeni_m2': a['yeni_m2'], 'eski_m2': a['eski_m2'],
        'bekleme_medyan_gun': a['gun_med'], 'bekleme_yeni_gun': a['gun_yeni'], 'bekleme_eski_gun': a['gun_eski'],
        'fiyat_alt': 5500000, 'fiyat_ust': 10000000, 'tarama': a['tarama']})
    sets['yas'] += [{'ilce': il, 'yas': r['g'], 'ilan': r['n'], 'm2_medyan': r['m2'], 'fiyat_medyan': r['p'], 'brut_medyan': r['brut']} for r in a['yas']]
    sets['oda'] += [{'ilce': il, 'oda': r['oda'], 'ilan': r['n'], 'm2_medyan': r['m2'], 'fiyat_medyan': r['p'], 'brut_medyan': r['brut'], 'net_medyan': r['net']} for r in a['oda_yeni']]
    sets['mahalle'] += [{'ilce': il, 'mahalle': r['mah'], 'ilan': r['n'], 'm2_medyan': r['m2'], 'yeni_ilan': r['yeni_n'], 'yeni_m2': r['yeni_m2'],
        'sifir_ilan': r['sifir'], 'yapimda': r['yapim'], 'site_pay': r['site'], 'bekleme_gun': r['gun']} for r in a['mah']]
    sets['bekleme'] += [{'ilce': il, 'aralik': r['g'], 'ilan': r['n']} for r in a['gun_dag']]
    ilce = [{'ilce': r['ilce'], 'ilan': r['n'], 'm2_medyan': r['m2'], 'yeni_m2': r['yeni_m2'], 'sifir_pay': r['sifir_pay']} for r in a['ilceler']]
    os.remove(tmp)
sets['ilce'] = ilce
for k, v in sets.items():
    json.dump(v, open(os.path.join(OUT, f'rapor-{k}.json'), 'w'), ensure_ascii=False)
    print(k, len(v))
