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
