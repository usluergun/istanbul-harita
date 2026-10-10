"""Müteahhit pazar raporunu ilçe başına A4 PDF olarak üretir.
Kullanım: python3 tools/rapor_pdf.py <rapor_json_klasoru> <cikis_klasoru> [İlçe ...]"""
import json, os, sys, html, unicodedata, asyncio
from playwright.async_api import async_playwright

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
L = {k: json.load(open(os.path.join(SRC, f'rapor-{k}.json'))) for k in ['ozet', 'yas', 'oda', 'mahalle', 'bekleme', 'ilce']}
RESMI = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'data', 'resmi.json'), encoding='utf-8'))
LOC = {'Avcılar': "Avcılar'da", 'Bağcılar': "Bağcılar'da", 'Başakşehir': "Başakşehir'de", 'Beylikdüzü': "Beylikdüzü'nde", 'Esenyurt': "Esenyurt'ta", 'Güngören': "Güngören'de", 'Küçükçekmece': "Küçükçekmece'de"}
ILCELER = [unicodedata.normalize('NFC', a) for a in sys.argv[3:]] or [r['ilce'] for r in L['ozet']]
SLUG = {'Avcılar': 'avcilar', 'Bağcılar': 'bagcilar', 'Başakşehir': 'basaksehir', 'Beylikdüzü': 'beylikduzu', 'Esenyurt': 'esenyurt', 'Güngören': 'gungoren', 'Küçükçekmece': 'kucukcekmece'}
AY = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']

def nf(v): return f'{round(v):,}'.replace(',', '.')
def tl(v): return '—' if v is None else nf(v) + ' TL'
def mtl(v): return ('%.2f' % (v / 1e6)).rstrip('0').rstrip('.').replace('.', ',') + ' M₺'
def pct(v): return '%' + str(round(v * 100))
def k1(v): return ('%.1f' % (v / 1000)).replace('.', ',') + 'B'
def tarih(s): y, m, d = s.split('-'); return f'{int(d)} {AY[int(m) - 1]} {y}'
e = html.escape

