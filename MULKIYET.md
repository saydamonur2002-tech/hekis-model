# Mulkiyet defteri

Ilk defter. Birim stoku. Kira yok, senet anaparasi yok.

## Acilis

Esenyurt, Agustos 2026. Endeksa-Emlakjet ilan endeksi, tapu islemi degil.

- m2 34.475 TL
- brut 105 m2
- ortalama 3.619.875 TL
- nominal yillik %32,18, ileri yolda donduruldu, dondurma veri degil

Ilce stok adedi bilinmiyor. Istanbul ortalamasindan turetilmez. 1000 olcek sayim degil.

Sinif payi gozlem degil. TUIK oturma bicimi malikin ikinci ve ucuncu dairesini saymaz. Pay %10, %30, %50 duyarlilik.

Bosluk iki vekil, ayni stok degil: elektrik aboneligi %3,7 ve ulusal kalinti %27.

Iskansiz birim satis adedine girmez.

## Akis

Bedel yalniz bos ucuncu ve sonrasina isler. Birincil 0, ikinci binde 2 bu kosuda yok: binde 2 stok getirmez, owner.py'de durur.

Satis, birikmis bedel farki kapatinca gelir. Iki teklif kurali:

- oransal: teklif her yil fiyatin yuzdesi. Yil = (1 - teklif) / oran. Varlik artisi karari degistirmez.
- sabit: teklif acilis fiyatina kilitli. Fiyat artinca fark bedelden hizli buyur, satis gecikir.

%80 teklif ve %2 oran, oransal kuralda statik 10 yil. %4 oran statik 5 yil. Akis ayni sayiyi satmaz: bedel gecmis fiyattan birikir, fark guncel fiyattir. Varlik artisi %32,18 dondurulunca yuzde 4 bes yilda stok getirmez. Bu esik, gozlem degil.

## Kapanis

Satilan adet mulkiyetten duser. Kalan bos durur. Cikan deger senet defterine alacak diye not dusulur, bu defterde anapara yazilmaz.

Kosu: `python -m hekis.mulkiyet`