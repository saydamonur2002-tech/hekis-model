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

## Sinir

Tip fiyati m2 carpi 40/60/95 olcek varsayimidir, sayim degil. Esenyurt satis fiyati gozlem degil, 18 yil iddiasindan turetilmistir. Fiziki uretim endeksi hala disaridan. Ulusal %27 bos stok ile %3,7 elektrik boslugu ayni sey degil. Bakim orani, aidat ve kira artisinin 12 aylik ortalamaya baglanmasi dogrulanmamistir. OVP yolu hedeftir, tahmin degil. 2029 sonrasi %9 varsayimdir. Model yeni konut istahini kapatmaz.
