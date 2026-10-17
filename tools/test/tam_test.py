# Çalıştırma: python3 -m http.server 8765 (depo kökünde) açıkken  python3 tools/test/tam_test.py [şehir…]  →  tools/test/sonuc.json, ekran/; karşılaştırma: python3 tools/test/sheet.py tel
"""Uçtan uca test: 6 şehir × (masaüstü, telefon 390, telefon 360). Her adımda JS hatası, yatay taşma ve
yapısal parmak izi toplanır; telefonda her adımın ekran görüntüsü alınır.
python3 tam_test.py  → sonuc.json, ekran/<sehir>_<vp>_<adim>.png"""
import json, os, sys
from playwright.sync_api import sync_playwright

H = os.path.dirname(os.path.abspath(__file__)); E = H + '/ekran'; os.makedirs(E, exist_ok=True)
URL = 'http://localhost:8765/'
SEHIR = sys.argv[1:] or ['istanbul', 'izmir', 'aydin', 'mugla', 'gaziantep', 'hatay']
VP = {'masa': dict(viewport={'width': 1440, 'height': 900}),
      'tel': dict(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True),
      'tel360': dict(viewport={'width': 360, 'height': 740}, device_scale_factor=2, is_mobile=True, has_touch=True)}

TASMA = '''() => { const W = document.documentElement.clientWidth, bad = [];
  document.querySelectorAll('body *').forEach(e => { const s = getComputedStyle(e); if (s.display === 'none' || s.visibility === 'hidden') return;
    const r = e.getBoundingClientRect(); if (!r.width || !r.height) return;
    if (e.closest('.leaflet-pane, .leaflet-control-container, .tw, .bar .in, .leaflet-marker-pane')) return;
    if (r.right > W + 1 || r.left < -1) bad.push((e.id ? '#' + e.id : e.className && typeof e.className === 'string' ? '.' + e.className.split(' ')[0] : e.tagName) + ' ' + Math.round(r.left) + '→' + Math.round(r.right)); });
  return {sw: document.documentElement.scrollWidth, W, bad: [...new Set(bad)].slice(0, 8)}; }'''
PARMAK = '''() => { const vis = e => { if (!e) return false; const s = getComputedStyle(e); const r = e.getBoundingClientRect(); return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0; };
  const ids = ['menu-btn','heat-fab','panel','close-menu','eyebrow','sehirler','rapor-link','bolgeler','f-yeni','f-site','pmin','pmax','hide','tab-list','tab-mah','tab-val','foot',
    't-heat','t-pf','t-ilce','t-mah','t-yol','t-semt','t-ilcelb','t-mahlb','t-semtlb'];
  const o = {}; ids.forEach(i => o[i] = vis(document.getElementById(i)));
  o.crm = vis(document.querySelector('.crm-link')); o.brand = vis(document.querySelector('.brand')); o.leg = vis(document.querySelector('.leg'));
  o.bases = [...document.querySelectorAll('.b-base')].filter(vis).length;
  return o; }'''


