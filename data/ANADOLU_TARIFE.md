# Anadolu buyuksehirleri tarifesi

Taslak, yururluk metni degil. Ankara, Izmir, Bursa, Antalya, Konya, Adana, Kocaeli. Veri `data/ANADOLU.md`, hesap `python -m hekis.anadolu`. Istanbul tarifesi `data/KANUN_TASLAGI.md`.

## Tarife

| Kalem | Anadolu | Istanbul |
| --- | --- | --- |
| Genel bedel (HEKIS bandi ve tampon, bos konut, yillik beyan degeri) | %0,5 | %1 |
| Luks bedel (deger siralamasinin ust %20'si) | %3 | %5 |
| Birincil konut | muaf | muaf |
| HEKIS gelir esigi | hane geliri duz memur (13/1) maasinin altinda | ayni, ulusal sabit |
| Havuz teklifi (kira) alt siniri | piyasa kirasinin %80'i | ayni |

Esikler sehre ozgudur, oran ayni: luks esigi her sehrin deger siralamasinin ust %20'sidir (gostergesel TL, ort. deger x 1,384, sigma 0,6 varsayim): Ankara ~7,10 mn, Izmir ~9,10 mn, Bursa ~6,56 mn, Antalya ~8,49 mn, Konya ~6,43 mn, Adana ~6,28 mn, Kocaeli ~7,22 mn TL. HEKIS bandinin payi gelir dagilimina gore degisir, cunku duz memur maasi ulusal sabit: Ankara %39, Izmir %44, Bursa, Antalya, Konya, Adana, Kocaeli %54 (son bes sehirde gelir yer tutucu).

## Neden Istanbul'dan dusuk

Modelde Istanbul tarifesi (genel %1, luks %5) Anadolu'da fazlasiyla yeterli: yetti sehirde gelir/sub. orani 2,8-3,3. Sebep, Anadolu'da subvansiyon kucuk: ulusal sosyal kira 10-12 bin TL yerel piyasa kirasina yakin (Bursa Esenyurt tipi kira ~9 bin TL), kira farki kucuk, abonelik baskin (birim sub. ortalama 47.500 TL/yil, abonelik payi %39; Bursa %49, Adana %53, Ankara %31). Daha dusuk tarife de kendini finanse eder.

| Tarife (genel, luks) | HEKIS daire | Yil 1 sub. | Bedel | Oran | Bosluktan cikan | 20 yil yuk |
| --- | --- | --- | --- | --- | --- | --- |
| %0,25 / %1 | 66 bin | 3,14 mr | 3,46 mr | 1,10 | 57 bin | 66 mr |
| %0,5 / %2 | 67 bin | 3,18 mr | 5,65 mr | 1,78 | 95 bin | 67 mr |
| **%0,5 / %3** | **67 bin** | **3,18 mr** | **6,69 mr** | **2,11** | **107 bin** | **67 mr** |
| %0,75 / %3 | 68 bin | 3,21 mr | 7,38 mr | 2,30 | 121 bin | 68 mr |
| %1 / %5 (Istanbul) | 68 bin | 3,24 mr | 10,00 mr | 3,08 | 143 bin | 68 mr |

Secim: %0,5 / %3. Finansman rahat (2,1 kat), HEKIS ayni (67 bin), bosluktan cikan 107 bin: Istanbul tarifesinin 143 binine gore dusuk ama yeterli. Daha dusuk bedel hukuki ve siyasi riski, ozellikle luks bedelde %5'in orantililik itirazini azaltir. HEKIS daire sayisi tarifeden neredeyse bagimsiz (66-68 bin): kullanilabilir stok ve katilim tavani belirliyor, bedel degil. Sehir baz oran: Ankara 2,2, Izmir 2,2, Bursa 2,0, Antalya 2,0, Konya 1,9, Adana 2,1, Kocaeli 2,2.

## Kapsam

Tarifenin yedi sehirde sagladigi HEKIS yerlesimi yaklasik 67 bin daire (Ankara 12,4 bin, Izmir 12,5 bin, Bursa 11,0 bin, Antalya 9,0 bin, Konya 7,9 bin, Adana 7,7 bin, Kocaeli 6,3 bin). Uygun kiracinin yuzde 0,9 ile 2,3'une ulasir. Bu Istanbul'un (yuzde 6,6) cok altinda: bos stok Istanbul'la ayni kisi basi varsayimiyla hesaplandi ve katilim tavani %25.

## Sinirlar (okumadan once)

- Gelir: yalniz Ankara (TR51) ve Izmir (TR31) icin IBBS-2 verisi var. Bursa, Antalya, Konya, Adana, Kocaeli gelir orani yer tutucu (ulusal = Istanbul'un 0,77'si). Bu sehirlerde HEKIS bandi %54 cikiyor, gercek deger farkli olabilir.
- Bos stok il bazinda bulunamadi. Kisi basi Istanbul degeri (450 bin / 15,75 mn) tum sehirlere uygulandi. Anadolu'da bos stok Istanbul'dan dusuk veya yuksek olabilir.
- Kiraci payi (%27), hane buyuklugu (Konya, Adana, Kocaeli) ulusal varsayim.
- Konya, Adana, Kocaeli fiyat ve kira Emlakjet-Endeksa Agustos 2026 aktarimi. Bursa, Antalya, Konya, Adana, Kocaeli beklenen reel fiyat artisi KFE'den (Anadolu icin ozel veri yok).
- Katilim tavani %25 ve etkin tahsilat %30 Istanbul'dan alindi, Anadolu icin kalibre edilemez.
- Ulusal sosyal kira (10-12 bin TL) tum sehirlerde ayni alinmis. Sehir bazli sosyal kira farkliysa sub. degisir.
- Tarife sehre ozgu, veriler yer tutucu oldugu icin sonuclar yon gosterir, nokta degil. Hepsinde finansman rahat cikti, bu yer tutuculara duyarsiz bir sonuc.
