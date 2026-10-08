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

## Uretim devresi kapsami (oneri, veri `data/SEKTOR.md`)
Devre (prim havuzunun 6/7'si) yalniz kar eden ve ithal girdisi dusuk imalata verilmek istenir. Veri iki olcutun carpistigini gosteriyor: kar eden sektorler (kimya, makine, otomotiv yan sanayi, fabrikasyon metal) yuksek ithal girdili; dusuk ithal girdili tekstil, giyim, mobilya kar etmiyor (uretim -%4,5 ve -%22,1, kapasite %70-74, mobilyada 2025 kari eridi). Tarim girdi enflasyonu %32-36 ve devlet destegiyle yasiyor. Gida (dusuk-orta ithal girdi, olumlu yatirim durusu) ve ahsap urunleri (kapasite %83,7) iki olcutu birlikte saglayana en yakin.
Oneri: devre kapsami sektor listesi degil, programin kendi talebine bagli: HEKIS dairelerinin donatimi (mobilya, ev tekstili, beyaz esya) ve duran insaat tamamlama girdileri (yapi malzemesi). Olculur: teslim edilen set sayisi, fiziki endeks yerine denetlenebilir.
Olcek: devre en olasi senaryoda yilda 0,76 mr TL (endeks 1,25) ile 7,65 mr TL (tavan) arasi. Senet anaparasi (89,2 mr TL) imalat aktiflerinin yalniz %0,35'i. Donatim talebi 43 bin daire x 100-300 bin TL = 4,3-12,9 mr TL (tek seferlik, gercek donatim maliyeti verisi yok), mobilya uretiminin %0,7-2,2'si. Devre bir sektoru kurtarmaz, kucuk bir talep capasidir. Geri odeme akisi (bos stok icin yilda ~5,6 mr TL net kira) sahiplere nakit doner; yatirim yeri belirsiz.

## Iki hat (yorum; kullanici bilgisayarindaki sektor dosyalari gorulmedi)
Hat A, taban ve istihdam: mevcut ayakta sektorler (gida, agac urunleri) ve programin kendi talebi (donatim, yapi malzemesi). Arac: anaparasi TUFE'ye endeksli temel senet, odul yok. Olcut: istihdam, teslim edilen set sayisi. Devlete risk: yalniz garanti.
Hat B, donusum ve hedef: bugun kar etmeyen sektorler (tekstil, giyim, mobilya). Arac: hedef primi, yalniz hedef tutarsa. Risk bu hatta: olcum ve regulator.
Cikarim: iki hat risk dagilimini dogru yere koyar (A dusuk, B yuksek). Ama B hattinin sorunu buyuk olcude makro (guclu TL, pozitif reel faiz), mikro hedef bunu cozmez. Iki alt sistem zit makro kosul ister: HEKIS katilim penceresi reel faiz yuksekken acik (esik yaklasik -%0,4), tekstil ve mobilya reel faiz ve kur gevsediginde iyilesir. Birlikte calisabilecekleri aralik dar: reel faizin sifira yakin ve hafif pozitif oldugu bolge. Olcek: iki hat toplami yilda 0,76-7,65 mr TL, imalat aktiflerinin yaklasik %0,03'u.
