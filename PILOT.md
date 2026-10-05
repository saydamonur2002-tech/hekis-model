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

## Kademe geçiş eşikleri (revize: modelden türetilmiş)
Eski eşikler (%15 / %25 / %30 / %30 / %90) dayanaksızdı; model çıktısının biraz altı olarak seçilmişti. Yeni kural: bedel/sub oranını ≥1,25'e (tespit, tahsil, idari maliyet modelde yok; %25 pay, karar) taşıyan en küçük değer; ölçüm hatası (%95 GA) üstüne eklenir. Kod: `pilot.gates()`.

| Ölçüm | Eski | Yeni | Dayanak |
|---|---|---|---|
| Katılım (uygun birim) | ≥%15 | %15-38 | alt: amaç (karar); üst: %38 üstünde sub. bedeli aşar |
| Genel bedel tahsilatı | ≥%25 | ≥%20 | lüks tahsilatla birlikte okunur (aşağı) |
| Lüks bedel tahsilatı | ≥%30 | ≥%18 (genel %20 ise) | sınır eğrisi: genel %30→lüks %13, %20→%18, %10→%24 |
| Kiracı ödeme/kira | ≤%30 | ≤%30 (tasarım) | değişmedi |
| Kiracı tahsilat | ≥%90 | finansal taban %38; operasyonel ≥%80 (karar) | %90 finansal değil, tahmindi |

Bulgular:
- Genel ve lüks tahsilat birbirinin yerine geçiyor; tek tek eşik yerine eğri. Lüksün yüksek olması genelin düşüklüğünü kapatır. Genel bedel tek başına (lüks yok) ancak %42 tahsilatla yeter: gerçekçi değil.
- Modelde %10 tahsilat tabanı vardı (AVOID_FLOOR): tahsilat 0'da bile oran >1 görünüyordu, yani kendi kendini finanse etme sonucu varsayımla korunuyordu. Eşikler tabansız hesaplandı. Ana modeldeki taban hâlâ duruyor; sonuçları (oran 2,39) hafifçe iyimser olabilir.
- Mikro pilot lüks tahsilatını ölçemez: 1.000 birimde ~77 lüks vergilendirilen birim var, hata ±9 puan. ±5 puan için ~4.000 birim gerekir. Katılım (407 uygun birim, ±3,9) ölçülür.

## Dış çapa: 2024 tasarruf finansman (benzetme yok)
`python -m hekis.anchor`. Sistem yalnız ölçek ve talep için dış kontrol; HEKİS tasarımı o sisteme benzemez (o: üye birikimi, sıra/çekiliş; HEKİS: boş stoğu havuza alan kira sistemi). Veri haber özetlerinden, doğrulanmamış; konut/taşıt ayrımı yok; baz yıl 2024, model 2026.
- 2024: sözleşme 498 mr TL, müşteri 630 bin, aktif 92 mr TL → müşteri başı ≈790 bin TL. HEKİS havuz birimi 2,41 mn TL; sözleşme birim değerin bir kısmı.
- HEKİS 36,9 bin hane = sistemin müşterisinin %5,9'u.
- Sistem aktifi mevduatın %0,29'u, senet %0,28'i (senet/aktif 0,97). En hızlı büyüyen 2024 kanalı bile mevduatın ~%0,3'ünü çekti: dolarizasyon kapasitesi ≈0 sonucuyla uyumlu.
- Sınır: müşteri tasarruf eden orta gelir, HEKİS'in uygun kiracısı (düz memur maaşı altı) başka nüfus. Talep kanıtı değil. Pilotun "kapsam" sütunu havuz stokunun katılımı; anchor'daki kapsam uygun kiracıya oranı (%6,6), ikisi aynı şey değil.
