# HEKIS modeli

Hedef Endeksli Kapali Ic Senet. Bos konut stokunu kullandirmanin stok-akim hesabi. Uc defter ayri tutulur: mulkiyet, oturan, senet. Esit gostermek cifte yazimdir.

Bu bir politika vaadi degil, hesap makinesidir. Repo ozel, kisisel modelleme. Dogrulanmis bir kamu maliyesi modeli degildir. Gozlem ile varsayim ayri tutulur, ayri dosyalarda: `data/VARSAYIM.md`.

**Kapsam: simdilik yalniz Istanbul.** Nufus 15,75 mn, 5,11 mn hane, 1,38 mn kiraci hane (hane buyuklugu 3,09 ADNKS; kiraci payi %27 ulusal varsayim, Istanbul'a ozgu veri bulunamadi; hane geliri baz ulusal TUIK dagilimi, bant sendika 0,63 ile Istanbul TR10 1,31 arasi, `hekis.union`). Diger sehirler 7c'de ayri, kapsam disi tutulur; ulusal hane sayisi artik kullanilmaz.

## Calistirma

Python 3 yeter. Ek paket yok, testler `unittest`.

```bash
python -m unittest discover -s tests   # 29 test
python -m hekis.checks                 # gerceklik kontrolleri
python -m hekis.analysis               # tornado, Monte Carlo, rank korelasyonu, ters stres
python -m hekis.final                  # uc sistem, luks ayrimi, luks bedel
python -m hekis.bind_cli               # stok-akim, eski A/B/C karsilastirmasi
python -m hekis.calibrate              # beklenti kurali kalibrasyonu, katilim bandi
python -m hekis.selffinance            # kendini finanse etme cebiri
```

## Veri

`data/`: istanbul_2026.json (girdiler), OKUMA.md, TEYIT.md, KFE.md (TCMB konut fiyat endeksi), KREDI.md (ipotekli pay), FAIZ_KUR.md, GELIR.md (TUIK), ANALOG.md (Vancouver, Irlanda, Fransa, Portekiz, Ispanya), VARSAYIM.md (varsayim envanteri ve etki sirasi).

## 0. Hangi komut hangi kurali kosar

Bu repoda iki ayri hat var, birbirine karistirilmamali.

| Hat | Komutlar | Kira ve oturan odemesi | Enflasyon |
| --- | --- | --- | --- |
| Eski sekiz mod | `hekis.bind_cli` | Sabit: `hekis` modunda sosyal kira, `esenyurt` modunda oturan havuz kirasinin tamamini oder (sub. 0), `sub20` %80. Gelir degiskeni ve %30 kurali YOK. `hekis` modunun havuz kirasi `policy_rent` 20/15/10 bin (kaynak: model varsayimi) | A, B sutunu: son gozlem %31,51 donuk; C: OVP |
| Gelirli hat | `final`, `zones`, `analysis`, `reality`, `union`, `stalled`, `cities` | Esenyurt gozlem kirasi 20/17/14,25 bin (KiraMetre ilan medyani), oturan min(kira, gelirin %30'u) (kural varsayim) | OVP yolu, donuk degil |

`bind_cli` tek baz degil, sekiz modu birden kosar. Guncel baz sonuclar gelirli hattadir. Eski `data/ESENYURT_SUB20.md` olu nottur (fiyat kira x 12 x 18), kosan kod teyitli Endeksa m2'sini kullanir. Kira artisi: model 12 aylik TUFE ortalamasini yillik adimda onceki ve cari yil enflasyonunun ortalamasi olarak yaklasik hesaplar; ilan edilen %31,79 yasal tavani her yenilemede yeniden ilan edilir, modelde dogrudan girdi degil. `main` dali eski surumdur, bu dal guncel.

### Sahibin senede karsilik kabul ettigi kira (havuz kirasi carpani)

`zones.run_three_zone(pool_rent_mult=m)`, `bind.build_units(rent_mult=m)` (esenyurt ailesi). m havuzun aldigi kirayi carpar, oturan payi ayri kalir (dereceli %30). Baglanti (varsayim): sahibin senet getirisi -lambda x (1-m), lambda havuz brut kira girisi / deger (%8,3). Esenyurt tipi havuz, en olasi senaryo:

| m | Katilim baglantisi | Daire | Yil 1 sub. | Oran | Geri odenen | 20 yil yuk |
| --- | --- | --- | --- | --- | --- | --- |
| 1,0 | - | 37 bin | 3,9 | 2,39 | %100 | 84 |
| 0,9 | acik | 35 bin | 3,0 | 3,09 | %100 | 65 |
| 0,8 | acik | 34 bin | 2,3 | 4,14 | %100 | 48 |
| 0,7 | acik | 32 bin | 1,6 | 5,71 | %85 | 35 |
| 0,6 | acik | 30 bin | 1,2 | 8,04 | %67 | 24 |

m dusurmek subvansiyonu keser (m=0,8'de -%41), katilimi az keser (-%9), cunku beklenen reel artis -%3,7 iken sahipler doygun bolgede. Beklenen reel artis yukselince isirir: g_e %0'da m=0,8 / m=1,0 katilim orani 0,84, %4'te 0,76. Baglanti kapali olsa katilim ayni kalir. Geri odeme m=0,7'de %85'e, 0,6'da %67'ye duser: yani 20 yilda anaparanin bir kismi odenmemis kalir.

## 1. Stok-akim cekirdegi

Istanbul satis m2 66.905 TL, kira m2 479 TL. Havuz sahibe kirayi oder, bakim/vergi/DASK/bos dairenin aidati havuzdan duser, oturan sosyal/dereceli kira oder, fark subvansiyondur. "Odenen" havuzun 20 yilda sahibe reel geri odedigi anapara payidir, yuksek iyidir.

A eski (donuk %31,5 enflasyon, kira aninda TUFE, gider yok), B kira 12 aylik TUFE ortalamasi ve gider dahil, C ayrica OVP yolu (%28,4/21/13,5/9). Odenen / yuk (mr TL, bugunku):

| Kosu | A | B | C |
| --- | --- | --- | --- |
| Piyasa kira, TUFE | %100 / 0 | %100 / 0 | %100 / 0 |
| Piyasa kira, sabit | %23 / 0 | %11 / 1,6 | %25 / 0,1 |
| HEKIS kirasi, TUFE | %61 / 3,2 | %36 / 3,2 | %41 / 3,5 |
| Resmi sosyal kira | %34 / 0 | %9 / 0 | %12 / 0 |
| Esenyurt, %20 alti kira | %100 / 2,0 | %100 / 2,0 | %100 / 2,2 |
| HEKIS, ulusal bos stok %27 | %46 / 2,5 | %17 / 2,5 | %21 / 2,7 |

Gider kalemleri: emlak vergisi binde 2 (ust sinir), DASK 2.022 TL, bos dairenin aidati sahibe yazilir (Istanbul ort. 3.330 TL/ay), bakim yilda degerin %1'i (varsayim). Bos dairenin sahibe maliyeti yilda yaklasik degerin %1,05'i.

## 2. Bos stoku kullandirma

Istanbul'da bos konut 225 bin (elektrik aboneligi) ile 450-750 bin (IBB) arasinda tahmin ediliyor, stok 4,5 milyon, yontem farki var. Orta semt Istanbul ortalamasi, ucuz semt Esenyurt.

| Daire basina | Fiyat | Sahibin bos maliyeti / yil | Subvansiyon / yil | 20 yil odenen |
| --- | --- | --- | --- | --- |
| Orta | 4,68 mn TL | 51 bin | 65 bin | %41 |
| Ucuz (Esenyurt) | 2,41 mn TL | 24 bin | 85 bin | %100 |

Katilim: sahip, bos tutmaktan beklenen reel getiri ile senedin reel getirisini (0) karsilastirir. Katilim = tavan x lojistik(egim x (tutma maliyeti + bedel - beklenen reel artis)). Tavan %40 ve egim 25 kalibre edilemez. Beklenti kurali (onceki reel KFE artisi) bir yil ilerisini sifir tahmininden iyi tahmin etmiyor (RMSE 21,0 vs 20,7 puan, n=9): davranis varsayimidir, tahmin degil. Tarihsel olarak negatif reel faiz donemi (2021-2023, reel faiz -%14 ile -%35) ile reel konut sicramasi (+%20, +%53, +%11) ortusuyor, kredi payi ayni donemde dusuyordu (%38'den %11'e). Kosul bugun: reel faiz +%3 ile +%6,5, reel konut -%6,5, katilim penceresi acik. Fiyat patlarken katilim sifira yakin: sistem ters donguludur.

Yurt disi benzerleri (`data/ANALOG.md`): Vancouver bos konut vergisi (%1'den %3-5'e) bos konut sayisini 2017-2022'de %54 azaltti, bunun yarisi sahibinin oturmasiyla. Fransa'da etkili olmadi, Irlanda'da kendi beyanla sinirli kaldi. Gonullu programlar cok dusuk: Portekiz kira sozlesmelerinin %0,12-0,4'u, Irlanda Repair and Leasing basvuranlarin %3,8'i. Gonullu tek basina yaklasik %4 katilim, guclu yaptirimla en fazla %50 civari.

## 3. Dereceli kira, abonelik, subvansiyon

Kararlar: oturan dereceli kira oder (min(kira, %30 x gelir), alt %40 gelir dilimi, kura ile), aidat havuzda, abonelik (elektrik, dogalgaz, su, yaklasik 1.583 TL/ay, gaz ve su alt sinir) tam subvanse. Gelir dagilimi: TUIK 2025, medyan 241 bin, ortalama 333 bin, lognormal uydurma (ust %20 payi model %48,5 TUIK %48; alt %20 %5,0 vs %6,4).

Subvansiyon bos stoku kullandirmanin maliyeti degil, sosyal kira kararinin maliyetidir: oturan kiranin tamamini odese subvansiyon sifir olur, geri odeme degismez. Havuz her durumda tam kirayi alir. Aidati oturana gecirmek geri odemeyi %75'ten %91'e cikarir ama oturanin konut yukunu %30'dan %34-40'a cikarir. Kalan %25 anapara 20. yilda odenmemis durur: senet garantisi varsa gizli yukumluluk.

## 4. Luks ust dilim

Orta tipteki bos stogun en pahali %20'si (45 bin daire, ortalama 9,5 mn TL) havuz disi, bos olsa bile, bedelden muaf degil, ayri tarife. Deger dagilimi lognormal (sigma 0,6, varsayim). Orta tipin kirasi degerle orantili olceklenir (yapisal secim): sabit politika kirasi tutulursa gelir/sub. orani 0,65 yerine 0,82 ve geri odeme %83 yerine %99 cikar.

Luks tepkisi Vancouver ankorlu (bedel %3'te bosluk %54 azalir, tavan %65), yuksek bedelde kacinma (%5 ustu her puan icin tahsilat 5 puan duser, taban %10). Toplam bedel geliri / yil 1 subvansiyon, luks bedel %1/3/5/8/12: karma sistem 0,55/0,70/0,82/0,87/0,79, Vancouver benzeri 0,74/0,84/0,92/0,96/0,90. Kacinma dahil luks gelirinin tepesi bedel %8,2 civari, yilda 5,5 mr TL: luks tek basina sistemi finanse edemez. %5 bedelde luks bos dairenin %62'si bosluktan cikar (yaklasik 28 bin daire, havuz disi).

## 5. Uc sistem (luks ayrilmis, bugunku TL)

| Sistem | Katilim | Daire | Giris | 20 yil odenen | Yil 1 sub. | 20 yil yuk | Gelir/sub. |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Gonullu tek basina | %4 | 18 bin | 51 mr | - | 1,4 mr | 29 mr | 0 |
| Karma (bedel %1, tavan %40) | %36 | 146 bin | 421 mr | %83 | 11,4 mr | 243 mr | 0,39 (luks bedelli 0,62) |
| Vancouver benzeri (bedel %3, tavan %55) | %51 | 208 bin | 602 mr | - | 16,4 mr | 347 mr | 0,62 (luks bedelli 1,09) |

## 6. Kendini finanse etme

Kosul: bedel x tahsilat >= (12 s / V) x p / (1 - p). s yerlesen daire basina aylik subvansiyon, V deger, p yerlesen oran. Katilim arttikca bedel odeyen taban erir. V 3,55 mn, s 8 bin TL/ay icin gerekli etkin bedel p %10'da %0,3, %36'da %1,5, %50'de %2,7, %60'ta %4,1 (`hekis.selffinance`).

Monte Carlo (1500 cekilis, 19 parametre, ucgen dagilim, `hekis.analysis`, Istanbul): yerlesen daire %5/%50/%95 yuzdeliginde 18/103/216 bin, 20 yil yuk 29/158/412 mr TL. Kendini finanse eden cekilis %83, ama bu olcege bagli: yerlesen daire 25 bin altinda %100, 25-75 binde %98, 75-150 binde %85, 150 binin ustunde %57 (medyan oran 1,09). Spearman(daire, oran) = -0,72. Baz durumda (132 bin daire) oran 0,93, sub. 10,4 mr, bedel 9,6 mr.

Sonucu en cok belirleyenler (rank korelasyonu, tornado): beklenen reel konut artisi (0,58), katilim tavani (-0,51), genel bedel, ayrilan luks pay, kira/gelir kurali, uygun kitle, etkin tahsilat. Bakim orani, aidat, stok buyuklugu (oranda), enflasyon yolu neredeyse hic.

## 7. Gerceklik kontrolleri

`hekis.checks`: 15 kontrol, 4 uyumlu, 9 uyari, 2 dogrulanamaz. Uyarilar: model bosluk orani (%3,7) bos stok tahminlerinin altinda; Esenyurt getirisi %7,3 vs Endeksa %10,04 (kaynaklar farkli); politika kirasi getirisi %3,8 vs piyasa %8,6; gelir dagilimi alt ucu fazla yoksul; ilk yil enflasyon yolu gozlenenin 2-3 puan altinda; beklenti kurali tahmin gucu yok; KFE Turkiye geneli Istanbul'dan 3 puan farkli; etkin tahsilat varsayimi iyimser; orta tip kirasi yapisal secim. Dogrulanamayan: katilim fonksiyonu, kisi basi subvansiyon.

## 7b. En olasi senaryo, guncel veriyle

`python -m hekis.reality`, `data/GUNCEL.md`. Eylul 2026 TUFE aciklanmadan once: Agustos yillik %31,51, Eylul beklentisi %30,16, yil sonu %29,66, politika faizi %37 (reel +%4,2), kira artis ust siniri (12 aylik TUFE ort.) %31,79 (kural dogrulandi), yeni kiraci %34,5, Gini 0,410.

Faiz kanali (2019-2025, n=7, R2 0,81, nedensellik degil): reel konut artisi = 0,005 - 1,35 x reel faiz. Bugunku reel faizde tahmin -%5,1, gozlenen -%6,5. Katilim penceresi reel faiz yaklasik -%0,4'un altina inmedikce acik; tampon 4,6 puan. Reel faiz 0'da yerlesen %30 duser, -%5'te dortte birine iner.

Senaryolar, Istanbul, beklenen reel artis -%3,7, ulusal TUIK gelir dagilimi (mr TL/yil, bugunku TL): en olasi (tavan %25, bedel %1, tahsilat %30, luks bedel %5) 82 bin daire, yil 1 sub. 6,5, bedel 6,1, oran 0,94, acik 0,4, 20 yil yuk 137. Iyimser 196 bin daire, sub. 15,3, oran 1,03, yuk 326. Kotumser 26 bin daire, yuk 43.

Etki (en olasi, 82 bin hane, hane basina ayda 6.524 TL): Istanbul'da uygun (alt %40) 551 bin kiraci hanenin %15,0'ina ulasir. Gini 0,4296 -> 0,4285 (-0,0011), goreli yoksulluk -0,27 puan, piyasa kirasi dogrusal yaklasimla -%6 ile -%20 (ust sinir, esneklik varsayimi). Yerlesen hanenin konut yuku gelire oranla alt %10'da %81'den %30'a, alt %40'ta %36'dan %30'a duser, aylik kazanc 12.100 ile 3.000 TL. Programsiz referans Esenyurt piyasa kirasi + abonelik, bu dusuk gelirli hanenin gercek karsi olgusunu abartabilir.

Duzeltme: bu bolumun onceki surumunde bos stok Istanbul'un (450 bin) ama kapsam ve etki 28 mn ulusal hane uzerindendi. Tutarsizlik giderildi.

### 7b-2. Sendika verisiyle hane geliri medyani

`python -m hekis.union`, `data/SENDIKA.md`. DISK-AR: ucretlilerin %46,7'si (8,36 mn) asgari ucret ve altinda, ozel sektor %49,6'si asgari ucretin %5 fazlasi ve alti. Medyan isci ucreti net asgari ucrete yakin: 28.076 TL (2026). Bu SGK kayitli bireysel ucrettir, hane geliri degil. Istanbul'a ozgu sendika verisi bulunamadi.

Uc anchor, en olasi senaryo: A sendika (28.076 x 1,5 calisan varsayimi = 42.113 TL hane medyani, yalniz ucret, alt sinir): 82 bin daire, sub. 9,9 mr, oran 0,61, 20 yil yuk 212, Gini -0,0025. B TUIK ulusal (66.369 TL, baz): sub. 6,5, oran 0,94, yuk 137, Gini -0,0011. C TUIK Istanbul (86.715 TL): sub. 4,6, oran 1,33, yuk 96, Gini -0,0006. Basabas hane medyani 69.638 TL/ay, net asgari ucretin 2,48 kati. Hane basina calisan sayisi 1,2'den 2,4'e giderse oran 0,55'ten 0,96'ya cikar. D IPA/TUIK Istanbul (TR10, IBBS-2) yoksulluk siniri 88.185 TL / 0,6 = 146.975 TL esdeger medyan, 2026'ya TUFE ile x2,57 veya ucret ile x2,82 yukseltilince hane medyani 62.954 ile 69.078 TL: oran 0,88 ile 0,99, sub. 6,9 ile 6,1 mr, yuk 147 ile 130 mr. D, B ile ve basabasla ust uste biner, A ve C'den bagimsiz ucuncu kanit. Istanbul Gini 0,428 (IPA, 2024) lognormal sigma 0,80'e karsilik gelir, modelin 0,803'u ile uyumlu; P80/P20 Istanbul 7,8, Turkiye 7,5 (`data/IBBS2.md`). Sonuc: sistem basabas civarinda, bagimsiz kanitlar 0,6 ile 1,3 arasi, ortadakiler (B, D) 0,9-1,0. Baz B.

### 7b-3. Memur maasi / asgari ucret

`data/MEMUR.md`. Temmuz 2026: en dusuk memur maasi (aile yardimi dahil) 70.224 TL = net asgari ucretin 2,50 kati, duz memur (13/1) kaba 55.000 TL = 1,96 kati, en dusuk memur emeklisi 31.527 TL = 1,12 kati. Model hane dagiliminda en dusuk memur maasi %53'luk, duz memur %41'lik dilime denk gelir. Basabas hane medyani 69.638 TL (asgari ucretin 2,48 kati), en dusuk memur maasinin %99,2'si: tesadufi yakinlik, nedensel degil. Uygunluk kesimi duz memur maasina baglanirsa (qcut 0,41) sonuc baza ayni (kapsam %14,7, oran 0,95); en dusuk memur maasina baglanirsa (qcut 0,53) uygun hane 727 bin, kapsam %11,3, sub. 5,3 mr, oran 1,15, 20 yil yuk 111 mr. Memur maasi aile yardimi dahil, hane geliri degil, ayrica memur hanelerinde ikinci gelir olabilir.

### 7b-4. Uc bolge: HEKIS, memur kesimi (tampon), luks

`python -m hekis.zones`. Bos stok deger sirasina gore uc bolgeye bolunur: alt %41 (gelir duz memur maasi 55.000 TL'nin altinda) HEKIS havuzu, %41-80 memur kesimi (tampon), ust %20 luks. Tampon havuza girmez, luks tarifesi de gormez: normal piyasa sistemi, genel bedel (%1) ve bosluga son verme tepkisi. Havuz Esenyurt tipi stoktan (ortalama deger 2,41 mn TL), tampon 4,69 mn, luks 9,47 mn.

En olasi senaryo: 37 bin daire yerlesir (iki bolgeli modelde 82 bin), uygun kiracinin %6,6'si, yil 1 sub. 3,9 mr, bedel 9,4 mr, oran 2,39, 20 yil yuk 84 mr. Bedelin 6,5 mr'si luks, 1,8 mr'si tampon, 1,1 mr'si havuza girmeyenden. Bosluktan cikan ve ozel piyasaya giren: tampon 51 bin, luks 55 bin daire. Oran artisi tamponun etkisi degil, tanim farki: onceki modelde luks yalniz orta tipin %20'siydi (45 bin daire), burada tum bos stokun %20'si (90 bin). Tampon genisligi: HEKIS ust kesimi q_h 0,30 / 0,41 / 0,53 / 0,65 iken daire 27 / 37 / 48 / 59 bin, oran 2,76 / 2,38 / 2,23 / 2,08. Varsayim: bos konut deger sirasina esit dagilmis (gercekte luks ve yatirim konutlarina kayik olabilir).

Varyantlar (`hekis.zones`, en olasi senaryo): tampon bedelsiz olursa bedel geliri 9,4'ten 7,6 mr'ye, oran 2,39'dan 1,94'e, bosluktan cikan 107 binden 55 bine iner, HEKIS ayni (37 bin daire). Bos konut luks bandinda yogunsa (luks payi %40 / %60): HEKIS havuzu 138 / 92 bin daireye, yerlesen 28 / 18 bin daireye duser, bedel geliri 15,2 / 21,0 mr, oran 5,2 / 10,7, 20 yil yuk 63 / 42 mr, bosluktan cikan 149 / 192 bin. Sorun finansmandan olcege kayar: luks bandi bedelle fazlasiyla finanse eder ama HEKIS cok kucuk kalir. Luks tahsilati %40 varsayimi, gelirin buyuk kismi ona bagli.

Fazla gelir geri donusu (`hekis.zones.solve_premium`): bedel gelirinin sub. ustunde kalan fazlasi katilim primine (katilan sahibe yillik, degerin yuzdesi) gider; butce dengeli en buyuk prim, katilim tavanina ulasinca durur. Temel: 37 bin -> 43 bin daire, prim %4,7, 4,8 mr/yil, kalan fazla 0. Tampon bedelsiz: 37 -> 41 bin, prim %3,2. Luks %40: 28 -> 34 bin, prim %12,7, kalan fazla 1,1 mr. Luks %60: 18 -> 23 bin, kalan fazla 11,7 mr bosa kalir. Sinir tavandir (kullanima uygun stok payi %25): para tavani asan daireyi satin alamaz. Kalan fazla tavani %25'ten %40'a cikaracak tadilata gitse, luks %60'ta daire basina yilda yaklasik 850 bin TL butce olur (tadilat maliyeti verisi yok).

### 7b-5. Fiziki durum: kentsel donusum, duran insaat, tadilat (uc ayri kategori)

`data/DURAN_YAPI.md`, `python -m hekis.stalled`. Kentsel donusum (Istanbul'da ~1,5 milyon saglıksiz birim, ~600 bin agir hasar riski, 2012'den beri ~900 bin bagimsiz bolum donustu) ve tadilat (bos konutun onarimi, veri yok) modelin disindadir. Duran insaat HEKIS'e entegre edilir. Sektor iddiasi ~100 bin yarim kalan konut (Fi Yapi ~8.500, Innova ~4.500), resmi sayi degil; baz olarak 30 bin alinir (karar: iddianin ucte biri). 2026 yapi yaklasik birim maliyeti apartman tipi ~19.800-33.900 TL/m2 (KDV haric, aktarim). Mekanizma varsayimi: havuz tamamlama bedelini oder, daire kiralanir, net kira bedeli geri oder, mulkiyet alici-sahipte kalir; havuzun sermayesi dairenin degeri degil tamamlama bedelidir.

Orta durum (kalan %20, 26.000 TL/m2, 100 m2): daire basina 520.000 TL, Esenyurt tipi dairenin yillik net kirasi 152 bin TL, geri odeme 3,4 yil, degerin %22'si. Kalan pay %10-30 ve birim maliyet 19.800-33.900 iken bedel 198 bin ile 1,02 milyon TL, geri odeme 1,3 ile 6,7 yil. Havuz sermayesi mevcut bos stoga gore 4,6 kat daha az.

Baz (30 bin duran konut, %50 tamamlanabilir, %41 HEKIS bandi): 6.112 daire, 3,2 mr TL sermaye, 0,64 mr TL/yil sub. Mevcut bos stokla (36.963 daire, 3,92 mr sub.) toplam 43.076 daire, 4,56 mr TL/yil sub., uygun kiracinin %7,7'si (mevcut stok tek basina %6,6). Duyarlilik: tum 30 bin tamamlanir ve hepsi HEKIS bandina girerse 30 bin daire, 15,6 mr sermaye, 3,2 mr/yil sub. (mevcut stok sonucunun 0,8 kati). Sektor iddiasi 100 bin cikarsa her sey 3,3 katina cikar. Yasal sahiplik, yapi guvenligi, tapu ve kentsel donusum projeleriyle cakisma hesapta yok.

## 7c. Istanbul ve 7 buyuksehir (simdilik kapsam disi, ayri calisma)

`python -m hekis.cities`. Sehirler: Istanbul, Ankara, Izmir, Bursa, Antalya, Konya, Adana, Kocaeli (TUIK 2025 konut satisi siralamasi; Gaziantep, Mersin, Sanliurfa bu aramada gorulmedi, siralama tam dogrulanmadi). Nufus TUIK ADNKS 2025: 39,0 mn, Turkiye'nin %45'i. Fiyat ve kira carpani Istanbul'a gore ortalama satis ve kira orani (Emlakjet-Endeksa Agustos 2026): Ankara 0,70 / 0,76, Izmir 0,89 / 0,73, Antalya 0,83 / 0,64, Bursa 0,64 / 0,53. Kocaeli, Konya, Adana icin veri yok, Bursa degerleri yer tutucu. Bos stok kisi basi Istanbul ile ayni (450 bin / 15,75 mn), hane buyuklugu 3,08, kiraci payi %27, gelir dagilimi ulusal: hepsi varsayim. Beklenen reel artis sehir bazinda KFE'ye Endeksa'nin sehir-Turkiye reel farki eklenir (Istanbul -%3,7, Ankara -%2,8, Kocaeli -%3,2, Antalya -%5,3, digerleri -%6,5).

En olasi senaryo (tavan %25, bedel %1, tahsilat %30, luks bedel %5): 8 sehirde 210 bin daire (Istanbul 82 bin, %39), yil 1 sub. 11,0 mr TL (Istanbul %59), bedel 12,6 mr, oran 1,14, 20 yil yuk 232 mr. Istanbul tek basina oran 0,94, acik 0,39 mr: diger sehirlerde kira farki kucuk (ulusal sosyal kira 10-12 bin yerel piyasa kirasina yakin), abonelik sub. baskin ve bedel tabani genis, o yuzden oran 1,18-1,80.

Etki (8 sehir nufusu, 12,7 mn hane, 3,4 mn kiraci hane): 210 bin hane (uygun alt %40 kiracinin %15'i), hane basina ayda 4.368 TL. Gini 0,4296 -> 0,4289, goreli yoksulluk -0,18 puan. Kira piyasasi etkisi dogrusal yaklasimla %-6 ile %-20, ust sinirdir: yerlesenlerin piyasa kiracisi olduklari ve esnekligin dusuk oldugu varsayilir.

## Sonuc

Model, bos stoku kullandirmanin maliyetini kira farkindan ve abonelikten ibaret gosteriyor, stoku kullandirmanin kendisi bedava. Kendini finanse etme olcek meselesi: kucuk programlar finanse eder, buyukler etmez. Yon sonuclari sagdir (ters dongululuk, olcek erozyonu, bedelin katilimi artirmada zayifligi), buyukluk sonuclari degildir (katilim, tahsilat ve beklenti kalibre edilemez).

## Sinir

Katilim orani gozlem degil, kalibre edilmemis en onemli girdidir. Tadilat, kiraci bulma gecikmesi, dairenin oturulabilir olup olmadigi, bakim orani Turkiye verisi, hane sayisi, 2024-2026 gelir artisi ve etkin tahsilat yok veya varsayimdir. Esenyurt satis fiyati gozlem degil, turetilmistir. Ulusal %27 bos stok ile %3,7 elektrik boslugu ayni sey degil. Fiziki uretim endeksi hala disaridan. Model yeni konut istahini kapatmaz, kacinma tek bir parametreyle temsil edilir, hukuki cerceve (bedelin vergi mi harc mi oldugu, anayasal sinir) hic modellenmedi.
