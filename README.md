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

Gider: emlak vergisi binde 2 (ust sinir), DASK 2.022 TL/daire, bos dairenin aidati sahibe yazilir. Aidat Turkiye ortalamasi 600 TL/ay, ama bu rakam tek basliktan, kapsami teyitsiz ve Istanbul stoku icin dusuk. Bakim yilda giris degerinin %1'i, yabanci rehber araligi %1-3'un alt ucu, Turkiye verisi degil.

Enflasyon: Agustos 2026 yillik %31,51 (TUIK). Ileri yol Hazine ve Maliye OVP 2027-2029: %28,4 / %21 / %13,5 / %9, sonrasi %9 sabit (varsayim).

"Odenen", havuzun 20 yilda sahibe reel olarak geri odedigi anapara payidir. Yuksek iyidir. "Yuk", kira farki ile havuzun kapatamadigi aciktir, bugunku TL ile.

A eski model: enflasyon %31,5 donuk, kira aninda TUFE, gider yok. B kira 12 aylik TUFE ortalamasiyla, giderler dahil. C ayrica OVP yolu.

| Kosu | A odenen / yuk | B odenen / yuk | C odenen / yuk |
| --- | --- | --- | --- |
| Piyasa kira, TUFE | %100 / 0 | %100 / 0 | %100 / 0 |
| Piyasa kira, sabit | %25 / 0 | %13 / 1,5 mr | %30 / 0 |
| HEKIS kirasi, TUFE | %74 / 3,2 mr | %50 / 3,2 mr | %56 / 3,5 mr |
| HEKIS kirasi, sabit | %12 / 0,5 mr | %3 / 2,4 mr | %6 / 1,7 mr |
| Resmi sosyal kira, TUFE | %47 / 0 | %22 / 0 | %27 / 0 |
| Esenyurt, TUFE | %100 / 0 | %100 / 0 | %100 / 0 |
| Esenyurt, %20 alti kira | %100 / 2,0 mr | %100 / 2,0 mr | %100 / 2,2 mr |
| HEKIS, ulusal bos stok %27 | %56 / 2,5 mr | %31 / 2,5 mr | %36 / 2,7 mr |

Duyarlilik (HEKIS kirasi, TUFE, C kosusu, geri odenen): aidat 600 TL ve bakim %1 icin %56. Istanbul ortalamasi 3.330 TL aidatta %41. Besiktas 8.400 TL'de %14. Bakim %2'de bu degerler %36, %21, %0. `python -m hekis.bind_cli` tum tabloyu basar.

## Sinir

Tip fiyati m2 carpi 40/60/95 olcek varsayimidir, sayim degil. Esenyurt satis fiyati gozlem degil, 18 yil iddiasindan turetilmistir. Fiziki uretim endeksi hala disaridan. Ulusal %27 bos stok ile %3,7 elektrik boslugu ayni sey degil. Bakim orani, aidat ve kira artisinin 12 aylik ortalamaya baglanmasi dogrulanmamistir. OVP yolu hedeftir, tahmin degil. 2029 sonrasi %9 varsayimdir. Model yeni konut istahini kapatmaz.
