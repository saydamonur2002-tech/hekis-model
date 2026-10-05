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

## İki sistem, aynı şok (150 çekim, 3. yıldan itibaren, 5. yıl medyanı; `python -m hekis.horizon`)

> **GÜNCEL (kapı düzeltmesi sonrası, 150 çekim, 5. yıl medyan):** şoksuz İst. 10,8 bin hane +1,72 mr / %1 zarar; Anad. 12,9 bin +0,94 mr / %2; lüks tahsilat çöküşü %9 / %19 zarar; hane geliri −%30: %4 / %9; bedel iptali %65 / %70; kısmi iptal %36 / %47; ağır kriz %14 / %33; toplam net şoksuz +2,7 mr. Nitel sonuç aynı: Anadolu daha kırılgan, ulusal şokta ikisi birlikte düşer, ralli ikisini de çökertir.
> **DÜZELTME:** aşağıdaki iki sistem şok tablosu hatalı Monte Carlo çekimleriyle üretilmişti (bkz. PILOT.md düzeltme notu). Geçerli değerler (150 çekim, 5. yıl medyan): yok: İst. 9,5 bin hane +1,38 mr / %1 zarar; Anad. 11,6 bin +0,65 mr / %2; lüks tahsilat çöküşü: %7 / %16 zarar; hane geliri −%30: %3 / %7; bedel iptali: %65 / %70; kısmi iptal: %33 / %45; ağır kriz: %11 / %31; toplam net şoksuz +2,0 mr. Sonuç aynı: Anadolu daha kırılgan, ulusal şokta ikisi birlikte düşer, ralli ikisini de çökertir.
| şok | İst. yerleşen | İst. net mr | İst. zarar | Anad. yerleşen | Anad. net mr | Anad. zarar | toplam net |
|---|---|---|---|---|---|---|---|
| yok | 11,8 bin | 2,00 | %0 | 14,8 bin | 0,98 | %0 | 2,98 |
| fiyat rallisi (g_e +10) | 457 | 1,42 | %0 | 690 | 0,73 | %0 | 2,15 |
| lüks tahsilat çöküşü (×0,4) | 2,8 bin | 0,31 | %5 | 3,1 bin | 0,13 | %18 | 0,44 |
| hane geliri −%30 | 1,9 bin | 0,62 | %0 | 2,4 bin | 0,22 | %7 | 0,84 |
| bedel iptali (hukuki) | 1,9 bin | −0,40 | %74 | 2,4 bin | −0,25 | %83 | −0,65 |
| kısmi iptal (yalnız lüks) | 1,9 bin | 0,10 | %41 | 2,4 bin | −0,05 | %64 | 0,05 |
| kur krizi + sermaye çıkışı | 478 | 1,06 | %0 | 713 | 0,53 | %0 | 1,59 |
| ağır kriz | 453 | 0,25 | %13 | 684 | 0,09 | %33 | 0,33 |

Okuma:
- **Anadolu daha kırılgan.** Baz net yarısı (0,98 vs 2,00 mr); lüks tahsilat çöküşünde zarar %18 (İstanbul %5), kısmi iptalde %64 (%41), ağır krizde %33 (%13), gelir şokunda %7 (%0). Neden: Anadolu tarifesi düşük (%0,5 / %3), bedel/sub marjı İstanbul'dan ince (1,58 vs 1,79 erozyonlu), şok bu marjı daha çabuk eritir. Tarife yükseltmek (örn. lüks %5) Anadolu'nun şok payını İstanbul düzeyine yaklaştırır; bedeli yüksek tutmanın başka maliyetleri (kaçınma) var.
- **İki sistem ayırmak yerel şokta korur, ulusal şokta korumaz.** Gelir erimesi, yerel fiyat rallisi bir sistemi vurur diğeri ayakta kalır. Hukuki iptal, kur şoku, lüks bedel iptali ulusal: ikisi birden düşer (toplam net −0,65 mr). Kademeli kapı iki sistemde de büyümeyi durdurur, bu yüzden toplam zarar sınırlı kalır.
- Fiyat rallisinde iki sistem de yaklaşık 450-700 haneye iner: katılım sorunu aynı, ayrım koruma sağlamaz.
