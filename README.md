# HEKIS modeli

Hedef Endeksli Kapali Ic Senet. Kapali kira-uretim devresinin stok-akim hesabi.

Ilk halka budur: havuz, oturan, senet. Bu halka bitmeden senet piyasasi ve kanun maddesi acilmaz. Sira `data/SIRA.md`.

Bu bir politika vaadi degil, uc defteri ayiran bir hesap makinesidir. Mulkiyet, oturan ve senet ayni sayiyi tasimak zorunda degildir. Esit gostermek cifte yazimdir.

Calisma taslagidir, dogrulanmis bir kamu maliyesi modeli degildir. Not kopyasi: `saydamonur2002-tech/modeller` icinde `HEKIS_Kapali_Kira_Uretim_Devresi.md`.

## Bu halkanin kanali: varlik enflasyonu

HEKIS TUFE modeli degildir. Kendi nesnesi varlik enflasyonudur: satis fiyati ile kira getirisi arasindaki stok, bos tutulan birimin elde tutma karari, anaparanin reel erimesi.

Ilk halka icin asagidaki hesap yeter. TUFE ayrismasi, atalet, kur, OVP, NOP ve rezerv bu halkanin sonucu degildir. O arastirma `ENFLASYON.md` dosyasina alindi. Oradaki sayilar kanonik HEKIS sonucu degildir.

Varlik enflasyonu uc satirdan okunur:

- Giris degeri mulkiyet defteridir. Havuz neti kira eksi aidattir. Ikisi ayni sayi degildir.
- Kira endekslenirse havuz anaparayi reel yer. Kira nominal sabit kalirsa enflasyon havuzu yer. Ikisi de varlik fiyatinin getiriye karsi hareketidir.
- Oturanin odeyecegi ile sahip getirisi ayri satirdir. Fark butcedir, havuzdan kesilmez.

## Calistirma

Python 3 yeter. Ek paket yok.

```bash
python -m hekis.simulate
python -m hekis.bind_cli
```

`bind_cli` fiyati, kirayi ve enflasyonu `data/istanbul_2026.json` dosyasindan okur. Kaynaklar `data/OKUMA.md` icindedir. Eski `scenarios/` uydurma fiyatla duruyor. Gercek kosu o degil.

Ilk halkanin kosusu bunlardir. `python -m hekis.sonuc` ve enflasyon modulleri `ENFLASYON.md` altindadir.

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

Bu tablo varlik enflasyonunun iki ayagidir: fiyat stoku ile kira akimi. Geri donus yili, varligin kendi getirisinden ne kadar yavas odendigini gosterir. Reel erime, anaparanin enflasyon karsisinda ne kadar kaldigini. TUFE'ye kac puan etki ettigi bu tablonun isi degildir.

## Sinir

Tip fiyati m2 carpi 40/60/95 olcek varsayimidir, sayim degil. Esenyurt satis fiyati gozlem degil, 18 yil iddiasindan turetilmistir. Fiziki uretim endeksi hala disaridan. Ulusal %27 bos stok ile %3,7 elektrik boslugu ayni sey degil. Model yeni konut istahini kapatmaz.

Ilk halka bu sinirlar kapanmadan bitmis sayilmaz. Senet notu `data/SENET.md`, yaptirim iskeleti `data/KANUN_TASLAGI.md`. Ikisi de model kapanmadan yazildi. 1/7 ve yuzde 4 gozlem degil, esik.

## Disari alinan

TUFE arastirmasi `ENFLASYON.md`. Kod duruyor, ilk halkanin kanonik kosusu degil.