def run(b, sh, vp):
    R = {'adim': {}, 'hata': [], 'konsol': []}
    ctx = b.new_context(**VP[vp]); pg = ctx.new_page()
    pg.on('pageerror', lambda e: R['hata'].append(str(e)[:200]))
    pg.on('console', lambda m: m.type == 'error' and 'Failed to load resource' not in m.text and R['konsol'].append(m.text[:200]))
    pg.route('**/arcgisonline.com/**', lambda r: r.abort()); pg.route('**/fonts.g*/**', lambda r: r.abort())
    tel = vp != 'masa'; n = [0]

    def adim(ad, shot=True):
        pg.wait_for_timeout(350)
        t = pg.evaluate(TASMA)
        R['adim'][ad] = {'tasma': t['sw'] > t['W'] + 1, 'bad': t['bad']}
        if shot and tel: n[0] += 1; pg.screenshot(path=f'{E}/{sh}_{vp}_{n[0]:02d}_{ad}.png')

    def menu(ac):
        if not tel: return
        open_ = pg.evaluate("document.getElementById('panel').classList.contains('open') || document.body.classList.contains('menu-open')")
        if ac and not open_: pg.tap('#menu-btn')
        if not ac and open_: pg.tap('#close-menu')
        pg.wait_for_timeout(400)

    pg.goto(f'{URL}index.html?sehir={sh}')
    pg.wait_for_function("(()=>{const l=document.getElementById('loading');return (!l||l.hidden||getComputedStyle(l).display==='none') && document.getElementById('t').textContent!=='0' && !!window.__mutRap})()", timeout=60000, polling=300)
    pg.wait_for_timeout(1500)
    R['parmak'] = pg.evaluate(PARMAK); R['n'] = pg.inner_text('#n'); R['t'] = pg.inner_text('#t')
    R['fiyat'] = pg.evaluate("[document.getElementById('pmin').value, document.getElementById('pmax').value, document.getElementById('pmin').options.length]")
    R['eyebrow'] = pg.inner_text('#eyebrow')
    adim('acilis')
    menu(True); R['parmak_menu'] = pg.evaluate(PARMAK); adim('menu')
    # menü sonuna kadar kaydır
    if tel:
        pg.evaluate("document.getElementById('panel').scrollTop = 1e6"); adim('menu_son')
        R['menu_kaydir'] = pg.evaluate("(()=>{const p=document.getElementById('panel');return [p.scrollHeight,p.clientHeight,p.scrollTop]})()")
        pg.evaluate("document.getElementById('panel').scrollTop = 0")
    # sekmeler
    for t in ['tab-mah', 'tab-val', 'tab-list']:
        pg.click(f'#{t}'); pg.wait_for_timeout(300)
        pane = pg.get_attribute(f'#{t}', 'aria-controls')
        R.setdefault('sekme', {})[t] = len(pg.inner_text(f'#{pane}').strip())
        if tel: pg.evaluate("document.getElementById('panel').scrollTop = document.querySelector('.tabs').offsetTop - 4")
        adim(t)
    # filtreler
    n0 = int(pg.inner_text('#n').replace('.', ''))
    pg.click('#f-yeni'); pg.wait_for_timeout(300); n1 = int(pg.inner_text('#n').replace('.', '')); pg.click('#f-yeni')
    pg.click('#f-site'); pg.wait_for_timeout(300); n2 = int(pg.inner_text('#n').replace('.', '')); pg.click('#f-site')
    opts = pg.evaluate("[...document.getElementById('pmax').options].map(o=>o.value)")
    pg.select_option('#pmax', opts[len(opts) // 2]); pg.wait_for_timeout(300); n3 = int(pg.inner_text('#n').replace('.', ''))
    pg.select_option('#pmax', opts[-1]); pg.wait_for_timeout(300)
    R['filtre'] = {'tum': n0, 'yeni': n1, 'site': n2, 'fiyat_yari': n3, 'geri': int(pg.inner_text('#n').replace('.', ''))}
    # bölge çipi (ikinci ilçe)
    chips = pg.evaluate("[...document.querySelectorAll('#bolgeler .bolge')].map(b=>b.dataset.b)")
    il = chips[1] if len(chips) > 1 else chips[0]
    pg.click(f'#bolgeler .bolge[data-b="{il}"]'); pg.wait_for_timeout(700); R['bolge'] = [il, pg.inner_text('#n')]
    menu(False); adim('bolge_harita')
    # ilan listesinden bir ilan → harita popup
    menu(True); pg.click('#tab-list'); pg.wait_for_timeout(200)
    pg.click('#list .lrow >> nth=0'); pg.wait_for_timeout(700)
    R['popup_ilan'] = pg.locator('.leaflet-popup').count(); adim('ilan_popup')
    pg.evaluate("document.querySelectorAll('.leaflet-popup-close-button').forEach(b=>b.click())")
    # ısı haritası
    i0 = pg.get_attribute('#t-heat', 'aria-pressed')
    for _ in range(2):
        if tel: pg.tap('#heat-fab')
        else: pg.click('#t-heat')
        pg.wait_for_timeout(600)
        if _ == 0: i1 = pg.get_attribute('#t-heat', 'aria-pressed'); adim('isi_kapali')
    R['isi'] = [i0, i1, pg.get_attribute('#t-heat', 'aria-pressed')]; adim('isi')
    # mahalleler sekmesinden mahalle → popup → mahalle raporu
    menu(True); pg.click('#tab-mah'); pg.wait_for_timeout(300)
    pg.click('#mlist tr.mrow >> nth=0'); pg.wait_for_timeout(900)
    R['popup_mah'] = pg.locator('.leaflet-popup').count(); adim('mah_popup')
    if pg.locator('.hp-rep').count():
        pg.click('.hp-rep'); pg.wait_for_timeout(800)
        R['mah_rapor'] = len(pg.inner_text('#rep')); adim('mah_rapor')
        pg.evaluate("document.getElementById('rep').scrollTop=1e6"); adim('mah_rapor_son')
        pg.click('#r-close'); pg.wait_for_timeout(300)
    # değer tahmini
    menu(True); pg.click('#tab-val'); pg.wait_for_timeout(300)
    pg.fill('#v-m2', '120'); pg.click('#vform button[type=submit]'); pg.wait_for_timeout(600)
    R['deger'] = pg.inner_text('#vres')[:80].replace('\n', ' '); adim('deger_sonuc')
    pg.click('#v-rep'); pg.wait_for_timeout(800); R['deger_rapor'] = len(pg.inner_text('#rep')); adim('deger_rapor')
    pg.click('#r-close'); pg.wait_for_timeout(300)
    # müteahhit raporu: tüm ilçeler
    menu(True); pg.click('#tab-list'); pg.wait_for_timeout(200); pg.click('#rapor-link'); pg.wait_for_timeout(900); adim('mut_rapor')
    pg.evaluate("document.getElementById('rep').scrollTop=1e6"); adim('mut_rapor_son')
    ils = pg.evaluate("[...document.getElementById('r-ilce').options].map(o=>o.value)"); R['mut'] = {}
    for x in ils:
        pg.select_option('#r-ilce', x); pg.wait_for_timeout(250)
        t = pg.evaluate(TASMA)
        R['mut'][x] = {'len': len(pg.inner_text('#rep')), 'tasma': t['sw'] > t['W'] + 1, 'nan': 'NaN' in pg.inner_text('#rep') or 'undefined' in pg.inner_text('#rep')}
    pg.click('#r-close'); pg.wait_for_timeout(300)
    # şehir seçici başka şehre götürüyor mu
    menu(True); pg.click('#tab-list'); pg.wait_for_timeout(200)
    hedef = 'izmir' if sh != 'izmir' else 'istanbul'
    pg.select_option('#sehir-sec', hedef); pg.wait_for_load_state(); pg.wait_for_timeout(1500)
    R['sehir_sec'] = pg.url.split('?')[-1]
    ctx.close()
    # CRM
    ctx = b.new_context(**VP[vp]); pg = ctx.new_page(); pg.route('**/arcgisonline.com/**', lambda r: r.abort())
    pg.on('pageerror', lambda e: R['hata'].append('crm: ' + str(e)[:200]))
    pg.goto(f'{URL}crm.html?sehir={sh}'); pg.wait_for_timeout(1500); adim('crm_bos')
    btn = pg.locator('button:has-text("Örnek verileri yükle")')
    if btn.count(): btn.first.click(); pg.wait_for_timeout(800)
    R['crm'] = {}
    for nb in ['Bugün', 'Kişiler', 'Portföy', 'Mesajlar']:
        loc = pg.locator(f'nav button:has-text("{nb}"), .nav button:has-text("{nb}"), [role=tab]:has-text("{nb}")')
        if loc.count(): loc.first.click(); pg.wait_for_timeout(400)
        R['crm'][nb] = len(pg.inner_text('#main')) if pg.locator('#main').count() else -1
        adim('crm_' + nb.lower().replace('ü', 'u').replace('ş', 's').replace('ö', 'o'))
    R['crm_geri'] = pg.get_attribute('a:has-text("Harita")', 'href') if pg.locator('a:has-text("Harita")').count() else None
    ctx.close()
    return R


if __name__ == '__main__':
    out = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for sh in SEHIR:
            for vp in VP:
                try: out[f'{sh}/{vp}'] = run(b, sh, vp)
                except Exception as e: out[f'{sh}/{vp}'] = {'COKTU': str(e)[:400]}
                r = out[f'{sh}/{vp}']
                print(sh, vp, 'ÇÖKTÜ ' + r['COKTU'][:200] if 'COKTU' in r else f"hata={len(r['hata'])} taşma={[k for k,v in r['adim'].items() if v['tasma']]}", flush=True)
        b.close()
    json.dump(out, open(H + '/sonuc.json', 'w'), ensure_ascii=False, indent=1)
