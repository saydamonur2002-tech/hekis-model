# HEKIS modeli

Hedef Endeksli Kapali Ic Senet. Kapali kira-uretim devresinin stok-akim hesabi.

Bu bir politika vaadi degil, uc defteri ayiran bir hesap makinesidir. Mulkiyet, oturan ve senet ayni sayiyi tasimak zorunda degildir. Esit gostermek cifte yazimdir.

Calisma taslagidir, dogrulanmis bir kamu maliyesi modeli degildir. Not kopyasi: `saydamonur2002-tech/modeller` icinde `HEKIS_Kapali_Kira_Uretim_Devresi.md`.

## Calistirma

Python 3 yeter. Ek paket yok.

```bash
python -m hekis.bind_cli    # gercek kosu: data/ altindaki gozlemlerle
python -m hekis.simulate    # ESKI, uydurma fiyatli scenarios/ kosusu (uyari basar)
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

## Durum

| Alan | Durum |
| --- | --- |
| Havuz / oturan / senet hesabi (`model`, `bind`, `owner`, `senet`) | Tamam, gercek veriyle kosuyor (`bind_cli`) |
| Enflasyon katki ayristirmasi (`sonuc`, `acmaz`, `borc_doviz`, `entegre`) | Calisiyor, ust sinir okunmali. Gerceklik 4/7 |
| Kanun taslagi (`data/KANUN_TASLAGI.md`) | Iskelet. Oranlar esik, gozlem degil |
| Finansal sistem (kupon, uretim hedefi) | Acilmadi. Model kapanmadan acilmaz kurali duruyor |
| `scenarios/` | Eski, uydurma fiyat. Silinmedi, simulate uyari basar |

Acik, veri gerektirenler: fiziki uretim endeksi, ITO kira alt kalemi, kira agirligi (`w_kira`), kur 2014-22 resmi serisi, kamu zam resmi tablosu, e-fatura eslesmesi (kilitli alacagin kapali dongu payi). Acik, olculemeyenler: kirilma olasiligi, kappa. Bunlar kodla degil veriyle kapanir, tahminle doldurulmadi.

## Modeller reposuyla yaklasik eslesme

`saydamonur2002-tech/modeller` belgeleri Drive aktarimi. Eslesme baslik okumasindan, yazar teyidi yok.

| Kod | Ilgili belge |
| --- | --- |
| `model`, `bind`, `senet` | `HEKIS_Kapali_Kira_Uretim_Devresi.md` (stok-akim formulleri) |
| `borc_doviz`, `birikim`, `tampon`, `rezerv`, `kirilma` | `Thirlwall_Minsky_SFC_Entegre_Model.md` (dis kisit, borc, bilanço) |
| `acmaz`, `enflasyon`, `entegre` | `Ampirik_Verilerle_Model_Sinamasi.md` (zarar aktarimi tau, dis kisit kappa) |
| `ovp`, makro yol | `Turkiye_Ekonomisi_Model_Analizi.md` (2026-2030 patikasi; o belge tek senaryo anlatisi, bu repo olasiligi bilinmiyor diye birakir) |

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

`gerceklik`: 4/7 gecti (T1 numpy/statsmodels yoksa atlanir ve sayilmaz; eskiden atlanan test gecmis sayiliyordu, skor sisikti). Kalan uc test (T2, T3, T8) ornek disi: kur-TUFE iliskisi 2023-25'i 7-44 puan yanlis tahmin ediyor (RMSE 28, naif 19). Eksik degisken para politikasi gorunuyor. Reel faiz eklenince 2024-25 duzelir ama 2022-23 kotulesir, genel hata 33,5. Bu yuzden modele eklenmedi. Doviz kanali sonuclari bu nedenle ust sinir okunmali.

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

### Resetleme: atalet kirilirsa (reset.py)

`python -m hekis.reset`. Atalet (rho ~0,68) enflasyonun ~%75'ini tasiyor. Koordineli bir endeksleme sifirlamasi rho'yu dusururse? Senaryo, mekanik sonuc degil: rho'nun dususu varsayim (0,10-0,35), baz ve geri tepme yok. 'Reset basarili' yolu 2027'de %10, 2028'de tabana (%3) iner, bu varsayimin aritmetigidir. Gercek bilgi: OVP yolu rho'nun 0,68'den ~0,45'e (%34, 1,5 se) dusmesini istiyor (makul); TCMB 2027 %15 icin 0,24 (2,7 se, makul degil). Reset + 2028 kur kirilmasi: 2028 %22. Kurumsal endeksleme: kira artisi yasal olarak 12 aylik ortalama TUFE ile sinirli (dogrulandi). Uluslararasi vakalar hafizadan.

### Olcum kontrolu: TUFE gercek enflasyonu olcuyor mu (olcum.py)

`python -m hekis.olcum`. Ana cerceve atalet (okuma 1), olcum belirsizligi kontrol degiskeni (okuma 2). Veri arama ozetlerinden, yalniz 2-3 nokta: ENAG Ara 2024 83,4, Ara 2025 56,14, Haz 2026 51,49, Agu 2026 49,03; TUIK 44,33 / 30,89 / 32,11 / 31,51; [DUZELTILDI, bkz. Ito bolumu: 23,25 ITO'nun TOPTAN endeksiydi, tuketici Ara 2025 %40,12] ENAG yontemi tartismali, sinir degeri olarak kullanildi.

Bulgu: bir yillik kalicilik TUIK x0,70, ENAG x0,67, yani atalet bulgusu olcuden bagimsiz (tek gecis, 2 nokta). Kur payi TUIK'te ~%26, ENAG'a gore ~%17; atalet her halukarda en buyuk. Kanonik sonuc 2,7 puan (TUIK puani), ITO tuketici olceginde 3,4, ENAG olceginde ~4,2 (orantili buyutme varsayimi); bant 2,7-4,2. Olcu farki zamanla kuculuyor (fark/TUIK 0,88 -> 0,56), sabit carpan degil. ENAG 2020-23 serisi yok, rho ENAG ile yeniden tahmin edilemez.

### ITO Enflasyon Indeksi, resmi tablo (ito.py)

Veri: `data/ito_enflasyon_endeksi.json`, `data/ITO.md` (ITO PDF, Ocak 2023-Eylul 2026, 45 ay, Istanbul Ucretliler Gecinme ve Toptan Esya). `python -m hekis.ito`.

- Yil sonu: ITO tuketici 74,88 / 55,27 / 40,12 (2023/24/25), TUIK 64,8 / 44,4 / 30,9, ENAG - / 83,4 / 56,14. ITO tuketici TUIK'in ~9-11 puan ustunde, ENAG'in altinda. Toptan 62,77 / 40,64 / 23,25.
- Bir yillik kalicilik: tuketici olculerinde x0,67-0,74 (TUIK 0,69-0,70, ITO 0,73-0,74, ENAG 0,67), toptan x0,57-0,65. Model rho 0,68 bandin icinde.
- Aylik yillik-yillik AR (ITO tuketici, n=33): rho 0,45 (se 0,19), R2 0,16. Yil sonu gecislerinden daha dusuk. Atalet 0,45-0,73 araligi; OVP'nin istedigi 0,45 bu aralikta (ust uste binen pencereler, tek rejim, dusuk R2).
- Tuketici-toptan makasi +12 (2023), +15, +17 (2025), Agu 2026 +14,5, Eyl 2026 +10,4: enflasyon mal/kur tarafinda degil hizmet ve marj tarafinda.
- Duzeltme: onceki surumde 'ITO Ara 2025 %23,25, TUIK'in altinda' demistim, bu toptan endeksiydi (arama ozeti karistirmisti).

### Kira bilesen: TCMB YKKE (kira.py)

Veri: `data/ykke_2026_08.json` (TCMB EVDS TP.YKKE.*, 2018-01..2026-08, 19 bolge). NOT: istenen 'Istanbul Ucretliler hizmet/kira bileseni' ITO'nun degildi; gelen dosya TCMB Yeni Kiraci Kira Endeksi. ITO alt kalemi hala yok. `python -m hekis.kira`.

- SEVIYE: yeni kira 2019-2025 yillik %10,3 / 26 / 53,5 / 122,5 / 117,2 / 57,7 / 36,0; reel yeni kira x2,5 (Oca 2018 -> Ara 2025 x2,2). 'Kira asla bu kadar yuksek olamaz' tezi SEVIYEDE destekleniyor (2021-23 reel +13/+35/+32).
- AKIS: Agustos 2026 yeni kira yillik TR %26,4 (TUIK 31,5: reel -3,9), Istanbul %34,5 (reel +2,3). Guncel kira primi yok. Onceki 'yeni kira reel ~sifir, tez zayif' sonucum tek noktaya (Subat 2026) dayaniyordu ve seviye icin YANLIS, akis icin dogruydu.
- HIPOTEZ (tek nokta): TUFE kira (mevcut sozlesme) ~ YKKE yillik 12 ay once. Subat 2026'da mevcut kiraci %53,9 = YKKE Subat 2025 %53,9 (6 ay: 45,4, 18 ay: 61,7 tutmuyor). Konut grubu Agu 2026 %39,77 ile tutarli (elektrik-gaz-su artisi 29-37%).
- Dogruysa TUFE kirasi kendiliginden duser: Ara 2025 57,7 -> Agu 2026 45,4 -> Ara 2026 36,0 -> Agu 2027 ~26,4. Kira agirligi 4,0-7,5% varsayimiyla TUFE'ye katki: 2026 ~1,2 puan [0,9-1,6], 2027 ~0,6 puan. OVP'nin istedigi ek dezenflasyonun (-3,7) ~%15'i. A kanalinin dogrudan etkisi (0,2) bunun yaninda ikincil.

### ITO alt kalemler: konut, hizmet, gecikme sinamasi (ito_alt.py)

Veri: `data/ito_alt_kalem.json` (ITO Fiyat Indeksleri Kitabi PDF: Istanbul Ucretliler Geckinme, 9 alt grup yillik % degisim Oca 2021-Ara 2025, seviye 1996-2025, 1995=100). `python -m hekis.ito_alt`. Genel Aralik yillik degerleri onceki ITO tablosuyla birebir ayni (capraz dogrulama).

- Aralik 2025 yillik: genel 40,1; KONUT 59,2 (+19,1); ulastirma+haberlesme 56,3 (+16,2); gida 36,0; saglik 32,8; kultur-egitim 31,1; ev esyasi 29,1; giyim 24,0.
- Konut - genel (puan): 2021 +6,4, 2022 -13,0, 2023 -28,7, 2024 +27,4, 2025 +19,1. Sozlesmelerin gecikmeli yetismesi (2022-23 yasal kira tavani %25 hafizadan, dogrulanmadi).
- Konutun goreli fiyati (konut/genel): 1996-2020 ort 1,306 (sd 0,090), 2023 dip 0,874, Aralik 2025 1,169: tarihsel ortalamanin 1,5 sd altinda. YKKE'deki reel x2,5'e ters gorunur; konut endeksi kira+enerji+bakim bilesimi, mevcut sozlesmeler.
- Gecikme sinamasi: konut yillik ile YKKE yillik(t-L) korelasyonu en iyi L=23 ay (r=0,45), L=12'de 0,16. kira.py'nin 12 ay hipotezi bu seride DESTEKLENMEDI. L=24 seviye olarak imkansiz (Ara 2025 kira %117 > konut %59). Makul L=12-18: kira kendiliginden dezenflasyonu 2026 1,2-1,6, 2027 0,6-1,2 puan.
- Testler 3/4 (T-A3 ve T-A7 hipotez reddi). Kira alt kalemi ve agirliklari ITO tablosunda yok.

### Atalet gercek mi? (atalet.py)

`python -m hekis.atalet`. Uc soru:
1. ISTATISTIKSEL: kalicilik var. Permutasyon p ~0,02 (10 gozlem); TUIK 0,69-0,70, ITO 0,73-0,74, ENAG 0,67; aylik ITO 0,38-0,45. Olcuye bagli degil, buyuklugu 0,4-0,7. (Newey-West n=10'da guvenilmez.)
2. GOLGE: gecikmeli kur eklenince rho 0,68 -> 0,43 (se 0,15): ataletin ~%36'si gecmis kur soklarinin golgesi. Bir yili disarida birakinca 0,32-0,65. 3 terimli modelde pozitif parcalar icinde kur (bu yil + gecen yil) %54, saf atalet %46. Iki terimli modelde atalet %75 / kur %27 idi: AYRIM SPESIFIKASYONA BAGLI. Onceki 'atalet kurun 3 kati' ifadesi iki terimli modele ozgu, geri cekilmeli.
3. MEKANIZMA: olculebilen endeksleme (kira sozlesmesi) saf ataletin ~%10'unu aciklar. Gerisi (ucret, beklenti, yonetilen fiyat) olculmedi.

### Asgari ucret, PKA beklentileri, TUIK agirlik tablosu (ucret.py, beklenti.py, metod.py)

Veri: `data/asgari_ucret.json` (arama sonuclari, resmi PDF okunamadi), `data/pka_2026_09.json` (TCMB PKA Eylul 2026), `data/tufe_agirlik_2016_2026.json` (TUIK Tablo4, birincil).

**Asgari ucret** (`python -m hekis.ucret`): Ocak artisi = 11,0 + 0,61*onceki yil TUFE (n=11, R2 0,80; 2019-26: b 0,62, R2 0,88). Ocak artisi / onceki TUFE: 2024 0,76, 2025 0,68, 2026 0,87. Hedefin 11-16 puan ustunde (2024-25 hedef hafizadan). Reel asgari ucret 2015-25 x1,57. SAGLAMLIK: AR modeline ucret artisi eklenince rho 0,68 -> 0,32 gorunur ama yalniz Ocak kararinda anlamsiz, 2022-23 disarida etki yok (rho 0,72, c negatif). 'Ataletin yarisi ucret kanali' KANITLANMADI. Saglam: ucret davranisi gecmisi izliyor.

**PKA Eylul 2026** (`python -m hekis.beklenti`): TUFE beklentisi 2026 sonu 29,61, 2027 sonu 22,69, 12 ay 23,70, 24 ay 18,32 (TCMB hedefi 5: 13 puan fark, capa yok). Beklenen kalicilik 0,75-0,77, gerceklesen 0,67-0,74. Kur 2026 sonu 51,57, 12 ay 58,60 (ima edilen oran kur/onceki TUFE ~0,63, modelin 0,5-0,9 araliginda). Politika faizi 37 -> 35,07 -> 29,22 -> 22,43. Cari acik beklentisi -50,1 / -44,4. Modelde faiz26 prior'i %30-42'den %35-40'a cekildi (T-B4 2026-07 NOP tahmini 203 -> 206, gercek 210,8).

**TUIK agirlik tablosu**: 2026 agirliklari arama ozetleriyle birebir tutuyor. Konut 15,26 -> 11,40, lokanta 8,32 -> 11,13, eglence 2,13 -> 4,34, saglik 4,09 -> 2,79, bilgi 4,81 -> 3,10. Kira ornegi 5.246 sozlesme. Kira kaleminin kendi agirligi YOK, w_kira hala varsayim.


## Kamu zamlari ve PKA beklenti zaman serisi (hekis/kamu.py)
`python -m hekis.kamu`. Veri: data/kamu_zamlari.json (arama ozeti, guven bayrakli), data/pka_zaman_serisi.json (EVDS PKA 2014-04..2026-09).
- Emekli artisi mekanik geriye endeksleme: 2026 iki artisin bilesigi 32,11 = TUIK Haz 2026 yillik TUFE (tutarli; 2025: 35,0 vs 35,05 hafizadan). 2024 Ocak 49,25 dusuk guven.
- Memur zammi / onceki yil TUFE: 2025 0,26, 2026 0,60; asgari ucret 0,68 ve 0,87 (toplu sozlesme asgariden dusuk).
- PKA: Ocak yil-sonu beklentisi onceki yil gerceklesmesiyle korelasyon 0,97 (beklenti = a + 0,54*onceki yil), gerceklesmeyi ort. +10,4 puan dusuk tahmin etmis; gerceklesme ~ beklenti (b 1,38) ama onceki yil eklenince ayrisamiyor (n=11). 24 ay beklentisi 18,3 (hedef 5): capa yok.
- Sonuc: atalet **beklenti ve yasal/idari endeksleme kanallarindan geriye bakisla tasiniyor**; hangisinin NEDEN oldugu bu veriyle ayrilamaz. Kamu zam verisi resmi tabloyla dogrulanmali.

## Dezenflasyon politikasinin enflasyonist etkisi (hekis/dezenf.py)
`python -m hekis.dezenf`. Politika = yuksek reel faiz (~13,8 puan ex-ante) + kontrollu kur kaymasi. Dogrudan maliyet: firma faiz maliyeti +0,5, butce/mali +0,2 (toplam ~0,7 puan/yil, parametreler onsel); kur kazanci -5,4 [4-10] puan/yil (karsi-olgu: kur = TUFE kadar kayardi; kasitli uc nokta). Dogrudan net dezenflasyonist.
Asil maliyet kazancin BORC ALINMIS olmasi: kirilmada 3 yil kum. +22 puan; kirilma olasiligi %73'u gecerse 3 yillik net kazanc sifirin altina iner. Kirilma olasiligi bilinmiyor. Olculmeyenler: yonetilen fiyat/vergi telafisi, talep kanali (dusurucu), ihracat rekabeti.

### Aylik beklenti testi (kamu.py bolum 5; data/tufe_yillik_aylik.json EVDS TP.TUKFIY2025.GENEL_3)
12 ay beklentisi (n=138, 2014-04..2025-09, Newey-West): MAE 12,5 vs 'bugunku yillik TUFE devam' 13,1; ort. hata +11,7 (2021-23 +34; 2014-20 +3,5; 2024-26 +5,0). bek = 4,5 + 0,47*bugun, R2 0,92: beklenti buyuk olcude geriye bakis. gerc ~ 0,79(0,51)*bek + 0,20(0,21)*bugun: ikisi ayrisamiyor. 2024-26'da beklenti saf kurali belirgin geciyor (MAE 5,0 vs 16,3, n=21): beklenti 2024'ten sonra daha bilgilendirici. 24 ay beklentisi saf kurali gecemiyor (19,2 vs 17,7). Bu bir NEDENSELLIK testi degil.

## Modelin amaci: ATALET / UCLU ACMAZ / DOVIZ yuzde ayrismasi (hekis/ayrisma.py)
`python -m hekis.ayrisma`. 2026 enflasyonu (28 puan) uc kovaya: ATALET (saf, acmazin tasinan kismi cikarilmis) %41-68, DOVIZ (kur) %26-57, UCLU ACMAZ dogrudan ~%7 (MC %4-10), KALAN %-2/-5. Aralik indirgenmis formun spesifikasyonundan (2 terimli vs gecikmeli kurlu 3 terimli) gelir: tek bir yuzde verilemez. Katki ayristirmasidir, nedensellik degil; atalet ve beklenti ayni anda olusur.

## Entegre uclu model (hekis/entegre.py): R atalet sifirlama + A uclu acmaz + F doviz akisi normalizasyonu
`python -m hekis.entegre`. Sira R -> A -> F; 8 alt kume, sirali ve Shapley katki, etkilesim, kirilma riski ayarli yol (2027-2031, baz 2026=28).
Bulgular (2029, medyan puan dusus): R tek ~20,7 (rho 0,68 -> 0,10-0,35 VARSAYIMI; veride karsiligi yok, %39'u %3 tabanina dokunuyor), A tek ~1,6, F tek ~-7,8 (enflasyonist: kur kaymasi/enflasyon 1'e giderken b+rho>1, cipa tek nominal capa), hepsi ~19,5. Sirali: +R -20,8, +A -0,4, +F +1,9. F yalniz R'den SONRA anlamli; F'nin tek faydasi kirilma olasiligini dusurmesi (olasilik bilinmiyor, pb0 hassasiyeti). R yari basariliysa hepsi 2029'da 14,6 (tam R'de 4,9). Kirilma gerceklesirse F'li yol daha kotu (10,9 vs 6,6).
