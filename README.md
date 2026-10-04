# HEKIS modeli

Hedef Endeksli Kapali Ic Senet. Bos konut stokunu kullandirmanin stok-akim hesabi. Uc defter ayri tutulur: mulkiyet, oturan, senet. Esit gostermek cifte yazimdir.

Bu bir politika vaadi degil, hesap makinesidir. Repo ozel, kisisel modelleme. Dogrulanmis bir kamu maliyesi modeli degildir. Gozlem ile varsayim ayri tutulur, ayri dosyalarda: `data/VARSAYIM.md`.

**Kapsam: simdilik yalniz Istanbul.** Nufus 15,75 mn, 5,11 mn hane, 1,38 mn kiraci hane (hane buyuklugu 3,09 ADNKS; kiraci payi %27 ulusal varsayim, Istanbul'a ozgu veri bulunamadi; Istanbul geliri ulusalin 1,307 kati, TUIK TR10 434.929 / 332.882 TL). Diger sehirler 7c'de ayri, kapsam disi tutulur; ulusal hane sayisi artik kullanilmaz.

## Calistirma

Python 3 yeter. Ek paket yok, testler `unittest`.

```bash
python -m unittest discover -s tests   # 29 test
python -m hekis.checks                 # gerceklik kontrolleri
python -m hekis.analysis               # tornado, Monte Carlo, rank korelasyonu, ters stres
python -m hekis.final                  # uc sistem, luks ayrimi, luks bedel
python -m hekis.bind_cli               # stok-akim, eski A/B/C karsilastirmasi
python -m hekis.calibrate              # beklenti kurali kalibrasyonu, katilim bandi
python -m hekis.selffinance            # kendini finanse etme cebiri
```

## Veri

`data/`: istanbul_2026.json (girdiler), OKUMA.md, TEYIT.md, KFE.md (TCMB konut fiyat endeksi), KREDI.md (ipotekli pay), FAIZ_KUR.md, GELIR.md (TUIK), ANALOG.md (Vancouver, Irlanda, Fransa, Portekiz, Ispanya), VARSAYIM.md (varsayim envanteri ve etki sirasi).

## 1. Stok-akim cekirdegi

Istanbul satis m2 66.905 TL, kira m2 479 TL. Havuz sahibe kirayi oder, bakim/vergi/DASK/bos dairenin aidati havuzdan duser, oturan sosyal/dereceli kira oder, fark subvansiyondur. "Odenen" havuzun 20 yilda sahibe reel geri odedigi anapara payidir, yuksek iyidir.

A eski (donuk %31,5 enflasyon, kira aninda TUFE, gider yok), B kira 12 aylik TUFE ortalamasi ve gider dahil, C ayrica OVP yolu (%28,4/21/13,5/9). Odenen / yuk (mr TL, bugunku):

| Kosu | A | B | C |
| --- | --- | --- | --- |
| Piyasa kira, TUFE | %100 / 0 | %100 / 0 | %100 / 0 |
| Piyasa kira, sabit | %23 / 0 | %11 / 1,6 | %25 / 0,1 |
| HEKIS kirasi, TUFE | %61 / 3,2 | %36 / 3,2 | %41 / 3,5 |
| Resmi sosyal kira | %34 / 0 | %9 / 0 | %12 / 0 |
| Esenyurt, %20 alti kira | %100 / 2,0 | %100 / 2,0 | %100 / 2,2 |
| HEKIS, ulusal bos stok %27 | %46 / 2,5 | %17 / 2,5 | %21 / 2,7 |

Gider kalemleri: emlak vergisi binde 2 (ust sinir), DASK 2.022 TL, bos dairenin aidati sahibe yazilir (Istanbul ort. 3.330 TL/ay), bakim yilda degerin %1'i (varsayim). Bos dairenin sahibe maliyeti yilda yaklasik degerin %1,05'i.

## 2. Bos stoku kullandirma

Istanbul'da bos konut 225 bin (elektrik aboneligi) ile 450-750 bin (IBB) arasinda tahmin ediliyor, stok 4,5 milyon, yontem farki var. Orta semt Istanbul ortalamasi, ucuz semt Esenyurt.

| Daire basina | Fiyat | Sahibin bos maliyeti / yil | Subvansiyon / yil | 20 yil odenen |
| --- | --- | --- | --- | --- |
| Orta | 4,68 mn TL | 51 bin | 65 bin | %41 |
| Ucuz (Esenyurt) | 2,41 mn TL | 24 bin | 85 bin | %100 |

Katilim: sahip, bos tutmaktan beklenen reel getiri ile senedin reel getirisini (0) karsilastirir. Katilim = tavan x lojistik(egim x (tutma maliyeti + bedel - beklenen reel artis)). Tavan %40 ve egim 25 kalibre edilemez. Beklenti kurali (onceki reel KFE artisi) bir yil ilerisini sifir tahmininden iyi tahmin etmiyor (RMSE 21,0 vs 20,7 puan, n=9): davranis varsayimidir, tahmin degil. Tarihsel olarak negatif reel faiz donemi (2021-2023, reel faiz -%14 ile -%35) ile reel konut sicramasi (+%20, +%53, +%11) ortusuyor, kredi payi ayni donemde dusuyordu (%38'den %11'e). Kosul bugun: reel faiz +%3 ile +%6,5, reel konut -%6,5, katilim penceresi acik. Fiyat patlarken katilim sifira yakin: sistem ters donguludur.

Yurt disi benzerleri (`data/ANALOG.md`): Vancouver bos konut vergisi (%1'den %3-5'e) bos konut sayisini 2017-2022'de %54 azaltti, bunun yarisi sahibinin oturmasiyla. Fransa'da etkili olmadi, Irlanda'da kendi beyanla sinirli kaldi. Gonullu programlar cok dusuk: Portekiz kira sozlesmelerinin %0,12-0,4'u, Irlanda Repair and Leasing basvuranlarin %3,8'i. Gonullu tek basina yaklasik %4 katilim, guclu yaptirimla en fazla %50 civari.

## 3. Dereceli kira, abonelik, subvansiyon

Kararlar: oturan dereceli kira oder (min(kira, %30 x gelir), alt %40 gelir dilimi, kura ile), aidat havuzda, abonelik (elektrik, dogalgaz, su, yaklasik 1.583 TL/ay, gaz ve su alt sinir) tam subvanse. Gelir dagilimi: TUIK 2025, medyan 241 bin, ortalama 333 bin, lognormal uydurma (ust %20 payi model %48,5 TUIK %48; alt %20 %5,0 vs %6,4).

Subvansiyon bos stoku kullandirmanin maliyeti degil, sosyal kira kararinin maliyetidir: oturan kiranin tamamini odese subvansiyon sifir olur, geri odeme degismez. Havuz her durumda tam kirayi alir. Aidati oturana gecirmek geri odemeyi %75'ten %91'e cikarir ama oturanin konut yukunu %30'dan %34-40'a cikarir. Kalan %25 anapara 20. yilda odenmemis durur: senet garantisi varsa gizli yukumluluk.

## 4. Luks ust dilim

Orta tipteki bos stogun en pahali %20'si (45 bin daire, ortalama 9,5 mn TL) havuz disi, bos olsa bile, bedelden muaf degil, ayri tarife. Deger dagilimi lognormal (sigma 0,6, varsayim). Orta tipin kirasi degerle orantili olceklenir (yapisal secim): sabit politika kirasi tutulursa gelir/sub. orani 0,65 yerine 0,82 ve geri odeme %83 yerine %99 cikar.

Luks tepkisi Vancouver ankorlu (bedel %3'te bosluk %54 azalir, tavan %65), yuksek bedelde kacinma (%5 ustu her puan icin tahsilat 5 puan duser, taban %10). Toplam bedel geliri / yil 1 subvansiyon, luks bedel %1/3/5/8/12: karma sistem 0,55/0,70/0,82/0,87/0,79, Vancouver benzeri 0,74/0,84/0,92/0,96/0,90. Kacinma dahil luks gelirinin tepesi bedel %8,2 civari, yilda 5,5 mr TL: luks tek basina sistemi finanse edemez. %5 bedelde luks bos dairenin %62'si bosluktan cikar (yaklasik 28 bin daire, havuz disi).

## 5. Uc sistem (luks ayrilmis, bugunku TL)

| Sistem | Katilim | Daire | Giris | 20 yil odenen | Yil 1 sub. | 20 yil yuk | Gelir/sub. |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Gonullu tek basina | %4 | 18 bin | 51 mr | - | 1,4 mr | 29 mr | 0 |
| Karma (bedel %1, tavan %40) | %36 | 146 bin | 421 mr | %83 | 11,4 mr | 243 mr | 0,39 (luks bedelli 0,62) |
| Vancouver benzeri (bedel %3, tavan %55) | %51 | 208 bin | 602 mr | - | 16,4 mr | 347 mr | 0,62 (luks bedelli 1,09) |

## 6. Kendini finanse etme

Kosul: bedel x tahsilat >= (12 s / V) x p / (1 - p). s yerlesen daire basina aylik subvansiyon, V deger, p yerlesen oran. Katilim arttikca bedel odeyen taban erir. V 3,55 mn, s 8 bin TL/ay icin gerekli etkin bedel p %10'da %0,3, %36'da %1,5, %50'de %2,7, %60'ta %4,1 (`hekis.selffinance`).

Monte Carlo (1500 cekilis, 19 parametre, ucgen dagilim, `hekis.analysis`, Istanbul): yerlesen daire %5/%50/%95 yuzdeliginde 18/103/216 bin, 20 yil yuk 23/124/309 mr TL. Kendini finanse eden cekilis %92, ama bu olcege bagli: yerlesen daire 75 bin altinda %100, 75-150 binde %93, 150 binin ustunde %78 (medyan oran 1,38). Spearman(daire, oran) = -0,74. Baz durumda (132 bin daire) oran 1,32, sub. 7,3 mr, bedel 9,6 mr.

Dikkat: bu sonuc Istanbul gelir olcegine cok duyarli. Olcek 1,0 (ulusal dagilim) iken oran 0,93, 1,15'te 1,12, 1,307'de (baz) 1,32, 1,5'te 1,58; yani sistem Istanbul geliri ulusalin yaklasik %6 ustundeyse kendini finanse eder. Tum dagilimi ortalama orani kadar olceklemek varsayimdir: Istanbul'un alt dilimleri ulusalin %31 ustunde olmayabilir.

Sonucu en cok belirleyenler (rank korelasyonu, tornado): beklenen reel konut artisi (0,58), katilim tavani (-0,51), genel bedel, ayrilan luks pay, kira/gelir kurali, uygun kitle, etkin tahsilat. Bakim orani, aidat, stok buyuklugu (oranda), enflasyon yolu neredeyse hic.

## 7. Gerceklik kontrolleri

`hekis.checks`: 15 kontrol, 4 uyumlu, 9 uyari, 2 dogrulanamaz. Uyarilar: model bosluk orani (%3,7) bos stok tahminlerinin altinda; Esenyurt getirisi %7,3 vs Endeksa %10,04 (kaynaklar farkli); politika kirasi getirisi %3,8 vs piyasa %8,6; gelir dagilimi alt ucu fazla yoksul; ilk yil enflasyon yolu gozlenenin 2-3 puan altinda; beklenti kurali tahmin gucu yok; KFE Turkiye geneli Istanbul'dan 3 puan farkli; etkin tahsilat varsayimi iyimser; orta tip kirasi yapisal secim. Dogrulanamayan: katilim fonksiyonu, kisi basi subvansiyon.

## 7b. En olasi senaryo, guncel veriyle

`python -m hekis.reality`, `data/GUNCEL.md`. Eylul 2026 TUFE aciklanmadan once: Agustos yillik %31,51, Eylul beklentisi %30,16, yil sonu %29,66, politika faizi %37 (reel +%4,2), kira artis ust siniri (12 aylik TUFE ort.) %31,79 (kural dogrulandi), yeni kiraci %34,5, Gini 0,410.

Faiz kanali (2019-2025, n=7, R2 0,81, nedensellik degil): reel konut artisi = 0,005 - 1,35 x reel faiz. Bugunku reel faizde tahmin -%5,1, gozlenen -%6,5. Katilim penceresi reel faiz yaklasik -%0,4'un altina inmedikce acik; tampon 4,6 puan. Reel faiz 0'da yerlesen %30 duser, -%5'te dortte birine iner.

Senaryolar, Istanbul, beklenen reel artis -%3,7, Istanbul gelir olcegi 1,307 (mr TL/yil, bugunku TL): en olasi (tavan %25, bedel %1, tahsilat %30, luks bedel %5) 82 bin daire, yil 1 sub. 4,6, bedel 6,1, oran 1,33, fazla 1,5, 20 yil yuk 96. Iyimser 196 bin daire, sub. 10,8, oran 1,46, yuk 228. Kotumser 26 bin daire, yuk 30. Gelir olcegi 1,0 olsa en olasi sub. 6,5, oran 0,94, yuk 137.

Etki (en olasi, 82 bin hane, hane basina ayda 4.600 TL): Istanbul'da uygun (alt %40) 551 bin kiraci hanenin %15,0'ina ulasir. Gini 0,4296 -> 0,4290 (-0,0006), goreli yoksulluk -0,15 puan, piyasa kirasi dogrusal yaklasimla -%6 ile -%20 (ust sinir, esneklik varsayimi). Yerlesen hanenin konut yuku gelire oranla alt %10'da %62'den %30'a, alt %20'de %44'ten %30'a, alt %40'ta %27'den %25'e duser, aylik kazanc 9.900 ile 1.600 TL. Programsiz referans Esenyurt piyasa kirasi + abonelik, bu dusuk gelirli hanenin gercek karsi olgusunu abartabilir.

Duzeltme: bu bolumun onceki surumunde bos stok Istanbul'un (450 bin) ama kapsam ve etki 28 mn ulusal hane uzerindendi. Tutarsizlik giderildi.

## 7c. Istanbul ve 7 buyuksehir (simdilik kapsam disi, ayri calisma)

`python -m hekis.cities`. Sehirler: Istanbul, Ankara, Izmir, Bursa, Antalya, Konya, Adana, Kocaeli (TUIK 2025 konut satisi siralamasi; Gaziantep, Mersin, Sanliurfa bu aramada gorulmedi, siralama tam dogrulanmadi). Nufus TUIK ADNKS 2025: 39,0 mn, Turkiye'nin %45'i. Fiyat ve kira carpani Istanbul'a gore ortalama satis ve kira orani (Emlakjet-Endeksa Agustos 2026): Ankara 0,70 / 0,76, Izmir 0,89 / 0,73, Antalya 0,83 / 0,64, Bursa 0,64 / 0,53. Kocaeli, Konya, Adana icin veri yok, Bursa degerleri yer tutucu. Bos stok kisi basi Istanbul ile ayni (450 bin / 15,75 mn), hane buyuklugu 3,08, kiraci payi %27, gelir dagilimi ulusal: hepsi varsayim. Beklenen reel artis sehir bazinda KFE'ye Endeksa'nin sehir-Turkiye reel farki eklenir (Istanbul -%3,7, Ankara -%2,8, Kocaeli -%3,2, Antalya -%5,3, digerleri -%6,5).

En olasi senaryo (tavan %25, bedel %1, tahsilat %30, luks bedel %5): 8 sehirde 210 bin daire (Istanbul 82 bin, %39), yil 1 sub. 11,0 mr TL (Istanbul %59), bedel 12,6 mr, oran 1,14, 20 yil yuk 232 mr. Istanbul tek basina oran 0,94, acik 0,39 mr: diger sehirlerde kira farki kucuk (ulusal sosyal kira 10-12 bin yerel piyasa kirasina yakin), abonelik sub. baskin ve bedel tabani genis, o yuzden oran 1,18-1,80.

Etki (8 sehir nufusu, 12,7 mn hane, 3,4 mn kiraci hane): 210 bin hane (uygun alt %40 kiracinin %15'i), hane basina ayda 4.368 TL. Gini 0,4296 -> 0,4289, goreli yoksulluk -0,18 puan. Kira piyasasi etkisi dogrusal yaklasimla %-6 ile %-20, ust sinirdir: yerlesenlerin piyasa kiracisi olduklari ve esnekligin dusuk oldugu varsayilir.

## Sonuc

Model, bos stoku kullandirmanin maliyetini kira farkindan ve abonelikten ibaret gosteriyor, stoku kullandirmanin kendisi bedava. Kendini finanse etme olcek meselesi: kucuk programlar finanse eder, buyukler etmez. Yon sonuclari sagdir (ters dongululuk, olcek erozyonu, bedelin katilimi artirmada zayifligi), buyukluk sonuclari degildir (katilim, tahsilat ve beklenti kalibre edilemez).

## Sinir

Katilim orani gozlem degil, kalibre edilmemis en onemli girdidir. Tadilat, kiraci bulma gecikmesi, dairenin oturulabilir olup olmadigi, bakim orani Turkiye verisi, hane sayisi, 2024-2026 gelir artisi ve etkin tahsilat yok veya varsayimdir. Esenyurt satis fiyati gozlem degil, turetilmistir. Ulusal %27 bos stok ile %3,7 elektrik boslugu ayni sey degil. Fiziki uretim endeksi hala disaridan. Model yeni konut istahini kapatmaz, kacinma tek bir parametreyle temsil edilir, hukuki cerceve (bedelin vergi mi harc mi oldugu, anayasal sinir) hic modellenmedi.
