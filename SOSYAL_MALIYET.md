# Sosyal etki ve yaşam maliyeti (`python -m hekis.social`)
"Sosyalleşme" = boş stokun toplumsal kullanıma açılma payı ve faydanın dağılımı (yorum; farklıysa düzeltilir). En olası senaryo, tam ölçek (37 bin hane).

**Sosyal etki.** Yerleşen hane yılda 106 bin TL (ayda 8,8 bin) fayda alır. Kapsam: uygun kiracının %6,6'sı, tüm kiracının %2,7'si, boş stokun %8,2'si, toplam stokun %0,82'si. Gini 0,4296 → 0,4290 (−0,0007); göreli yoksulluk %19,40 → %19,24. Yani yerleşene fayda büyük (alt %10'da gelirin %50'si, alt %30-41'de %18'i), ama kapsam küçük olduğundan dağılıma etkisi ihmal edilebilir. Kura rastlantısal: aynı dilimde yerleşen ve yerleşmeyen hane arasında adalet sorunu var. Mekânsal yoğunlaşma (Esenyurt tipi stokta) ilçe verisi olmadığından ölçülmedi.

**Yaşam maliyeti.** Kiracı hane 1,38 milyon. Yerleşenler kiracı talebini %2,7 azaltır; serbest kalan birimlerin %50'si kiraya giderse (varsayım) toplam arz/talep etkisi %6,6.
| esneklik* | piyasa kirası (yalnız talep) | (talep+arz, üst sınır) | TÜFE puanı (talep) | (talep+arz) |
|---|---|---|---|---|
| 0,3 | −%9,0 | −%21,9 | −0,61 | −1,48 |
| 0,6 | −%4,5 | −%10,9 | −0,30 | −0,74 |
| 1,0 | −%2,7 | −%6,6 | −0,18 | −0,44 |
*Esneklik literatür tahmini, doğrulanmadı. Kira TÜFE ağırlığı %6,76 (TÜİK 2026 sepeti). Etki tek seferlik düzey etkisidir; serbest kalan birimler lüks/tampon segmentinde, düşük gelirli kiracı piyasasına etkisi dolaylı, o yüzden "talep+arz" üst sınır. 5. yılda (12 bin hane) etki %−1,4 kira, −0,09 TÜFE puanı (esneklik 0,6).
Maliyeti boş birim sahibi öder: havuz sınıfı birim yılda ~7,2 bin TL, lüks birim ~189 bin TL (beklenen, etkin tahsilatla). Tüm haneye bölünürse yılda 1.837 TL bedel / 769 TL sübvansiyon; net kamu fazlası 5,4 mr TL, vergi veya para basımı yok.

**Dürüst yorum.** Sistem yaşam maliyetini birkaç yüz baz puanın altında (TÜFE −0,1 ile −0,7 puan) oynatır; yerleşene çok, genele az. Fayda büyük bir gelir transferi gibi görünse de ölçeği küçük.

## Kapı revizyonu (horizon)
Kapı artık kiracı tahsilatını (≥%80) ve ölçülen hane gelirini (≥%85) de ölçer; bedel/sub oranı bu ölçümlerle yeniden hesaplanır. Sonuç: gelir şokları büyümeyi durdurur. Gelir erimesi (hane −%20, kiracı tahsilat ×0,8): önce 148 bin ölçek, 20 yıl yük 32,4 mr; şimdi 23,7 bin ölçekte durur, 20 yıl yük 6,0 mr. Hane geliri −%30: 20 yıl yük 31,9 → 5,7 mr. Şoksuz taban 11,6 bin hane (önce 11,7): gelir ölçümündeki rastlantısal gürültü bazen yanlış durdurur, bedeli küçük. Ağır kriz: %11 zarar, 20 yıl yük 1,3 mr.

## Yıl bazlı etki (`python -m hekis.social`, en olası senaryo, erozyon %25, büyüme ×2,5, kira esnekliği 0,6)
Kusursuz ölçüm yolu:
| yıl | ölçek | yerleşen | kapsam | sub mr | bedel mr | kümülatif net mr | ΔGini | Δyoksulluk (puan) | kira % | TÜFE puanı |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 3.800 | 312 | %0,06 | 0,03 | 0,08 | 0,05 | −0,00001 | −0,001 | −0,04 | −0,003 |
| 2 | 9.500 | 780 | %0,14 | 0,08 | 0,19 | 0,15 | −0,00001 | −0,003 | −0,09 | −0,006 |
| 3 | 23.750 | 1.951 | %0,35 | 0,21 | 0,45 | 0,39 | −0,00003 | −0,008 | −0,24 | −0,016 |
| 4 | 59.375 | 4.877 | %0,86 | 0,52 | 1,06 | 0,93 | −0,00009 | −0,021 | −0,59 | −0,040 |
| 5 | 148.438 | 12.193 | %2,16 | 1,29 | 2,50 | 2,14 | −0,00022 | −0,053 | −1,48 | −0,100 |
Belirsiz değerler + ölçüm hatası (200 çekim medyanı) neredeyse aynı: 5. yıl 11,8 bin hane, kümülatif net +2,0 mr TL, TÜFE −0,10 (serbest kalan birim arzı dahil üst sınır −0,24).
Okuma: 5 yılda etki yok denecek kadar küçük: Gini −0,0002, yoksulluk −0,05 puan, kira −%1,5, TÜFE −0,1 puan. Sistem ilk 5 yılda kendini finanse eder (kümülatif +2 mr TL) ama toplumsal etkisi 5. yıldan sonra tam ölçeğe (37 bin hane) ulaşıldığında belirginleşir (Gini −0,0007, TÜFE −0,18 ile −0,6 puan). TÜFE puanı tek seferlik düzey etkisidir, yıllık enflasyona eklenmez.
