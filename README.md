# HEKIS modeli

Hedef Endeksli Kapali Ic Senet. Kapali kira-uretim devresinin stok-akim hesabi.

Bu bir politika vaadi degil, uc defteri ayiran bir hesap makinesidir. Mulkiyet, oturan ve senet ayni sayiyi tasimak zorunda degildir. Esit gostermek cifte yazimdir.

Calisma taslagidir, dogrulanmis bir kamu maliyesi modeli degildir. Not kopyasi: `saydamonur2002-tech/modeller` icinde `HEKIS_Kapali_Kira_Uretim_Devresi.md`.

## Calistirma

Python 3 yeter. Ek paket yok.

```bash
python -m hekis.simulate
python -m hekis.bind_cli
```

`bind_cli` fiyati, kirayi ve enflasyonu `data/istanbul_2026.json` dosyasindan okur. Kaynaklar `data/OKUMA.md` icindedir. Eski `scenarios/` uydurma fiyatla duruyor. Gercek kosu o degil.

## 2026 bagi, 1000+1000+500 olcek

Istanbul satis m2 66.905 TL. Kira m2 479 TL. Enflasyon ileri patikada son gozlenen yillik oran, %31,5, donduruldu. Bu dondurma veri degil. Bosluk %3,7, Avrupa yakasi elektrik aboneligi. Aidat 3 bin varsayim.

| Kosu | Statik geri donus | 20 yilda reel erime |
| --- | --- | --- |
| Piyasa kira, TUFE'ye bagli | 13,5 yil | tamamlanir |
| Piyasa kira, nominal sabit | 13,5 yil | %23 |
| HEKIS kirasi 20/15/10, oturan sosyal kira, TUFE | 31,8 yil | %63 |
| Resmi sosyal kira, TUFE | 55,9 yil | %36 |
| Esenyurt gozlenen kira, 18 yil turev fiyat | 23,0 yil | %87 |
| HEKIS, ulusal bos stok %27 | 42,0 yil | %48 |

Piyasa kirasi endekslenirse havuz anaparayi reel olarak 15 yilda bitirir. Endekslenmezse enflasyon havuzu yer, 20 yilda anaparanin ancak dortte biri erir. HEKIS kirasi piyasanin altindadir. Oturan resmi sosyal kirayi oderse fark butcedir. Bu fark da endekslenirse reel yillik transfer yaklasik 162 milyon TL'dir. Nominal toplam 161 milyar yaziyorsa bu enflasyonun toplamidir, bugunku yuk degil.

## Sinir

Tip fiyati m2 carpi 40/60/95 olcek varsayimidir, sayim degil. Esenyurt satis fiyati gozlem degil, 18 yil iddiasindan turetilmistir. Fiziki uretim endeksi hala disaridan. Ulusal %27 bos stok ile %3,7 elektrik boslugu ayni sey degil. Model yeni konut istahini kapatmaz.

## Enflasyon katki modeli

### KANONIK SONUC: `python -m hekis.sonuc`

Uclu acmaz (kira/konut, mahsup, ic borclanma) cozulurse enflasyon, yavas uygulamayla, baz %31,5'e gore: 1. yil ~0,3, 3. yil ~1,5, **5 yilda ~2,7 puan** (carry rejimi 'tam ornek'; 2024-25 rejiminde ~3,0). Bunun ~1,9'u dogrudan etki, ~0,6'si doviz borcu uzerinden (kappa'ya bagli, 0-1,2). Doviz bu kanallarin sonucu olarak icsel kurulur (`borc_doviz.py`), dissal degil. Katki ayristirmasidir, tahmin degil. Tahmin ve OVP kiyasi: `ovp.py`.

**KALDIRILDI:** eski dissal doviz kanali (D) ve ondan gelen "hepsi cozulurse %19 / yil 3 ~12 puan / 'hepsi %4,7'" sonuclari. Neden: ayni etki kappa ~12 gerektiriyordu, makul degil. Asagidaki tarihsel bolumlerde gecen o rakamlar gecersizdir.

(Tarihsel notlar, eski sirayla:)

```bash
python -m hekis.enflasyon
```