CSS = """
@page { size: A4; margin: 14mm 14mm 16mm; }
* { box-sizing: border-box; }
body { font-family: 'Inter', 'DejaVu Sans', sans-serif; font-size: 9.6pt; color: #1d2329; margin: 0; }
h1 { font-family: 'Lora', 'DejaVu Serif', serif; font-weight: 500; font-size: 24pt; margin: 2mm 0 2mm; letter-spacing: -.01em; }
h2, h3 { break-after: avoid; }
h2 { font-size: 12pt; font-weight: 600; margin: 0 0 2.5mm; }
h3 { font-size: 10.5pt; font-weight: 600; margin: 0 0 1mm; }
.eyebrow { font-size: 7.6pt; letter-spacing: .08em; text-transform: uppercase; color: #6a737c; }
.lede { font-size: 10.5pt; line-height: 1.5; margin: 0 0 5mm; max-width: 165mm; }
.tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 3mm; margin-bottom: 5mm; }
.tile { border: 1px solid #dfe3e6; border-radius: 2mm; padding: 3mm 3.5mm; }
.tile .l { font-size: 7.8pt; color: #6a737c; }
.tile .b { font-family: 'Lora', 'DejaVu Serif', serif; font-size: 17pt; margin: 1mm 0; font-variant-numeric: tabular-nums; }
.tile .n { font-size: 7.6pt; color: #6a737c; line-height: 1.4; }
.tile .n span { display: block; white-space: nowrap; }
.tile .l { white-space: nowrap; }
.card { border: 1px solid #dfe3e6; border-radius: 2mm; padding: 3.5mm 4mm; margin-bottom: 4.5mm; break-inside: avoid; }
.note { font-size: 7.8pt; color: #6a737c; margin: 0 0 2.5mm; line-height: 1.4; }
ul.reads { margin: 0; padding-left: 4.5mm; line-height: 1.5; }
ul.reads li { margin-bottom: 1.2mm; }
b { font-weight: 600; }
table { width: 100%; border-collapse: collapse; font-size: 8.2pt; font-variant-numeric: tabular-nums; }
th { text-align: right; font-weight: 600; color: #6a737c; border-bottom: 1px solid #c9cfd4; padding: 1.2mm 1.5mm; white-space: nowrap; }
td { text-align: right; padding: 1.1mm 1.5mm; border-bottom: 1px solid #eceff1; white-space: nowrap; }
th:first-child, td:first-child { text-align: left; }
.bar { display: inline-block; height: 2.2mm; border-radius: 1mm; background: #c4cad0; vertical-align: middle; margin-right: 1.5mm; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; }
.hb { display: grid; grid-template-columns: auto 1fr auto; gap: 1.3mm 2mm; align-items: center; font-size: 8.2pt; }
.hb .lab { text-align: right; white-space: nowrap; }
.hb .trk { height: 4mm; }
.hb .fill { height: 100%; border-radius: 1mm; background: #c4cad0; }
.hb .fill.hi { background: #2a6f97; }
.hb .val { color: #6a737c; white-space: nowrap; font-variant-numeric: tabular-nums; }
.vb { display: flex; align-items: flex-end; gap: 4mm; height: 38mm; padding-top: 5mm; border-bottom: 1px solid #c9cfd4; }
.vb .c { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; }
.vb .c i { display: block; width: 60%; background: #2a6f97; border-radius: 1mm 1mm 0 0; }
.vb .c span { font-size: 8pt; margin-bottom: 1mm; }
.vbl { display: flex; gap: 4mm; font-size: 7.6pt; color: #6a737c; margin-top: 1mm; }
.vbl span { flex: 1; text-align: center; }
.method { font-size: 7.8pt; color: #4f5961; line-height: 1.5; }
.method p { margin: 0 0 1.5mm; }
.foot { margin-top: 3mm; font-size: 7.4pt; color: #8a939b; }
.pb { break-before: page; }
"""

def hbars(rows, label, value, side, hi):
    mx = max(value(r) for r in rows) or 1
    out = ['<div class="hb">']
    for r in rows:
        out.append(f'<div class="lab">{e(label(r))}</div><div class="trk"><div class="fill{" hi" if hi(r) else ""}" style="width:{100 * value(r) / mx:.1f}%"></div></div><div class="val">{e(side(r))}</div>')
    return ''.join(out) + '</div>'

def sp(v): return ('+' if v >= 0 else '−') + '%' + ('%.1f' % abs(v * 100)).rstrip('0').rstrip('.').replace('.', ',')

def resmi(il):
    T, C = RESMI['tuik'], RESMI['tcmb']; n = T['ilce'].get(il)
    rows = sorted(({'b': b, 'v': v} for b, v in T['ilce'].items()), key=lambda r: -r['v'])
    tiles = (f'<div class="tile"><div class="l">İlçede satılan konut</div><div class="b">{nf(n)}</div><div class="n"><span>İstanbul\'un %{("%.1f" % (100 * n / T["istanbul"]["satis"])).replace(".", ",")}\'i</span></div></div>' if n else '')
    tiles += (f'<div class="tile"><div class="l">İstanbul\'da satılan konut</div><div class="b">{nf(T["istanbul"]["satis"])}</div><div class="n"><span>İlk el {pct(T["istanbul"]["ilk_el"] / T["istanbul"]["satis"])} · ipotekli {pct(T["istanbul"]["ipotekli"] / T["istanbul"]["satis"])}</span></div></div>'
              f'<div class="tile"><div class="l">İstanbul fiyat, yıllık</div><div class="b">{sp(C["istanbul_fiyat_yillik"])}</div><div class="n"><span>Aylık {sp(C["istanbul_fiyat_aylik"])} · TCMB</span></div></div>'
              f'<div class="tile"><div class="l">Türkiye fiyat, reel yıllık</div><div class="b">{sp(C["turkiye_fiyat_reel_yillik"])}</div><div class="n"><span>İstanbul kira {sp(C["istanbul_kira_yillik"])}</span></div></div>')
    return f'''<div class="card"><h2>Resmî veriler · {e(RESMI["donem"])}</h2>
<p class="note">Satılan konut: tapuda el değiştiren konut adedi (yalnızca ilan bandı değil, tüm fiyatlar).</p>
<div class="tiles" style="margin-bottom:3mm">{tiles}</div>
<h3>Aynı ay komşu ilçelerde satılan konut</h3>
{hbars(rows, lambda r: r['b'], lambda r: r['v'], lambda r: nf(r['v']), lambda r: r['b'] == il)}
<p class="note" style="margin:2mm 0 0">Kaynak: {e(T["kaynak"])}; {e(C["kaynak"])}.</p></div>'''

