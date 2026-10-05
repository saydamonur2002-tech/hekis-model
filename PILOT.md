# Mikro pilot ve kademeli genişleme

Çalıştır: `python -m hekis.pilot` (kod: `hekis/pilot.py`, 2 test `PilotTests`).
Kapsam: tek mahalle, 1.000 boş birim, İstanbul en olası senaryo. Senet, duran inşaat, Anadolu yok.

## Çıktı (model)
| kademe | yerleşen | kapsam | bedel/sub | not |
|---|---|---|---|---|
| K0 yalnız havuz | 78 | %19 | 0 | bedel yok, sub. karşılanmaz |
| K1 + genel bedel %1 | 82 | %20 | 0,72 | tek başına kendini finanse etmez |
| K2 + lüks %5 | 82 | %20 | 2,39 | finansmanı lüks bedel taşır |
| K3 + hedef primi | 95 | %23 | 2,06 | prim %4,66/yıl |

Ölçek: mahalle 82, ilçe (20 bin) 1.643, İstanbul 36.963 yerleşen; oran her yerde 2,39.

## Dürüst not
Ölçek değişmezliği modelin doğrusal olmasından gelir, kanıt değildir. Gerçek ölçek etkisini (tahsilat erozyonu, katılım doygunluğu) yalnız pilot verisi gösterir. Testler model tutarlılığını sınar; gerçeklik testi değildir.

## Kademe geçiş eşikleri (pilottan ölçülecek)
- Katılım: uygun birimin ≥%15'i (model %20 ±4 puan; 407 uygun birimle ölçülebilir).
- Fiili tahsilat ≥%25 (model: genel %30).
- Lüks bedel tahsilatı ≥%30 (model %40).
- Kiracı ödemesi/kira ≤%30 ve tahsil ≥%90.
- Eşik tutmazsa bir sonraki kademeye geçilmez; ilk bozulan parça düzeltilir.

Sıra: K0 mahalle → K1 bedel → K2 üç bölge → K3 prim → ilçe (20 bin) → İstanbul → Anadolu → senet/duran inşaat.
