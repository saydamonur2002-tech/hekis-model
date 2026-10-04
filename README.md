# HEKIS modeli

Hedef Endeksli Kapali Ic Senet. Kapali kira-uretim devresinin stok-akim hesabi.

Bu bir politika vaadi degil, uc defteri ayiran bir hesap makinesidir. Mulkiyet, oturan ve senet ayni sayiyi tasimak zorunda degildir. Esit gostermek cifte yazimdir.

Repo ozeldir. Calisma taslagidir, dogrulanmis bir kamu maliyesi modeli degildir. Not kopyasi: `saydamonur2002-tech/modeller` icinde `HEKIS_Kapali_Kira_Uretim_Devresi.md`.

## Calistirma

Python 3 yeter. Ek paket yok.

```bash
python -m hekis.simulate
python -m hekis.bind_cli
```

`bind_cli` fiyati, kirayi ve enflasyonu `data/istanbul_2026.json` dosyasindan okur. Kaynaklar `data/OKUMA.md` icindedir. Eski `scenarios/` uydurma fiyatla duruyor. Gercek kosu o degil.

## 2026 bagi, 1000+1000+500 olcek

Istanbul satis m2 66.905 TL. Kira m2 479 TL. Bosluk %3,7, Avrupa yakasi elektrik aboneligi.

Gider: emlak vergisi binde 2 (ust sinir), DASK 2.022 TL/daire, bos dairenin aidati sahibe yazilir. Aidat Istanbul ortalamasi 3.330 TL/ay (2026 site aidati haberi aktarimi). Turkiye ortalamasi 600 TL tek basliktan, kapsami teyitsiz, Istanbul stoku icin dusuk, baz alinmadi. Bakim yilda giris degerinin %1'i, yabanci rehber araligi %1-3'un alt ucu, Turkiye verisi degil.

Enflasyon: Agustos 2026 yillik %31,51 (TUIK). Ileri yol Hazine ve Maliye OVP 2027-2029: %28,4 / %21 / %13,5 / %9, sonrasi %9 sabit (varsayim).

"Odenen", havuzun 20 yilda sahibe reel olarak geri odedigi anapara payidir. Yuksek iyidir. "Yuk", kira farki ile havuzun kapatamadigi aciktir, bugunku TL ile.

A eski model: enflasyon %31,5 donuk, kira aninda TUFE, gider yok. B kira 12 aylik TUFE ortalamasiyla, giderler dahil. C ayrica OVP yolu.

| Kosu | A odenen / yuk | B odenen / yuk | C odenen / yuk |
| --- | --- | --- | --- |
| Piyasa kira, TUFE | %100 / 0 | %100 / 0 | %100 / 0 |
| Piyasa kira, sabit | %23 / 0 | %11 / 1,6 mr | %25 / 0,1 mr |
| HEKIS kirasi, TUFE | %61 / 3,2 mr | %36 / 3,2 mr | %41 / 3,5 mr |
| HEKIS kirasi, sabit | %10 / 0,5 mr | %2 / 2,6 mr | %3 / 2,0 mr |
| Resmi sosyal kira, TUFE | %34 / 0 | %9 / 0 | %12 / 0 |
| Esenyurt, TUFE | %100 / 0 | %100 / 0 | %100 / 0 |
| Esenyurt, %20 alti kira | %100 / 2,0 mr | %100 / 2,0 mr | %100 / 2,2 mr |
| HEKIS, ulusal bos stok %27 | %46 / 2,5 mr | %17 / 2,5 mr | %21 / 2,7 mr |

Duyarlilik (HEKIS kirasi, TUFE, C kosusu, geri odenen): bazda (Istanbul ortalamasi 3.330 TL, bakim %1) %41. Turkiye ortalamasi 600 TL ile %56. Besiktas 8.400 TL'de %14. Bakim %2'de bu degerler %36, %21, %0. `python -m hekis.bind_cli` tum tabloyu basar.

