# Sira

Durum, 2026-10-05. Kapsam Istanbul.

1. Model. TAMAM. Havuz, oturan, senet, elde tutma karari, uc bolge, luks tarife, abonelik, dereceli kira, duran insaat, havuz kirasi carpani. 46 test, 15 gerceklik kontrolu, Monte Carlo. Ozet `SONUC.md`, ayrinti `README.md`, varsayimlar `data/VARSAYIM.md`.
2. Finansal sistem. ACILABILIR, ama model sonucuyla senet tasarimi cakisiyor (asagida).
3. Yaptirim kanun taslagi. GUNCELLENDI (`KANUN_TASLAGI.md`, 2026-10-05): bolge ayrimi, luks tarife, tespit, tamamlama maddesi, model bagi. Anadolu buyuksehirleri icin ayri tarife yazildi (`ANADOLU_TARIFE.md`, %0,5 genel / %3 luks, veri `ANADOLU.md`).

## 2. Finansal sistem: modelden gelen girdiler ve cakismalar

Model verdi: reel kupon sifir, anapara TUFE ile yurur, geri odeme %83 (luks ayrilmis) ile %100 arasi, anapara 20. yilda tamamen odenmemis kalir (m<0,8 iken %67-85). `hekis/senet.py` Esenyurt tabanli 6,03 mr TL anapara ve hedef primi varsayiyor: eski, guncel baz degil.

| Konu | Eski tasarim (`senet.py`, `SENET.md`) | Modelin gosterdigi | Yapilacak |
| --- | --- | --- | --- |
| Ihrac buyuklugu | 6,03 mr TL, Esenyurt tabani | Bos stok icin ~89 mr TL, duran insaat ~3,2 mr TL (baz) | Ihrac tabanini guncel havuz buyuklugune bagla |
| Geri odeme | Anapara TUFE ile yurur, itfa sistem icinde | 20 yilda %67-100 odenir, kalan anapara durur | Odenmeyen kalan icin itfa kurali ve garanti sorusu |
| Hedef primi | Fiziki endeks 1'i gecince, 1/7 sahipte | Fiziki endeks modelde yok (sabit 1,00) | Endeks disaridan, model kapatamaz |
| Katilim primi | Yok | Prim katilimi %16-28 artirir, tavana carpar | Prim yerine tavani artiran tadilat/duran insaat |
| Kupon | Reel sifir | Katilim reel faize bagli (esik ~ -%0,4) | Kupon sifir kalirsa pencere reel faize bagimli |

## 3. Yaptirim kanun taslagi: guncelleme oncesi uyumsuz maddeler (hepsi KANUN_TASLAGI.md'de giderildi)

Taslak "ucuncu ve sonrasi duran birim %4" diyor (Esenyurt, havuz %80 teklif, 5 yilda satis karari). Guncel model bedeli ayri kullanir.

| Taslak maddesi | Modelin guncel degeri | Sorun |
| --- | --- | --- |
| 3. Ucuncu ve sonrasi %4, tek oran | Genel bedel %1, luks %5 (ayri tarife), tampon genel bedel | Taslakta luks ayri tarife yok, bolge ayrimi yok |
| 2. Ikinci konut binde 2 | Genel bedel %1 (bos stok) | Taslak sembolik, model etkili |
| Beyan esasli | Etkin tahsilat %30 (en olasi), Irlanda isaretlenenin ~%6'si | Taslak beyana dayaniyor, tespit icin elektrik tuketimi/aboneligi yok |
| 5. Bitmemis stok satis tesviki alamaz | Duran insaat tamamlanip havuza girer (tamamla-kirala-devret) | Taslak yasak koyuyor, tamamlama mekanizmasi yok |
| 8. Kira indirimi konu disi | Dereceli kira %30 ve abonelik sub. modelin parcasi | Taslak ayri, ama sosyal kira kararinin maliyeti buyuk |
| 7. Havuz teklifini reddetmek serbest | Sahip kararina bagli katilim, tavan %25 | Tutarli |
| Kentsel donusum, tadilat | Model disinda | Kapsam notu yok |

Taslaktaki "Anayasa madde 35 ve 73" siniri hala ayri sinav, modellenmedi.

## Sirada
1. Senet tasarimini guncel havuz buyuklugu ve odenmeyen kalan anapara icin yeniden yaz.
2. TOKI-HEKIS is bolumu (`TOKI_HEKIS_IS_BOLUMU.md`) taslak maddelere baglanir.