AYAD = {'01':'Oca','02':'Şub','03':'Mar','04':'Nis','05':'May','06':'Haz','07':'Tem','08':'Ağu','09':'Eyl','10':'Eki','11':'Kas','12':'Ara'}
def talep_rows():
    A, N = RESMI['tuik']['aylik'], RESMI['nufus']; son3 = sorted(A)[-3:]
    rows = []
    for b in RESMI['tuik']['ilce']:
        s3 = sum(A[m].get(b, 0) for m in son3); n = N['2025'][b]
        rows.append({'b': b, 's3': s3, 'nf': n, 'dn': n / N['2021'][b] - 1, 'k': s3 / len(son3) * 12 / n * 1000})
    return sorted(rows, key=lambda r: -r['k']), son3

def k1d(v): return ('%.1f' % v).replace('.', ',')

def talep(il):
    A = RESMI['tuik']['aylik']; rows, son3 = talep_rows(); Y = RESMI['yapi_izin']
    seri = [(AYAD[m[5:]] + ' ' + m[2:4], A[m].get(il, 0)) for m in sorted(A)]
    mx = max(v for _, v in seri) or 1
    vb = ''.join(f'<div class="c"><span>{nf(v)}</span><i style="height:{80 * v / mx:.1f}%"></i></div>' for _, v in seri)
    vbl = ''.join(f'<span>{e(g)}</span>' for g, _ in seri)
    tr = ''.join(f'<tr{" style=\"background:#e8f1f6;font-weight:600\"" if r["b"] == il else ""}><td>{e(r["b"])}</td><td>{nf(r["s3"])}</td><td>{nf(r["nf"])}</td><td>{sp(r["dn"])}</td><td>{k1d(r["k"])}</td></tr>' for r in rows)
    return f'''<div class="card"><h2>Son aylar ve talep · {e(il)}</h2>
<div class="two"><div><h3>Tapuda satılan konut, aylık</h3><div class="vb" style="height:30mm">{vb}</div><div class="vbl">{vbl}</div>
<p class="note" style="margin:2mm 0 0">Şubat–Nisan 2026 ilçe verisi bulunamadı.</p></div>
<div><h3>Talebin nüfusa göre yoğunluğu</h3><table><thead><tr><th>İlçe</th><th>3 ay satış</th><th>Nüfus 2025</th><th>2021–25</th><th>Satış/1.000</th></tr></thead><tbody>{tr}</tbody></table>
<p class="note" style="margin:2mm 0 0">3 ay: {"–".join(AYAD[m[5:]] for m in son3)} {son3[0][:4]}. Satış/1.000: 1.000 kişiye düşen yıllık konut satışı.</p></div></div>
<p class="note" style="margin:2mm 0 0"><b>Gelecek arz (Türkiye geneli):</b> Yapı ruhsatı alan daire sayısı 2026'nın 1. çeyreğinde yıllık {sp(Y["ruhsat_daire_2026c1_yillik"])} artışla {nf(Y["ruhsat_daire_2026c1"])} oldu, 2. çeyrekte {sp(Y["ruhsat_daire_2026c2_yillik"])} değişti; iskân alan daire sayısı 2. çeyrekte {sp(Y["iskan_daire_2026c2_yillik"])} arttı. İstanbul ve ilçe kırılımı bulunamadı.</p></div>'''

