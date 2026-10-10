# Yeni şehir: Mac'te yapılacaklar

Bu bulut ortamı emlakjet ve OpenStreetMap'e erişemiyor. Aşağıdaki iki adım internet erişimi olan bilgisayarda (Mac) çalışır.
Her adımdan sonra değişiklikleri `cok-sehir` dalına gönderin; harita yeni veriyi kendiliğinden kullanır.

## 1. Mahalle sınırları — İzmir, Aydın, Gaziantep için TAMAM

Sınırlar açık veri setinden alındı (`tools/sinir_acik_veri.py`, kaynak: github.com/ttezer/turkiye-harita-verisi). Aşağıdaki OpenStreetMap komutu yalnızca semt adları ve ana yol katmanı da istenirse veya yeni bir şehir bu veri setinde yoksa gerekir.

### OpenStreetMap ile (isteğe bağlı, her şehir için 5–15 dk)

```bash
cd ~/Istanbul_Emlak_Harita   # bu deponun Mac'teki kopyası
git checkout cok-sehir && git pull
python3 tools/sinir_indir.py izmir
python3 tools/sinir_indir.py aydin
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

### Aydın ve Muğla kıyısı

- **Kuşadası** (Aydın kıyı): https://www.emlakjet.com/satilik-konut/aydin-kusadasi
- **Söke** (Aydın kıyı): https://www.emlakjet.com/satilik-konut/aydin-soke
- **Didim** (Aydın kıyı): https://www.emlakjet.com/satilik-konut/aydin-didim
- **Milas** (Muğla kıyı): https://www.emlakjet.com/satilik-konut/mugla-milas
- **Bodrum** (Muğla kıyı): https://www.emlakjet.com/satilik-konut/mugla-bodrum

### Gaziantep

- **Şahinbey** (Gaziantep merkez): https://www.emlakjet.com/satilik-konut/gaziantep-sahinbey
- **Şehitkamil** (Gaziantep merkez): https://www.emlakjet.com/satilik-konut/gaziantep-sehitkamil