## Bos stoku kullandirma

`python -m hekis.activation`. Bos duran daire sisteme girerse ne olur. Orta semt Istanbul ortalamasi, ucuz semt Esenyurt. Havuz kirayi oder, oturan sosyal kira oder, fark butcedir.

Istanbul'da bos konut 225 bin (elektrik aboneligi, Buyukduman) ile 450-750 bin (IBB) arasinda tahmin ediliyor. Stok 4,5 milyon. Yontem farki, tek sayi degil. Orta/ucuz semt payi bilinmiyor, yari yariya senaryodur. Katilim orani gozlem degil, kalibre edilmemis en onemli girdidir.

| Daire basina | Fiyat | Sahibin bos maliyeti / yil | Sosyal sub. / yil | 20 yil odenen | 20 yil yuk |
| --- | --- | --- | --- | --- | --- |
| Orta semt | 4,68 mn TL | 51 bin TL | 65 bin TL | %41 | 1,4 mn TL |
| Ucuz semt (Esenyurt) | 2,41 mn TL | 24 bin TL | 85 bin TL | %100 | 1,8 mn TL |

Ornek: 225 bin bos stokun %10'u girerse 22.500 daire, 80 mr TL giris degeri, 20 yilda yaklasik 36 mr TL (bugunku TL) yuk. Katilim %25 olursa 91 mr TL.

Ucuz semtte geri odeme %100 cikmasi Esenyurt fiyatinin turetilmis olmasina dayanir. Esenyurt aidati kaynaksiz varsayim.

Bu blokta olmayanlar: tadilat, kiraci bulma gecikmesi, dairenin oturulabilir olup olmadigi, katilim karari, kademeli giris.

### Katilim simulasyonu

Sahip, bos tutmaktan beklenen reel getiri ile senedin reel getirisini (0) karsilastirir. Katilim = tavan x lojistik(egim x (tutma maliyeti + bos tutma bedeli - beklenen reel artis)).

Testler: `python -m unittest discover -s tests` (15 test, model degismezleri ve katilim kurali). Kalibrasyon ve bant: `python -m hekis.calibrate`.

Kalibrasyon sonucu. Beklenti kurali (onceki yillarin reel KFE artisi) bir yil ilerisini tahmin etmede sifir tahmininden iyi degil: RMSE 20-24 puan, pencere farklari anlamsiz. n=9. Pencere 1 secildi, ama secim gurultuye yakin. Davranis modeli olarak tutulur, tahmin modeli olarak degil. Tavan (%40) ve egim (25) icin gozlem yok, kalibre edilemez.

Bugun beklenen reel artis -%6,5. 450 bin bos stok, bedel %1, orta nokta (tavan %40, egim 25): yaklasik 161 bin daire, 571 mr TL giris degeri, 20 yilda 261 mr TL yuk. Tavan ve egim bandinda (tavan %10-60, egim 10-50) giren daire 32 bin ile 266 bin arasinda, yuk 51-432 mr TL. Sekiz kat fark.

Geriye donuk (pencere 1): 2021 %1, 2022 %0,3, 2023 %0, 2024 %3, 2025 %38, 2026 %26, bugun %35. Patlama rejiminde katilim sifir. Bos tutma bedeli %0-2 araliginda katilimi sadece birkac puan oynatir: tavan sinirlayici, insentif degil.

Yurt disi benzerleri (`data/ANALOG.md`). Bos stoktaki tepkiyi olcen tek net ornek Vancouver: bos konut vergisi degerin %1'inden %3-5'ine cikarken bos konut sayisi 2017-2022'de %54 azaldi (bir kismi sahibinin oturmasiyla, kiraya verilenler %25). Fransa'da vergi onemli olcude etkili olmadi, Irlanda'da kendi beyanli vergi sinirli kaldi. Yaptirimsiz gonullu programlar cok dusuk: Portekiz'de kira sozlesmelerinin %0,12-0,4'u, Irlanda Repair and Leasing'de basvuranlarin %3,8'i anlasma imzaladi. Bunlar secilmis kitle uzerinden, bos stoga orani degil.