def sayfa(il):
    o = next(r for r in L['ozet'] if r['ilce'] == il)
    yas = [r for r in L['yas'] if r['ilce'] == il and r['ilan'] > 0]
    oda = [r for r in L['oda'] if r['ilce'] == il]
    mah = sorted([r for r in L['mahalle'] if r['ilce'] == il], key=lambda r: -r['m2_medyan'])
    bek = [r for r in L['bekleme'] if r['ilce'] == il]
    prim = o['yeni_m2'] / o['eski_m2'] - 1
    bos = o['sifir_bos'] / o['sifir_ilan'] if o['sifir_ilan'] else 0
    toda = sum(r['ilan'] for r in oda) or 1
    lede = (f"Fiyat bandındaki <b>{nf(o['ilan'])}</b> ilanın <b>{nf(o['sifir_ilan'])}</b>'i sıfır daire. "
            + (f"Yeni binalar m²'de eski binalardan <b>{pct(prim)}</b> pahalı" if prim >= 0 else f"Yeni binalar m²'de eski binalardan <b>{pct(-prim)}</b> ucuz")
            + (f"; yeni arzın <b>{pct(oda[0]['ilan'] / toda)}</b>'i {e(oda[0]['oda'])}." if oda else '.'))
    reads = []
    rk = sorted([r for r in mah if r['sifir_ilan'] > 0], key=lambda r: -r['sifir_ilan'])[:4]
    lst = lambda rows, f: ''.join((', ' if i and i < len(rows) - 1 else (' ve ' if i else '')) + f'{e(r["mahalle"])} (<b>{f(r)}</b>)' for i, r in enumerate(rows))
    if rk: reads.append('Rekabet en yoğun: ' + lst(rk, lambda r: nf(r['sifir_ilan']) + ' sıfır ilan') + '. Bu mahallelerde yeni proje, satılmayı bekleyen sıfır stokla yarışır.')
    yt = sorted([r for r in mah if r['yeni_m2'] is not None], key=lambda r: -r['yeni_m2'])[:3]
    if yt: reads.append('Yeni binada en yüksek m² fiyatı: ' + lst(yt, lambda r: tl(r['yeni_m2'])) + '.')
    s = sorted(r['m2_medyan'] for r in mah); med = s[len(s) // 2]
    az = [r for r in mah if r['m2_medyan'] > med and r['yeni_ilan'] < 3 and r['ilan'] >= 10]
    if az: reads.append('Fiyatı ilçe ortancasının üstünde ama yeni arzı neredeyse yok: ' + ', '.join(f'{e(r["mahalle"])} (<b>{tl(r["m2_medyan"])}</b>, <b>{r["yeni_ilan"]}</b> yeni ilan)' for r in az) + '. Arsa veya kentsel dönüşüm fırsatı burada aranabilir.')
    if len(oda) >= 2: reads.append(f'Yeni binalarda arz {e(oda[0]["oda"])} (<b>{pct(oda[0]["ilan"] / toda)}</b>) ve {e(oda[1]["oda"])} (<b>{pct(oda[1]["ilan"] / toda)}</b>) ağırlıklı. Bu tiplerde fiyatla, diğerlerinde farklılaşarak rekabet edilir.')
    if il in RESMI['tuik']['ilce']:
        C = RESMI['tcmb']
        reads.append(f"{e(RESMI['donem'])}'da {e(LOC.get(il, il))} <b>{nf(RESMI['tuik']['ilce'][il])}</b> konut el değiştirdi. İstanbul'da fiyatlar yıllık <b>{sp(C['istanbul_fiyat_yillik'])}</b> arttı; Türkiye genelinde reel olarak <b>{sp(C['turkiye_fiyat_reel_yillik'])}</b>, yani fiyatlar enflasyonun gerisinde.")
    tr_, _ = talep_rows(); me = next((r for r in tr_ if r['b'] == il), None)
    if me:
        ort = sum(r['k'] for r in tr_) / len(tr_)
        reads.append(f"Talep yoğunluğu: {e(LOC.get(il, il))} 1.000 kişiye yılda <b>{k1d(me['k'])}</b> konut satışı düşüyor (7 ilçe ortalaması <b>{k1d(ort)}</b>). Nüfus 2021'den bu yana <b>{sp(me['dn'])}</b> değişti.")
    if o['sifir_ilan']: reads.append(f'Sıfır dairelerin <b>{pct(bos)}</b>\'i boş, yani satılmayı bekleyen stok. Fiyat kararı bu stoka göre verilmeli.')
    mx = max(r['m2_medyan'] for r in mah)
    mrows = ''.join(f'<tr><td>{e(r["mahalle"])}</td><td>{nf(r["ilan"])}</td><td><span class="bar" style="width:{14 * r["m2_medyan"] / mx:.1f}mm"></span>{tl(r["m2_medyan"])}</td><td>{tl(r["yeni_m2"])}</td><td>{nf(r["sifir_ilan"])}</td><td>{nf(r["yapimda"])}</td><td>%{r["site_pay"]}</td><td>{nf(r["bekleme_gun"])} gün</td></tr>' for r in mah)
    orows = ''.join(f'<tr><td>{e(r["oda"])}</td><td>{nf(r["ilan"])}</td><td>{mtl(r["fiyat_medyan"])}</td><td>{nf(r["brut_medyan"])} m²</td><td>{nf(r["net_medyan"])} m²</td><td>{tl(r["m2_medyan"])}</td></tr>' for r in oda)
    bmx = max(r['ilan'] for r in bek) or 1
    vb = ''.join(f'<div class="c"><span>{nf(r["ilan"])}</span><i style="height:{80 * r["ilan"] / bmx:.1f}%"></i></div>' for r in bek)
    vbl = ''.join(f'<span>{e(r["aralik"])}</span>' for r in bek)
    band = f'{mtl(o["fiyat_alt"])} – {mtl(o["fiyat_ust"])}'
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="eyebrow">Müteahhitler için pazar raporu · örnek</div>
<h1>{e(il)} konut pazarı</h1>
<p class="lede">{lede}</p>
<div class="tiles">
 <div class="tile"><div class="l">Satılık daire ilanı</div><div class="b">{nf(o['ilan'])}</div><div class="n"><span>{band} arası</span></div></div>
 <div class="tile"><div class="l">Ortanca brüt m² fiyatı</div><div class="b">{tl(o['m2_medyan'])}</div><div class="n"><span>Ortanca daire {mtl(o['fiyat_medyan'])}</span><span>{nf(o['brut_medyan'])} m² brüt</span></div></div>
 <div class="tile"><div class="l">Sıfır daire ilanı</div><div class="b">{nf(o['sifir_ilan'])}</div><div class="n"><span>{nf(o['yapimda_ilan'])} yapım aşamasında</span><span>{pct(bos)} boş (satılmamış)</span></div></div>
 <div class="tile"><div class="l">Yeni binanın m² farkı</div><div class="b">{('+' if prim >= 0 else '−') + pct(abs(prim))}</div><div class="n"><span>0–5 yaş: {tl(o['yeni_m2'])}/m²</span><span>6+ yaş: {tl(o['eski_m2'])}/m²</span></div></div>
</div>
{resmi(il)}
{talep(il)}
<div class="card"><h2>Müteahhit için okuma</h2><ul class="reads">{''.join(f'<li>{r}</li>' for r in reads)}</ul></div>
<div class="card" style="break-inside:auto"><h2>Mahalleler</h2><p class="note">m² fiyatına göre sıralı. Yeni bina m²: mahallede en az 3 yeni (0–5 yaş) ilan varsa. Bekleme: ilan tarihinden tarama gününe geçen ortanca süre.</p>
<table><thead><tr><th>Mahalle</th><th>İlan</th><th>m² fiyatı</th><th>Yeni bina m²</th><th>Sıfır ilan</th><th>Yapımda</th><th>Site içi</th><th>Bekleme</th></tr></thead><tbody>{mrows}</tbody></table></div>
<div class="two">
 <div class="card"><h3>Bina yaşına göre m² fiyatı</h3><p class="note">Ortanca brüt m² fiyatı · ilan adedi. Sıfır gruplar renkli.</p>
 {hbars(yas, lambda r: r['yas'], lambda r: r['m2_medyan'], lambda r: k1(r['m2_medyan']) + ' · ' + nf(r['ilan']), lambda r: r['yas'].startswith(('Yapım', 'Sıfır')))}</div>
 <div class="card"><h3>İlçelere göre m² fiyatı</h3><p class="note">Aynı fiyat bandında ortanca brüt m² · sıfır ilan payı.</p>
 {hbars(L['ilce'], lambda r: r['ilce'], lambda r: r['m2_medyan'], lambda r: k1(r['m2_medyan']) + ' · %' + str(r['sifir_pay']), lambda r: r['ilce'] == il)}</div>
</div>
<div class="two">
 <div class="card"><h3>Yeni binalarda daire tipi</h3><p class="note">0–5 yaş binalar, en az 3 ilanı olan tipler.</p>
 <table><thead><tr><th>Tip</th><th>İlan</th><th>Fiyat</th><th>Brüt</th><th>Net</th><th>m² fiyatı</th></tr></thead><tbody>{orows}</tbody></table></div>
 <div class="card"><h3>İlanda bekleme süresi</h3><p class="note">Yeni binalarda ortanca {nf(o['bekleme_yeni_gun'])} gün, eski binalarda {nf(o['bekleme_eski_gun'])} gün.</p>
 <div class="vb">{vb}</div><div class="vbl">{vbl}</div></div>
</div>
<div class="card method"><h3>Yöntem ve sınırlar</h3>
<p>Kaynak: emlakjet.com'daki satılık daire ilanları, tarama günü {tarih(o['tarama'])}. Yalnızca {band} fiyat bandındaki ilanlar tarandı; bu bandın dışındaki daireler rapora girmedi, bu yüzden küçük 1+1'ler ve büyük daireler eksik temsil ediliyor.</p>
<p>m² fiyatı = ilan fiyatı ÷ brüt m². Mahalle ve tip değerleri ortancadır (medyan). Aynı daire birden fazla kez ilan verildiyse bir kez sayıldı. Bunlar ilan (istenen) fiyatlarıdır, satış fiyatı değildir. Satılıp yayından kalkan ilanlar bu taramada görünmez; gerçek satış hızı için düzenli tarama gerekir.</p>
<p>Resmî veriler: satış adetleri TÜİK'in tapu kayıtlarından, fiyat değişimi TCMB'nin banka değerleme raporlarına dayanan endeksinden, nüfus TÜİK Adrese Dayalı Nüfus Kayıt Sistemi'nden, yapı izinleri TÜİK Yapı İzin İstatistikleri'nden alınmıştır.</p>
<p>Sıfır: 0 yaş (yapım aşamasında veya oturuma hazır). Yeni bina: 0–5 yaş.</p></div>
</body></html>"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        for il in ILCELER:
            await pg.set_content(sayfa(il), wait_until='load')
            path = os.path.join(OUT, f'muteahhit-raporu-{SLUG[il]}.pdf')
            await pg.pdf(path=path, format='A4', print_background=True, display_header_footer=True,
                         header_template='<span></span>',
                         footer_template=f'<div style="font-size:7px;color:#8a939b;width:100%;padding:0 14mm;display:flex;justify-content:space-between;font-family:Inter,sans-serif"><span>{e(il)} konut pazarı · örnek rapor</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
                         margin={'top': '14mm', 'bottom': '16mm', 'left': '14mm', 'right': '14mm'})
            print(path)
        await b.close()
asyncio.run(main())
