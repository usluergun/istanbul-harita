"""Telefon ekran görüntülerini adım adım, 6 şehir yan yana birleştirir: karsi/<vp>_<adim>.jpg"""
import glob, os, re, sys
from PIL import Image, ImageDraw
H = os.path.dirname(os.path.abspath(__file__)); O = H + '/karsi'; os.makedirs(O, exist_ok=True)
S = ['istanbul', 'izmir', 'aydin', 'mugla', 'gaziantep', 'hatay']
vp = sys.argv[1] if len(sys.argv) > 1 else 'tel'
adimlar = {}
for f in glob.glob(f'{H}/ekran/*_{vp}_*.png'):
    m = re.match(rf'(\w+)_{vp}_(\d+)_(.+)\.png', os.path.basename(f))
    if m: adimlar.setdefault(m.group(3), {})[m.group(1)] = f
w = 300
for ad, d in adimlar.items():
    ims = [Image.open(d[s]).convert('RGB') if s in d else None for s in S]
    h = max(int(i.height * w / i.width) for i in ims if i)
    out = Image.new('RGB', (w * 6 + 50, h + 24), 'white'); dr = ImageDraw.Draw(out)
    for k, (s, i) in enumerate(zip(S, ims)):
        dr.text((k * (w + 10) + 4, 4), s, fill='black')
        if i: out.paste(i.resize((w, int(i.height * w / i.width))), (k * (w + 10), 22))
    out.save(f'{O}/{vp}_{ad}.jpg', quality=78)
print(len(adimlar), 'adım')