Uc ikincil kanal (konut/kira, tedarik zinciri mahsubu, ic borclanma) cozulurse yillik TUFE kac puan duser. Katki ayristirmasidir, tahmin degil. Gozlem repo verisinden, varsayimlar aralik olarak cekilir (Monte Carlo, 20 bin cekim). Doviz kisiti modelde yok, kalan olarak raporlanir.

Baz sonuc: tam cozumde yil 1 icin medyan 1,1 puan (aralik 0,7-1,5), ataletle 3. yilda 1,8 puan (1,2-2,6). Yarim uygulamada bunun yarisi. En belirsiz sayi, kilitli alacagin kapali dongu payi. Bu sayiyi e-fatura eslesme verisi olcer, model olcmez.

[KALDIRILDI] Doviz kanali (D) Drive'daki `Secici_Kredi_Veri_MOBIL.pdf` serisiyle kalibre edildi (`python -m hekis.kalibre`): TUFE ~ kur + onceki yil TUFE, 10 gozlem. Ayni yil geciskenlik 0,43 (se 0,16), atalet 0,68 (se 0,16). Kur 2023-25 dosyadan, 2014-22 hafizadan (dogrulanmadi). Indirgenmis bicim, ortak sok yukluyor, uzun donem 1,33 (>1) bunu gosterir.

Hepsi birlikte cozulurse medyan: yil 1 ~6,9 puan, yil 3 ~12,3 puan (aralik 8-18), yani %31,5 -> yaklasik %19 (%14-23).

## Ucluk acmaz ve gerceklik testleri

```bash
python -m hekis.acmaz       # altkume etkileri + 5 yillik enflasyon yolu
python -m hekis.gerceklik   # 8 test, gecmeyeni gizlemez
```

`acmaz`: kira (A), mahsup (B), ic borclanma (C) tek tek ve birlikte cozulur (D kaldirildi). Tek basina cozumde sizinti varsayimi vardir (0-%40, veriden tanimlanamaz). Dinamik yol e_t = atalet*e_{t-1} + y1*g_t, baz %31,5 dondurulmustur.

`gerceklik`: 6/8 gecti. Kalan iki test ornek disi: kur-TUFE iliskisi 2023-25'i 7-44 puan yanlis tahmin ediyor (RMSE 28, naif 19). Eksik degisken para politikasi gorunuyor. Reel faiz eklenince 2024-25 duzelir ama 2022-23 kotulesir, genel hata 33,5. Bu yuzden modele eklenmedi. Doviz kanali sonuclari bu nedenle ust sinir okunmali.

## Doviz dorduncu etki, ic olusan (borc_doviz)

```bash
python -m hekis.borc_doviz
```

Doviz dissal kisit degil, A (konut/varlik enflasyonu), B (mahsup), C (ic borclanma) sonucu kademeli birikmis doviz borcudur. Reel kesim net doviz acigi 2023-25: 70 -> 148 -> 189 mlr $ (GSYH'nin %6,2 -> %10,7 -> %11,6'si, Drive V21). 2024'te artis (78) cari acigin (13) 6 kati. Faiz-kur farki (carry) yuksekken en hizli artmis.

Sonuc: doviz borcu uzerinden etki 5. yilda 0,5 puan (0,1-1,5). Onceki dissal D (yil 5 ~10 puan) bu yapida kappa ~12 gerektirir, makul degil, bu yuzden `acmaz.py` icindeki D dissal okuma olarak ust sinirdir ve reddedilir. kappa veriden tanimlanamaz (3 stok gozlemi). Gerceklik testleri 4/7.

### Dongu: faiz - carry - doviz borcu

`python -m hekis.borc_doviz` dongulu yolu da basar. Enflasyon dusunce TCMB faizi indirir (taylor 0,3-1,0), carry daralir, doviz borclanmasi azalir. Kur artisi yavaslarsa carry geri artar (ters ayak). Ayrica dusen faiz firma maliyetini ve butce faizini azaltir. Bir yil gecikmeli, yil yil simulasyon.

Sonuc: dongu 5. yilda +0,13 puan (0-0,3), carpan medyan 1,06 (max 1,23), yani zayif ve kararli. Toplam 5. yil dusus 2,5-2,9 puan (taylor 0 -> 1). Gerceklik testleri 6/10.

