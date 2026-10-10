# Şehir verileri

Her şehir kendi klasöründe durur; harita adresteki `?sehir=` değerine göre klasörü okur (varsayılan: istanbul).

```
sehirler/
  index.json            şehir listesi ve durumları (hazir / hazirlaniyor)
  <şehir>/config.json   ad, başlık, harita merkezi, ilçeler (ad, -de/-da eki, merkez, grup, emlakjet adresi),
                        fiyat adımları, tarama tarihleri, kaynak notu
  <şehir>/resmi.json    TÜİK satış ve nüfus, TCMB fiyat endeksi (şehirden bağımsız anahtarlar: tuik.il, tcmb.il_*)
  <şehir>/geo.json      sınırlar, adlar, yollar      ← tools/sinir_indir.py (Mac)
  <şehir>/ilan.json     ilanlar                      ← emlakjet taraması + tools/mahalle_esle.py (Mac)
  _ham/                 resmî verilerin ham derlemesi ve kaynak bağlantıları
```

- `geo.json` ve `ilan.json` yoksa harita o şehirde **hazırlık görünümü** açar: ilçeler, resmî veriler ve sıradaki adımlar.
- İkisi gelince ısı haritası, Mahalleler, Değer tahmini ve Müteahhit raporu aynı kodla çalışır.

## Yeni şehir eklemek

1. `sehirler/<şehir>/config.json` yaz (bir öncekini kopyala, ilçeleri değiştir).
2. `index.json`'a ekle (`durum: hazirlaniyor`).
3. `resmi.json`: TÜİK ve TCMB son ay verileri.
4. Mac'te `TARAMA.md` adımları.

Ayrıntılar: [TARAMA.md](TARAMA.md)