Bu uc ucla sinirlanmis senaryolar (450 bin bos stok): gonullu tek basina %4 katilim, 20 bin daire, 32 mr TL yuk. Mevcut karma varsayim (bedel %1, tavan %40) 161 bin daire, 261 mr TL. Vancouver benzeri (bedel %3, tavan %55) 231 bin daire, 374 mr TL. Mevcut kanun taslagindaki bedel (%0,2-2) Vancouver'in altinda, Fransa'nin basarisiz kaldigi duzeye yakin. Merkezi %40 varsayimina ancak guclu yaptirimla ulasilir, gonullu program tek basina ulasmaz.

### Subvansiyon

`python -m hekis.subsidy`. Havuz sahibe piyasa kirasini oder, oturan sosyal kira oder, fark butcedir. 161 bin dairede (mevcut karma senaryo) yil 1 subvansiyonu yaklasik 12 mr TL, 20 yilda 261 mr TL (bugunku TL), daire basina ayda yaklasik 6.750 TL. Prim ve havuz acigi sifir: yukun tamami kira farkidir.

Havuz her durumda tam kirayi aldigi icin oturanin odedigi pay sahibe geri odemeyi degistirmez: ayni 20 yilda %75. Oturan kiranin tamamini odese subvansiyon sifir olur, geri odeme degismez. Subvansiyon bos stoku kullandirmanin maliyeti degil, sosyal kira kararinin maliyetidir. Ayri karar, ayri tartisilmali.

Kalan %25 anapara 20. yilda reel olarak odenmemis durur. Senedi devlet garanti ederse bu gizli yukumluluktur, modelde yuk olarak sayilmiyor.

### Dereceli kira, bedel ve siyasi hesap

`python -m hekis.politics`. Gelir dagilimi: TUIK 2025 medyan 241 bin, ortalama 333 bin TL (`data/GELIR.md`), lognormal uydurma. Sinavi: ust %20 payi model %48,5 (TUIK %48), alt %20 model %5,0 (TUIK %6,4). Esdeger-hane katsayisi 2,0, gelir artisi (asgari ucret 2024-2026) ve hane sayisi varsayimdir.

Oturan min(kira, a x gelir) oder, kura ile secilir. a %30, uygun kitle gelirin alt %40'i: ortalama odeme 9.990 TL, subvansiyon 6.830 TL/ay, yilda 13 mr TL (duz sosyal kira referansi 12,4 mr). Kesim dusurulursa (alt %20) subvansiyon 19 mr TL'ye cikar: en yoksulu hedeflemek pahali. 161 bin daire uygun kiracilarin %5,3'une yeter, %95'i disarida kalir.

Bos tutma bedeli gelir olarak subvansiyonu karsilar mi: tahsilat %60 varsayimiyla bedel %2'de gelir/subvansiyon 0,9, %3'te 1,3. Yani Vancouver'in etkili bulunan %3 duzeyi ayni zamanda kendini finanse eden duzey. Bedel %1'de genel hane basina yilda yaklasik 250 TL yuk kalir.

## Sinir

Tip fiyati m2 carpi 40/60/95 olcek varsayimidir, sayim degil. Esenyurt satis fiyati gozlem degil, 18 yil iddiasindan turetilmistir. Fiziki uretim endeksi hala disaridan. Ulusal %27 bos stok ile %3,7 elektrik boslugu ayni sey degil. Bakim orani, aidat ve kira artisinin 12 aylik ortalamaya baglanmasi dogrulanmamistir. OVP yolu hedeftir, tahmin degil. 2029 sonrasi %9 varsayimdir. Model yeni konut istahini kapatmaz.
