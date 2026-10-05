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

## Dış çapa: 2024 tasarruf finansman (benzetme yok)
`python -m hekis.anchor`. Sistem yalnız ölçek ve talep için dış kontrol; HEKİS tasarımı o sisteme benzemez (o: üye birikimi, sıra/çekiliş; HEKİS: boş stoğu havuza alan kira sistemi). Veri haber özetlerinden, doğrulanmamış; konut/taşıt ayrımı yok; baz yıl 2024, model 2026.
- 2024: sözleşme 498 mr TL, müşteri 630 bin, aktif 92 mr TL → müşteri başı ≈790 bin TL. HEKİS havuz birimi 2,41 mn TL; sözleşme birim değerin bir kısmı.
- HEKİS 36,9 bin hane = sistemin müşterisinin %5,9'u.
- Sistem aktifi mevduatın %0,29'u, senet %0,28'i (senet/aktif 0,97). En hızlı büyüyen 2024 kanalı bile mevduatın ~%0,3'ünü çekti: dolarizasyon kapasitesi ≈0 sonucuyla uyumlu.
- Sınır: müşteri tasarruf eden orta gelir, HEKİS'in uygun kiracısı (düz memur maaşı altı) başka nüfus. Talep kanıtı değil. Pilotun "kapsam" sütunu havuz stokunun katılımı; anchor'daki kapsam uygun kiracıya oranı (%6,6), ikisi aynı şey değil.
