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

Istanbul satis m2 66.905 TL. Kira m2 479 TL. Aidat 3 bin varsayimdir. Gider: emlak vergisi binde 2, DASK 2.022 TL/daire, bos dairenin aidati sahibe yazilir (kaynakli). Bakim yilda giris degerinin %0,5'i (varsayim). Bosluk %3,7, Avrupa yakasi elektrik aboneligi.

"Odenen", havuzun 20 yilda sahibe reel olarak geri odedigi anapara payidir. Yuksek olmasi iyidir. "Yuk", kira farki ile havuzun kapatamadigi aciktir, bugunku TL ile. Nominal toplam enflasyonun toplamini da icerir, o yuzden kullanilmaz.

Uc kosu yan yana. A eski model: enflasyon %31,5'te donuk, kira aninda TUFE kadar artar, gider yok. B kira yenilemede 12 aylik TUFE ortalamasi ile artar, gider eklendi. C ayrica enflasyon %31,5'ten %15'e dogrusal iner (varsayim).

| Kosu | A odenen / yuk | B odenen / yuk | C odenen / yuk |
| --- | --- | --- | --- |
| Piyasa kira, TUFE | %100 / 0 | %100 / 0 | %100 / 0 |
| Piyasa kira, sabit | %23 / 0 | %15 / 0,8 mr | %15 / 0,6 mr |
| HEKIS kirasi, TUFE | %63 / 3,2 mr | %47 / 3,2 mr | %50 / 3,3 mr |
| HEKIS kirasi, sabit | %10 / 0,5 mr | %4 / 1,6 mr | %4 / 1,5 mr |
| Resmi sosyal kira, TUFE | %36 / 0 | %20 / 0 | %22 / 0 |
| Esenyurt, TUFE | %100 / 0 | %100 / 0 | %100 / 0 |
| Esenyurt, %20 alti kira | %100 / 2,0 mr | %100 / 2,0 mr | %100 / 2,1 mr |
| HEKIS, ulusal bos stok %27 | %48 / 2,5 mr | %29 / 2,5 mr | %30 / 2,5 mr |

Gider eklenince geri odeme belirgin duser. Sabit kirada gider TUFE ile artar, havuz bir noktadan sonra negatife doner. Dusen enflasyon sonucu pek degistirmez, cunku kira ve gider ayni endekste.

## Sinir

Tip fiyati m2 carpi 40/60/95 olcek varsayimidir, sayim degil. Esenyurt satis fiyati gozlem degil, 18 yil iddiasindan turetilmistir. Fiziki uretim endeksi hala disaridan. Ulusal %27 bos stok ile %3,7 elektrik boslugu ayni sey degil. Bakim orani ve kira artisinin 12 aylik ortalamaya baglanmasi dogrulanmamis varsayimdir. Dusen enflasyon yolu tahmin degil, varsayimdir. Model yeni konut istahini kapatmaz.
