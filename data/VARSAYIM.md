# Varsayim envanteri, 2026-10-05

Siniflar: TEYITLI (kaynakta gorulen), TURETILMIS (veriden hesap, yontem varsayimli), VARSAYIM (gozlem yok), KALIBRE EDILEMEZ (veri yoksa yapilamaz).
"Etki": Monte Carlo rank korelasyonu |rho| ile gelir/sub. orani uzerindeki etki (hekis.analysis). Yuksek = sonucu cok belirler.

| Girdi | Deger | Sinif | Etki |
| --- | --- | --- | --- |
| Istanbul satis m2, kira m2 | 66.905 / 479 TL | TEYITLI (Emlakjet-Endeksa Agustos 2026) | orta |
| TUFE Agustos 2026 yillik | %31,51 | TEYITLI | dusuk |
| Ileri enflasyon yolu | OVP %28,4/21/13,5/9 sonra %9 | TEYITLI hedef, 2029 sonrasi VARSAYIM | dusuk (0,05) |
| Esenyurt m2, kira | 34.475 TL, 20/17/14,25 bin | TEYITLI ama farkli kaynaklar, getiri %7,3 vs Endeksa %10,04 | dusuk |
| Aidat | Istanbul ort. 3.330, Esenyurt 1.450 | Istanbul TEYITLI aktarim, Esenyurt VARSAYIM | cok dusuk (0,01) |
| Emlak vergisi, DASK | binde 2, 2.022 TL | TEYITLI (ust sinir) | dusuk |
| Bakim orani | %1 | VARSAYIM (yabanci rehber %1-3) | cok dusuk (0,05) |
| Abonelik (elektrik, gaz, su) | 1.583 TL/ay | elektrik TEYITLI, gaz ve su TURETILMIS/eski | dusuk (0,03) |
| Gelir dagilimi | lognormal, medyan 241 bin, ort. 333 bin | TURETILMIS (ust/alt %20 payi sinandi: %48,5/%5,0) | orta |
| Hane katsayisi, gelir artisi | 2,0; 1,65 | VARSAYIM | orta (uplift 0,12) |
| Hane gelir olcegi | baz 1,0; sendika 0,63; Istanbul TR10 1,31 | Sendika medyani TEYITLI (aktarim), hane medyanina cevirme VARSAYIM (1,5 calisan); TR10 ortalama TEYITLI, tum dagilima uygulama VARSAYIM | yuksek: oran 0,61 / 0,94 / 1,33 |
| Istanbul hane sayisi | 15,75 mn / 3,09 = 5,10 mn | TEYITLI (ADNKS 2025) | orta |
| Istanbul kiraci hane payi | %27 | VARSAYIM (ulusal, Istanbul verisi bulunamadi) | orta |
| Sosyal kira | 12/10 bin | TEYITLI (Bakan aciklamasi) | orta |
| Kira/gelir kurali, uygun kitle | %30, alt %40 | VARSAYIM (politika karari) | yuksek (0,18/0,19) |
| Bos stok (Istanbul) | 225 bin - 750 bin | TEYITLI ama yontem farkli, tek sayi yok | stok buyuklugu daire sayisini belirler, oran degil |
| Beklenen reel konut artisi | son gozlem, KFE | TURETILMIS, tahmin gucu yok | EN YUKSEK (0,58) |
| Katilim tavani, egim | %40, 25 | KALIBRE EDILEMEZ | cok yuksek (0,51) |
| Etkin tahsilat | %60 | VARSAYIM (Irlanda ~%6 isaretlenen) | orta (0,21) |
| Luks ayrilan pay, dagilim genisligi | %20, sigma 0,6 | VARSAYIM | orta (cut 0,07) |
| Luks tepki | Vancouver ankorlu, tavan %65 | KALIBRE EDILEMEZ (tek ankor) | dusuk-orta |
| Luks kacinma | %5 ustu her puan icin 5 puan tahsilat kaybi | VARSAYIM | dusuk |
| Orta tip kirasi | degerle orantili | YAPISAL SECIM: sabitse oran 0,65, degilse 0,82 | yuksek |
| Havuz tahsilati, bosluk | %98, %3,7 | VARSAYIM / TEYITLI (bosluk Avrupa yakasi) | dusuk |

En yuksek etkili uc girdi: beklenen reel konut artisi, katilim tavani, kira/gelir kurali ve uygun kitle. Hicbiri veriyle kalibre edilmis degil.
