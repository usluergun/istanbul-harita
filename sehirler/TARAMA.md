# Yeni şehir: Mac'te yapılacaklar

Bu bulut ortamı emlakjet ve OpenStreetMap'e erişemiyor. Aşağıdaki iki adım internet erişimi olan bilgisayarda (Mac) çalışır.
Her adımdan sonra değişiklikleri `main` dalına gönderin; harita yeni veriyi kendiliğinden kullanır.

## 1. Mahalle sınırları — İzmir, Aydın, Gaziantep için TAMAM

Sınırlar açık veri setinden alındı (`tools/sinir_acik_veri.py`, kaynak: github.com/ttezer/turkiye-harita-verisi). Aşağıdaki OpenStreetMap komutu yalnızca semt adları ve ana yol katmanı da istenirse veya yeni bir şehir bu veri setinde yoksa gerekir.

### OpenStreetMap ile (isteğe bağlı, her şehir için 5–15 dk)

```bash
cd ~/"Emlak Haritası_Web Tabanlı"   # bu deponun Mac'teki kopyası
git checkout main && git pull
python3 tools/sinir_indir.py izmir
python3 tools/sinir_indir.py aydin
python3 tools/sinir_indir.py mugla
python3 tools/sinir_indir.py hatay
python3 tools/sinir_indir.py gaziantep
```

Her komut `sehirler/<şehir>/geo.json` yazar (ilçe ve mahalle sınırları, semt adları, ana yollar). Ek kurulum gerekmez.

## 2. İlan taraması

Mevcut tarayıcı (`emlakjet/emlakjet_ilce.py`) aşağıdaki sayfalarla çalıştırılır. İstanbul'dan farklı olarak:

- **Fiyat sınırı yok:** tüm fiyatlar taranır. Haritadaki fiyat süzgeci şehir ayarından (`config.json → fiyat`) gelir.
- **Villa ve müstakil ev de tutulur** (özellikle kıyı ilçeleri). Adres açılmazsa emlakjet'te ilçeyi seçip doğru adresi buraya yazın.