### Birikim 2014'ten (birikim.py)

`python -m hekis.birikim`: net doviz acigi (NOP) 2014'ten kurulur, N0 bilinmeyen. NOP_t = NOP_{t-1} + c_up*max(carry,0) - c_dn*max(-carry,0), (N0, c_up, c_dn) 2023-25 gozlemlerine (70/148/189, +-12) ABC ile uydurulur. Sonuc: c_up 2,1-2,7 (kalibre), c_dn 0,1-0,7, N0 ~132 (67-193). 2025'i disarida birakinca tahmin 202 (gercek 189).

Tarihsel karsi-olgusal (A-C 2014'ten cozulseydi): 2025 enflasyonu medyan 4,6 puan dusuk (2,6-7,7), kacinilan NOP ~82 mlr $, NOP/GSYH %11,9 -> %6,8. Not: dogrudan A-C katkisi 2026 kalibrasyonundan yila sabit tasindi (anakronik), sonucu yukari esikler.

Kanal sinirlari: carry modeli 2015-18'de borcun arttigi hafizayi (kuresel likidite) aciklamaz, o yillarda yanlis isaret verir. Kur 2014-22 hafizadan. Gercek TCMB NOP serisi 2014-22 gelirse N0 ve c_dn dogrulanir.

#### 2014 cipasi (TCMB Finansal Istikrar Raporu, Mayis 2015)

s.18: reel sektorun net doviz pozisyonu acigi Subat 2015'te 177,8 mlr $, 2014 ortasindan beri belirgin bozulma yok, kisa vadeli acik 10 mlr $. s.25 (ayri tanim, finansal hesaplar): 2009 63 -> 2014 150 mlr $, kapsam farkli, kullanilmadi. birikim.py N0'i 177,8 +-12'ye bagladi. Sonuc: c_dn 0,6-0,7 (prior siniria dayanmadi), 2014 NOP/GSYH ~%18-19, 2025'te %11,9. Yani dolar bazinda 2025 (189) 2014 (178) ile yakin. 2023'teki 70 cukuru gecici, 2024-25 yeniden insa. 'Kademeli artis' 2014'ten bakinca net birikim degil, derin bir cozulmeden sonra geri donustur.

### TCMB resmi serisi (FKDFDVY, Temmuz 2026) ile yeniden kalibrasyon

Veri: `data/fkdfdvy_2026_07.json`, `data/FKDFDVY.md`. Kod: `hekis/nop_veri.py`. `birikim.py` artik ABC yerine gercek seriyi kullanir.

Bulgular:
- NOP 2014 174 -> 2017 200 (yillik tepe) -> 2023 71 -> 2025 190 -> 2026-07 211 mlr $. Dolar bazinda seri tepesi asildi. GSYH'ye oran %11,8 (2017 %23, 2014 ~%19), yani oran olarak yarisi.
- Carry katsayisi 11 yillik resmi seride 0,75 (se 0,34), R2 0,35. 2023'e kadar fit c = -0,04: carry 2024 oncesini aciklamaz. 2024-25 rejimi 2,6 ve 2,1. Iki rejim `borc_doviz.REJIM` ile ("tam" / "son2yil").
- Eski iki noktadan c=2,4 kestirimi 3 kat fazlaydi. 2015-17'de borc carry negatifken arttigi dogrulandi (kuresel likidite).
- 2024 bozulmasi (+75,6): yukumluluk +49, varlik -26,7. Yurt ici banka doviz kredisi +39,8, yurt disi +1,6. 2025: yukumluluk +68,4, varlik +24,2; yurt ici +27,3, yurt disi +25,3.
- Kisa vadeli net pozisyon (likidite tamponu) 70 (2022) -> 4,4 mlr $ (2026-07). Modelde yok.
- Model baz 2026-07 icin 203 (190-212) verdi, gercek 210,8. 2026 kalibrasyona girmedi.
- Ileri enflasyon iki rejimde de ~%28,8 (2030). Tarihsel karsi-olgusal: 2025'te 4,8 puan dusuk, kacinilan NOP 85 mlr $.
- Testler 2/5: carry anlamli ama 2015-17 isareti ve ornek disi 2024-25 tahmini tutmuyor, likidite tamponu modelde yok.

### Likidite tamponu ve stres (tampon.py)

`python -m hekis.tampon`: kisa vadeli net pozisyon (KV net) 2022 70 -> 2026-07 4,4 mlr $. Tersten stres: butun kisa vadeli kalemlerde (banka kredisi, ithalat borcu, net turev) yeniden finansman kaybi kac olunca likit varlik (mevduat+menkul) ve ihracat alacagi yetmez. Kirilma orani f*: 2020 %84, 2022 %79, 2023 %74, 2024 %49, 2026-07 %47. Tarihin en kotu yillik daralmasi %24 (ithalat borcu 2018), yani tolerans 3,3x'ten 2,0x'e dustu ama hala 2 kati. Tarihsel siddette stres talep dogurmuyor (P=%2, 2026-07). Yani KV net 'tampon bitti' gostergesi olarak yaniltici, f* dogru olcu.

Turev: KV turev yukumlulugu 2,3 (2022) -> 22,7 mlr $ (2026-07), turev varligi 13,6 -> 16,1. Net turev pozisyonu uzun taraftan +11 mlr $'dan kisa tarafa -6,6'ya gecti.

Ileri tampon yolu (KV net) baz senaryoda 2027'de negatife (P %66-86), cozumde gecikir. Testler 3/5: tampon kur sokunu onceden gostermedi (r=+0,60), eta ve TCMB payi rezerv verisi olmadan tanimlanamaz.

### TCMB resmi rezerv, Eylul 2026 (rezerv.py)

Veri: `data/urdl_20260925.json`, `data/URDL.md`. `python -m hekis.rezerv`.

- Resmi rezerv Agustos 186,7 -> 25 Eylul 171,2 mlr $ (-15,5). Altin fiyat degerlemesi -7,9 (4602 -> 4291 $/ons), altin miktari +0,5, altin-disi (doviz+SDR+IMF) -8,0. Yani dususun yarisi degerleme. Hafta hafta altin-disi: -2,0, -5,6, -1,2.
- Altin rezervin %64'u. Altin-disi 61,6.
- Kesin cikislar 12 ay: kredi/mevduat -40,2, forward kisa pozisyon -17,2, diger giris +3,7 = -53,7. Altin-disi net likit 7,8 mlr $ (3 ay: 52,7).
- Aylik 4-9 mlr $ net satisla altin-disi net likit 1-2 ayda biter (aritmetik, tahmin degil).
- Sistem ters stresi (firma + resmi katman): f* %47 (yalniz firma), %53 (resmi altin-disi), %75-97 (altinin %25-50'si satilabilirse). Tarihin en kotu daralmasi %24.
- eta ve cb'nin kur bacagi kur serisi olmadan hala tanimlanamaz.

### Kur 2026 ve kirilma senaryosu (kirilma.py)

Veri: `data/usdtry_2026.json`, `data/USDTRY.md` (TCMB EVDS gunluk, 2 Oca-6 Eki 2026). `python -m hekis.kirilma`.

- Kur 42,88 -> 49,12, YTD +%14,5, yillik tempo %19,4. Aylik %1,1-2,0 (sd 0,28), haftalik %0,31-0,38. Altin-disi rezerv -5,6 mlr $ oynarken kur 0,37'de kaldi: baski rezervde, kurda. Bu rejimde eta ~ 0, cb ~ 1, net likit bitene kadar.
- `enflasyon.cek` d_yil'i gozleme cekildi (%16-20, onceki %20-28 varsayimdi). Model bu kur hiziyla 2026 TUFE'yi ~26 veriyor, gozlem 31,5: ~5 puan eksik (T8 ve T-K3 kaldi).
- Kirilma senaryosu: J = kayma ustu sicrama, tarihte +20 (2018), +62 (2021), +20 (2022), +37 (2023) puan. TUFE'ye yil 1 12,3 puan, 3 yilda kumulatif 22. Cozumun (A+B+C+dongu) 3 yillik kazanci 2,7 puan. Maliyet/kazanc 8x; cozum kirilma olasiligini mutlak ~12 puan dusurse esitlenir. Olasilik bilinmiyor.

### TUIK metod kirilimlari (metod.py)

`python -m hekis.metod`. Kaynak arama ozetleri; TUIK/TCMB siteleri bu ortamdan acilamadi, metodoloji dokumani okunamadi.

- Ocak 2026: baz 2003=100 -> 2025=100, ECOICOP v2, 12 -> 13 grup (sigorta ve finansal hizmet yeni), 407 -> 428 madde, grup agirliklari HBA -> Ulusal Hesaplar. Konut %15,21 -> %11,40, ulastirma %15,34 -> %16,62, gida %24,96 -> %24,44. TUIK: aylik ve yillik oranlar zincirleme, gecmis seri kirilmadi. TCMB: agirlik Ocak etkisi ~-0,1 puan, hizmet payi artisi (mal-hizmet kaymasi 7,4 puan) yillik enflasyona ~+1 puan.
- Agustos 2026 yillik %31,51: konut grubu %39,77 (katki 5,01 puan), efektif agirlik %12,6, genel enflasyon hizinda artsaydi katki 3,97, genel ustu fazla 1,04 puan. Bu, A (kira) kanalinin ust siniri: dogrudan A medyan 0,13, asma olasiligi %0.
- `enflasyon.cek`: w_kira 4,0-7,5% (onceki 6-10), r_kira 42-55% (onceki 40-50). Kira agirligi dogrulanamadi.
- Model 2026 aciginin (~5,5 puan) ~1 puani kirilimla aciklanir, ~4,5 puan baska surucu.
- TCMB YKKE (Sub 2026): yeni kiraci %34,2, mevcut kiraci %53,9. TUFE kirasi mevcut sozlesmeleri izler: yuksek olcum kismen eski sozlesmelerin yetismesi, guncel kitlik degil.

Guncelleme: birincil kaynak eklendi, `data/TUIK_DUYURU_30102025.md` (TUIK Kamuoyu Duyurusu 30.10.2025). Dogruladigi: baz 2025=100, ECOICOP v2, grup agirliklari Ulusal Hesaplar HHNTH'den (AB tarafindan zorunlu), alt duzey agirliklar HBA'dan, mevcut seri zincir yapiyla yeniden gruplanir, 2003=100 donemi manset gostergelerinde degisiklik yok, yalniz bazi alt endekslerde siniflama farki olabilir. Icermedigi: agirlik, madde ve grup sayisi (arama ozetinden). Sonuc: manset 2015-25 TUFE serisi kirilmamis, Drive'daki konut grubu serisi ile 2026 konut grubu ayni kapsam olmayabilir.

### OVP 2027-2029 simulasyonu ve tahmin (ovp.py)

`python -m hekis.ovp`. Resmi rakamlar arama ozetlerinden (OVP belgesi okunamadi). OVP yil sonu TUFE: 2026 28,4 (onceki OVP'de 16), 2027 21, 2028 13,5, 2029 9. TCMB (Ag 2026): 2026 28, 2027 15, 2028 9. OVP buyume 3,3/4,2/4,6/5,0; acik/GSYH 3,1/3,5/3,1/2,8; cari acik mlr $ 47,5/38,5/37/35,5.

Tahmin cekirdegi TUFE_t = a + b*kur_t + rho*TUFE_t-1 + delta (kalibre.py, bootstrap), kayma kurali kur = oran*TUFE_t-1. delta onceligine cok duyarli:
- cipali (2026 sonu TCMB'nin 28'ine baglanir, delta sonraki yillara tasinir): 28,0 / 26,7 / 25,4 / 24,1. OVP'yi tutturma olasiligi 2027 %2, 2028 %1, 2029 %2.
- tarihsel kalinti U(-4,2): 24,6 / 20,2 / 16,1 / 12,1 (p10-p90 2029: 3-34).
- Tutmak icin gereken ek dezenflasyon (kalinti): OVP 2027 -3,7, 2028 -4,0, 2029 -1,3; TCMB 2027 -9,3 (tarihte en fazla -6,1 gorulmus). Cozum (A-C+doviz borcu) 2029'da ~1,5 puan ekler, OVP'ye yetmez. Kur sicramasi senaryosu 2027 40%.
- OVP gecmis hatasi ~+12 puan (2024-25 hafizadan). Testler 0/2, 3 bilgi.

