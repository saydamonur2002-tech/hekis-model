# Senet: hedef odakli ic senet (guncel tasarim, 2026-10-05)

Para piyasasi fonu degil, sosyal tahvil degil, doviz borcu degil, KKM degil. Tasarim notu, yururluk metni degil. Rakamlar modelden (`hekis/zones.py`), kod `hekis/senet.py`.

## Tanim
Anapara TUFE ile yurur (enflasyona karsi korunur). Reel kupon sifir. Hedef tutarsa ek parasal odul (hedef primi), tutmazsa sifir. Yalniz yurt ici: dis aliciya kapali, doviz, altin, fon, arsa itfasi yok, itfa yalniz sistem icinde. Rant degil, gelir koruma araci. KKM'den farki: KKM kur riskini acik uclu ustleniyordu, burada koruma yalniz enflasyona, ust sinir havuzun net kirasi ve prim formulu.

## Mekanizma
Hedef primi yalniz fiziki endeks 1'i gecince dogar. Oran = min(0,10, 0,04 x (endeks - 1)), reel anaparaya gore. Prim havuzunun 1/7'si senet sahibinde, 6/7'si uretim devresinde kalir. 1/7 gozlem degil, tasarim payi. Fiziki uretim endeksi modelde sabit 1,00, dis veridir.

## Ihrac buyuklugu (Istanbul, baz)
Bos stoktan 89,2 mr TL (yaklasik 1,83 mr USD), duran insaattan ek 3,2 mr TL. Bos stokun toplam degeri yaklasik 1,6 trilyon TL: ihrac onun yaklasik %5,6'si.

## Sahibin reel getirisi: hedef primi mevduatla yaris edemez
| Endeks | Prim orani | Prim havuzu (mr TL/yil) | Sahibin 1/7'si | Sahip reel getirisi |
| --- | --- | --- | --- | --- |
| 1,10 | %0,40 | 0,36 | 0,05 | %0,06 |
| 1,25 | %1,00 | 0,89 | 0,13 | %0,14 |
| 1,50 | %2,00 | 1,78 | 0,25 | %0,29 |
| 2,00 | %4,00 | 3,57 | 0,51 | %0,57 |
| 3,50 (tavan) | %10,00 | 8,92 | 1,27 | %1,43 |
Mevduat reel faizi bugun yaklasik +%4,2, bos tutma maliyeti degerin %1,05'i. Senedin reel getirisi tavanda bile %1,43. Yani senet gonullu katilimda mevduatla rekabet edemez; katilim bedel ve yaptirim baskisina dayanir, senedin cazibesine degil. Prim tavani (%10 = 8,9 mr) yillik subvansiyonun (4,6 mr) yaklasik iki kati, formul ust uctayken devlete maliyeti subvansiyonu asar.

## Riskler
1. Rekabet: senet reel getirisi sifir (tavanda %1,4), mevduat +%4,2. Reel faiz negatife donerse mevduat da cazip degil, sermaye konuta, dovize ve altina gider.
2. Olcum: fiziki endeks yok. Regulator hem hedefi koyar hem hakem. Hedef tutmadi/tuttu karari siyasi baskiya acik (Goodhart).
3. Odenmeyen anapara: 20 yilda geri odeme havuz kirasina bagli (kira m=0,8 altina inerse %85, 0,6'da %67). Kalan anapara icin devlet garantisi gizli yukumluluk.
4. Likidite: ikincil piyasa yok, sahip 20 yil kilitli. Modelde likidite maliyeti ayri satir degil.
5. Banka kanali (oneri): mevduat faizine esitleme ve kamu bankasi destegiyle ozel bankalarin etkisini azaltmak finansal baski araci, kamu bankalarina yari mali yuk. Test edilmedi.
6. Servet cikisi: konut bos stok olarak kapanirsa servet baska bir depoya gider. Reel faiz pozitif kaldikca mevduat, negatifse doviz ve altin. Bu, hedeflenen doviz girdisi sinirlamasinin tersi bir talep yaratabilir.
7. Dis alici kapali: doviz girdisi azalir ama alici tabani da daralir. Devletin dis borc yapisi hakkindaki iddia bu oturumda dogrulanmadi.
