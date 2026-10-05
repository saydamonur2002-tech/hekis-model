# İki ayrı HEKİS sistemi: İstanbul ve Anadolu (7 büyükşehir)
Kod: `hekis/systems.py`, `python -m hekis.social` (her şey iki sistem için ayrı). Aynı işlev, ayrı veri ve tarife. En olası senaryo, erozyon %25, büyüme ×2,5/yıl, kusursuz ölçüm; kira esnekliği 0,6.

| | İstanbul | Anadolu (7 şehir) |
|---|---|---|
| Tarife (genel / lüks) | %1 / %5 | %0,5 / %3 |
| Boş stok (tam ölçek) | 450 bin | 664 bin |
| Hane / kiracı | 5,10 mn / 1,38 mn | 7,93 mn / 2,14 mn |
| Uygun kiracı | 561 bin | 1,03 mn |
| Tam ölçekte yerleşen | 36,9 bin | 66,9 bin |
| Hane başına fayda | 106 bin TL/yıl | 47,5 bin TL/yıl |
| Kapsam (uygun kiracıya) | %6,6 | %6,5 |
| Bedel/sub (erozyonsuz) | 2,39 | 2,11 |
| Tam ölçeğe ulaşma | 7. yıl | 7. yıl |
| 7. yıl+ sub / bedel (erozyonlu) | 3,92 / 7,03 mr | 3,18 / 5,02 mr |
| ΔGini (tam ölçek) | −0,00066 | −0,00036 |
| Δyoksulluk | −0,16 puan | −0,085 puan |
| Kira (esneklik 0,6) | −%4,5 | −%5,2 |
| Yerel TÜFE puanı | −0,30 | −0,35 |
| Ulusal TÜFE puanı (hane payı %18 / %28) | −0,055 | −0,10 |

İki sistem toplamı (7. yıl ve sonrası): 104 bin hane, sub 7,1 mr, bedel 12,0 mr, kümülatif net 10. yılda +26,6 mr TL, ulusal TÜFE −0,16 puan (esneklik 0,6; tek seferlik düzey etkisi).

**Düzeltme (önceki not):** SOSYAL_MALIYET.md'deki "TÜFE −0,30" yalnız İstanbul yerel TÜFE'si; ulusal etki hane payıyla (%18) ölçeklenir: −0,055. Hane payı, kiraların İstanbul'da daha yüksek olması nedeniyle gerçek harcama payının altında kalır; ulusal etki biraz daha büyük olabilir. Ulusal hane sayısı (86,09 mn nüfus / 3,09) yaklaşık, doğrulanmadı.

**Okuma.** Anadolu'da daha çok hane yerleşir (67 bin) ama hane başına fayda yarıdan az (kira ve değer düşük), bu yüzden Gini ve yoksulluk etkisi İstanbul'un yarısı. Finansman iki sistemde de kendini taşır (oran 1,8-2,4), Anadolu'da bedel/sub biraz düşük. Bu yapı dayanıklı: bir sistemde hukuki iptal ya da tahsilat çöküşü olursa diğeri ayakta kalır, çünkü kademe kapıları ayrı çalışır.
**Sınırlar:** Anadolu'da Kocaeli, Konya, Adana fiyat/kira verisi yer tutucu; gelir dağılımı Gini hesabı için ulusal lognormal; boş stok kişi başı İstanbul'la aynı varsayım; pilot toplam 3.800 birim şehirlere paylaştırıldı (tek şehir pilotu daha gerçekçi). Anadolu için şok testleri henüz koşulmadı.