Çıktı tek dosyada birleştirilir: `sehirler/<şehir>/ilan.json` (İstanbul'daki alanlarla aynı). Sonra mahalle eşleştirmesi:

```bash
python3 tools/mahalle_esle.py izmir
```

Ardından `sehirler/index.json` içinde şehrin `durum` değeri `hazir` yapılır ve `config.json → tarama` doldurulur
(tarih, ilçe bazında farklı günler, metin). Bu son adımı Claude da yapabilir.

## Taranacak sayfalar

İstanbul'da kullanılan `satilik-konut/<il>-<ilçe>` adres yapısı. Konut kategorisi daire, villa ve müstakil evi birlikte içerir; tarayıcı ilan tipini (`tip` alanı) kaydetmeli ki haritada ayrı süzülebilsin.

### İzmir

- **Çiğli** (İzmir merkez): https://www.emlakjet.com/satilik-konut/izmir-cigli
- **Bayraklı** (İzmir merkez): https://www.emlakjet.com/satilik-konut/izmir-bayrakli
- **Konak** (İzmir merkez): https://www.emlakjet.com/satilik-konut/izmir-konak
- **Karşıyaka** (İzmir merkez): https://www.emlakjet.com/satilik-konut/izmir-karsiyaka
- **Balçova** (İzmir merkez): https://www.emlakjet.com/satilik-konut/izmir-balcova
- **Narlıdere** (İzmir merkez): https://www.emlakjet.com/satilik-konut/izmir-narlidere
- **Güzelbahçe** (İzmir kıyı): https://www.emlakjet.com/satilik-konut/izmir-guzelbahce
- **Urla** (İzmir kıyı): https://www.emlakjet.com/satilik-konut/izmir-urla
- **Çeşme** (İzmir kıyı): https://www.emlakjet.com/satilik-konut/izmir-cesme
- **Karaburun** (İzmir kıyı): https://www.emlakjet.com/satilik-konut/izmir-karaburun
- **Seferihisar** (İzmir kıyı): https://www.emlakjet.com/satilik-konut/izmir-seferihisar
- **Menderes** (İzmir kıyı): https://www.emlakjet.com/satilik-konut/izmir-menderes
- **Selçuk** (İzmir kıyı): https://www.emlakjet.com/satilik-konut/izmir-selcuk

### Aydın

- **Kuşadası**: https://www.emlakjet.com/satilik-konut/aydin-kusadasi
- **Söke**: https://www.emlakjet.com/satilik-konut/aydin-soke
- **Didim**: https://www.emlakjet.com/satilik-konut/aydin-didim

### Muğla

- **Milas**: https://www.emlakjet.com/satilik-konut/mugla-milas
- **Bodrum**: https://www.emlakjet.com/satilik-konut/mugla-bodrum
- **Datça**: https://www.emlakjet.com/satilik-konut/mugla-datca
- **Marmaris**: https://www.emlakjet.com/satilik-konut/mugla-marmaris
- **Menteşe**: https://www.emlakjet.com/satilik-konut/mugla-mentese
- **Ula**: https://www.emlakjet.com/satilik-konut/mugla-ula
- **Köyceğiz**: https://www.emlakjet.com/satilik-konut/mugla-koycegiz
- **Ortaca**: https://www.emlakjet.com/satilik-konut/mugla-ortaca
- **Dalaman**: https://www.emlakjet.com/satilik-konut/mugla-dalaman
- **Fethiye**: https://www.emlakjet.com/satilik-konut/mugla-fethiye
- **Seydikemer**: https://www.emlakjet.com/satilik-konut/mugla-seydikemer

### Gaziantep

- **Şahinbey** (Gaziantep merkez): https://www.emlakjet.com/satilik-konut/gaziantep-sahinbey
- **Şehitkamil** (Gaziantep merkez): https://www.emlakjet.com/satilik-konut/gaziantep-sehitkamil

### Hatay

- **Erzin** (Hatay kıyı): https://www.emlakjet.com/satilik-konut/hatay-erzin
- **Dörtyol** (Hatay kıyı): https://www.emlakjet.com/satilik-konut/hatay-dortyol
- **Payas** (Hatay kıyı): https://www.emlakjet.com/satilik-konut/hatay-payas
- **İskenderun** (Hatay kıyı): https://www.emlakjet.com/satilik-konut/hatay-iskenderun
- **Arsuz** (Hatay kıyı): https://www.emlakjet.com/satilik-konut/hatay-arsuz
- **Samandağ** (Hatay kıyı): https://www.emlakjet.com/satilik-konut/hatay-samandag
- **Defne** (Antakya): https://www.emlakjet.com/satilik-konut/hatay-defne
- **Antakya** (Antakya): https://www.emlakjet.com/satilik-konut/hatay-antakya
- **Yayladağı** (Suriye sınırı): https://www.emlakjet.com/satilik-konut/hatay-yayladagi
- **Altınözü** (Suriye sınırı): https://www.emlakjet.com/satilik-konut/hatay-altinozu
- **Reyhanlı** (Suriye sınırı): https://www.emlakjet.com/satilik-konut/hatay-reyhanli
- **Kumlu** (Suriye sınırı): https://www.emlakjet.com/satilik-konut/hatay-kumlu
- **Kırıkhan** (İç Hatay): https://www.emlakjet.com/satilik-konut/hatay-kirikhan
- **Belen** (İç Hatay): https://www.emlakjet.com/satilik-konut/hatay-belen
- **Hassa** (İç Hatay): https://www.emlakjet.com/satilik-konut/hatay-hassa

Hatay'ın mahalle sınırları açık veri setinde yok: `python3 tools/sinir_indir.py hatay` (OpenStreetMap) ile eklenir.
