# Blokaj modeli: parametreleri veriden kestirme

`data/kurumlar.json` ornek parametrelerle gelir, olculmedi. Bu belge `I`, `B0`, `delta` icin olculebilir karsiliklari ve sinirlarini anlatir. Arac: `hekis/blokaj_veri.py`.

## Ne olculur

| Parametre | Olcu | Formul |
| --- | --- | --- |
| I | D'nin dosyayi bilme orani | `m / n_X`, yakalama-yeniden yakalama |
| B | D'nin bildigi dosyalardan yaptirima donmeyen pay | `1 - y / n_D` |
| delta | B'nin merkezilesmeye duyarliligi | kurum sabit etkili egim, B uzerine C |

`n_D`: D'nin kayitli dosya sayisi. `n_X`: D'den bagimsiz ikinci kaynaktaki dosya sayisi. `m`: iki kaynakta da gorunen. `y`: n_D icinden pencere icinde yaptirima donenler. `C`: formal merkezilesme, 0-1.

## Kullanim

```bash
cp data/dosya_sayim_sablon.csv data/dosya_sayim.csv   # doldur
python -m hekis.blokaj_veri data/dosya_sayim.csv       # kurumlar_olculen.json yazar
python -m hekis.blokaj data/kurumlar_olculen.json      # modeli olculen parametrelerle calistir
python -m hekis.blokaj_veri --test                     # yontem sinamasi (sentetik)
```

## Ilk aramada ne bulundu

Hazir bir `I` veya `B` istatistigi bulunmadi. Bulunan, dogrudan istatistik degil, ham madde:

- Sayistay kurum bazli denetim raporlari (sayistay.gov.tr/reports). `n_D` icin aday kaynak.
- Sayistay Kanunu madde 78: suc teskil eden fiillerin Sayistay Baskanligi uzerinden savciliga gonderilmesi. `y` icin aday: sevk edilen bulgu sayisi.
- Adalet Istatistikleri Haber Bulteni (adlisicil.adalet.gov.tr). Savcilik sevkinin yargi sonucu icin ust katman.
- Arama bu ortamdan yapildi, tam metin raporlar okunmadi. Hicbir rakam bu belgede verilmis degildir.

## Bilinen sinirlar

1. **Bagimsizlik.** `n_X` D'den bagimsiz olmali. Iki kaynak ayni seyi gorunur kiliyorsa (ornegin ikisi de basin taramasi, D de basini izler) N dusuk, I yuksek cikar.
2. **D secilmis olabilir.** Sayistay raporu da D'nin parcasi. Organ ele gecirilmisse n_D kendisi secilmistir; bu yontem onu yalniz n_X ile karsilastirarak yakalar.
3. **Pencere.** `y` icin beklenen sure B'yi degistirir. Gec yaptirim erken yilda B'yi yukari iter.
4. **Rakip hat.** 'Rakip hat acti' ile 'devlet denetledi' y icinde ayrilmaz. B alt sinir olabilir.
5. **C bir tanimdir.** Formal merkezilesmeyi nasil olctugun (yetki devri, onay kademesi sayisi, merkeze baglanan karar orani) delta'yi belirler.
6. **Yalniz uc parametre.** `tau, a, r, p_pat, q_rival, phi` olculmez, ornek kalir. Cikti bu yuzden kesin sayi degil, hangi kurumda ne yonde sorusudur.

## Yontem sinamasi (sentetik, gercek degil)

200 sentetik veri setinde (10 donem, gercek I=0,55, B0=0,30, delta=0,35) %90 aralik gercek degeri I icin %88, delta icin %84 yakaladi. Hedef %90. delta araligi biraz dar: yalniz 10 satirla satir bootstrap'i aralik dar verir. Gercek veride az donemle delta'ya guvenme, araligi 0'i iceriyorsa isaret bilinmiyor say.
