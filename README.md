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

```bash
python -m hekis.enflasyon
```

Uc ikincil kanal (konut/kira, tedarik zinciri mahsubu, ic borclanma) cozulurse yillik TUFE kac puan duser. Katki ayristirmasidir, tahmin degil. Gozlem repo verisinden, varsayimlar aralik olarak cekilir (Monte Carlo, 20 bin cekim). Doviz kisiti modelde yok, kalan olarak raporlanir.

Baz sonuc: tam cozumde yil 1 icin medyan 1,1 puan (aralik 0,7-1,5), ataletle 3. yilda 1,8 puan (1,2-2,6). Yarim uygulamada bunun yarisi. En belirsiz sayi, kilitli alacagin kapali dongu payi. Bu sayiyi e-fatura eslesme verisi olcer, model olcmez.

Doviz kanali (D) Drive'daki `Secici_Kredi_Veri_MOBIL.pdf` serisiyle kalibre edildi (`python -m hekis.kalibre`): TUFE ~ kur + onceki yil TUFE, 10 gozlem. Ayni yil geciskenlik 0,43 (se 0,16), atalet 0,68 (se 0,16). Kur 2023-25 dosyadan, 2014-22 hafizadan (dogrulanmadi). Indirgenmis bicim, ortak sok yukluyor, uzun donem 1,33 (>1) bunu gosterir.

Hepsi birlikte cozulurse medyan: yil 1 ~6,9 puan, yil 3 ~12,3 puan (aralik 8-18), yani %31,5 -> yaklasik %19 (%14-23).

## Ucluk acmaz ve gerceklik testleri

```bash
python -m hekis.acmaz       # altkume etkileri + 5 yillik enflasyon yolu
python -m hekis.gerceklik   # 8 test, gecmeyeni gizlemez
```

`acmaz`: kira (A), mahsup (B), ic borclanma (C) ve doviz (D) tek tek ve birlikte cozulur. Tek basina cozumde sizinti varsayimi vardir (0-%40, veriden tanimlanamaz). Dinamik yol e_t = atalet*e_{t-1} + y1*g_t, baz %31,5 dondurulmustur.

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

