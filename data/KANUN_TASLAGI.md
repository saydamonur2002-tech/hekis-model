# Yaptirim kanun taslagi (guncel model orani)

Bu metin yururluk taslagi degil. Modeldeki karar kuralinin madde iskeleti. Oranlar gozlem degil, esik; model sonucuna ve varsayimlara bagli. Finansal sistem ve senet bu metne girmez. Surum: 2026-10-05 (ikinci duzeltme: kademeli yururluk, kapi esikleri, ayrilabilirlik, sok hukumleri), Istanbul. Anadolu buyuksehirleri icin ayri tarife: `data/ANADOLU_TARIFE.md`. Onceki surum git gecmisinde (%4 tek oranli ucuncu konut rejimi); model onu desteklemedi.

## Amac

Mevcut konut rezervini isler kilmak. Duran, yarim kalmis insaati tamamlayarak sisteme almak. Sermayeyi konutun satis fiyatinda tutmamak. Bos tutmanin maliyetini bos tutana yuklemek.

## Kapsam

Istanbul'daki bagimsiz bolumler. Kapsam disi: kentsel donusum (riskli yapi yenileme) ve tadilat, ikisi ayri sistemdir. Duran insaat HEKIS'e entegre edilir ama kentsel donusum projesi icindeki duran yapi bu madde kapsamina girmez, cifte sayilmaz.

## Tanimlar

Birincil konut: malikin veya esinin adreste fiilen oturdugu tek bagimsiz bolum.
Bos konut: son on iki ayda elektrik aboneligi tuketimi esik altinda kalan ve oturulmadigi, kiralanmadigi tespit edilen bagimsiz bolum. Esik EPDK dagitim verisiyle yonetmelikte belirlenir (bu taslak rakam vermez).
Deger bandi: sehirdeki bos konutlarin beyan edilen ve belediye rayicinden dusuk olmayan degerine gore siralamasi. Alt %41 HEKIS bandi, %41-80 tampon (memur kesimi), ust %20 luks. Yuzdeler Istanbul icindir. HEKIS bandinin siniri, hane geliri duz memur (13/1) maasinin altinda kalan hanelerin gelir dagilimindaki payidir, maas degisince yeniden hesaplanir.
Duran stok: iskani olup tespit kosuluna uyan bolum. Bitmemis stok: iskani olmayan, yapi kayit veya kaba insaat asamasindaki bolum.
Havuz teklifi: sistemin sahibe senet karsiligi odedigi kira esasli deger. Piyasa degeri vermek zorunda degil.
Hasilat donusu: satis bedelinin sistem senedine yazilmasi. Daire, doviz, altin ve fon sayilmaz.

## Rejim

1. Birincil konut bos tutma bedelinden muaf. Oturma belgesi yoksa muafiyet dusur.
2. Genel bedel: bos konut icin yillik, beyan degerinin yuzde 1'i. HEKIS bandi ve tampon icin gecerli. Bu oran model icin en olasi senaryoda bosluk tepkisini (yaklasik %29 bosluktan cikis) ve boslugu piyasaya doner kilma etkisini birlikte verir.
3. Luks bedel: luks bandindaki bos konut icin yillik yuzde 5. Yuzde 5'in ustu denenmemis ve kacinma riski yuksek; model luks bedel gelirinin yaklasik yuzde 8 civarinda tepe yaptigini ve sonra kacinmayla dustugunu gosterir. Oran sahibin konut sayisina bakmaz.
4. Sahip sayisi carpani (SECENEK, test edilmedi): ayni gercek veya tuzel kisinin ucuncu ve sonraki bos birimleri icin bedel carpani. Modelde sahip sayisi yok. Eski surumdeki yuzde 4 tek oran buna dayanmiyordu ve kaldirildi.
5. Bedel bos ay uzerinden hesaplanir. Yil icinde oturulur, kiralanir veya sisteme girerse kalan ay dusulur.
6. Muafiyet: tadilat, miras sureci, sahibin hastaligi, satisa veya kiraya cikarilmis bolum, sinirli sureyle. Muafiyet talebi belgeye baglidir. (Irlanda'da isaretlenen 50 bin konuttan yaklasik 2 bini muafiyet aldi, 972'si yapi isi, 256'si hastalik.)
7. Bitmemis stok icin tamamlama mekanizmasi: kentsel donusum disindaki duran yapilarin ruhsat yasi, hak sahipligi ve yapi guvenligi tespitinden sonra tamamlanmasi, tamamlama bedelinin kiradan geri odenmesi ve mulkiyetin alici-sahipte kalmasi. Tamamlanana kadar satis tesviki, teminat ve ipotek devri yok. Yapi guvenligi tespiti sart; basarisiz olan yapi kentsel donusume duser.
8. Satis hasilati ancak sisteme donerse gelir vergisinden istisna edilir. Baska varliga donen hasilat istisna disidir ve artan oranli vergilendirilir.
9. Havuz teklifini reddetmek serbest. Ret, bedeli durdurmaz. Teklifin kirasi piyasa kirasinin yuzde 80'inin altina inmez (altinda anapara 20 yilda tamamen odenmez, sahip icin kayip).
10. Bedel geliri once subvansiyona gider. Fazla gelir katilim primi olarak sahibe odenmez (model: prim katilimi yalniz %16-28 artirir, tavana carpar). Fazla gelir tavani artiran tadilat ve duran insaat tamamlamaya gider.
11. Oturanin odemesi, abonelik destegi ve kira indirimi ayri duzenleme. Model varsayimi: oturan piyasa kirasi ile gelirinin yuzde 30'unun kucugunu oder, abonelik devletce karsilanir, uygun kitle geliri duz memur maasinin altindaki haneler. Bu maddeler bu kanunun konusu degil ama bedel gelirinin harcama yeri bunlardir.

## Beyan ve tespit

Malik, es ve kontrol edilen sirketlerdeki bolumleri tek bildirimde sayar. Bos konut tespiti beyana birakilmaz: elektrik abonelik tuketim verisi ve adres kayit sistemi belediye ve dagitim sirketince capraz kontrol edilir. Deger, belediye rayicinden az olamaz. Rayic ile ilan ortalamasi arasinda sistem ilan ortalamasini esas alir. Bedel emlak vergisiyle birlikte belediyece tahsil edilir, odenmeyen bedel icin tapuya serh ve haciz.

## Kademeli yururluk ve kapi

Kanun bir anda tum sehre degil, olcum kapisiyla kademeli uygulanir. Model bunu gerektiriyor: sistemin finansmani luks bedel tahsilatina dayanir ve bu tahsilat hicbir yerde olculmedi.

1. Birinci yil pilot: secilen mahallelerde toplam yaklasik 3.800 bos birim (luks bolgede yaklasik 290 vergilendirilen birim; luks tahsilati olcmek icin gerekli en kucuk buyukluk, +-4,6 puan hassasiyet). Ilk yil bedel oranin yarisi.
2. Her yil sonunda olcum. Esikler tutarsa bir sonraki yil kapsam en fazla 2,5 kati buyur (3.800, 9.500, 23.750, 59.375, 148.000, 371.000, tum Istanbul 450.000; model: tam olcege 7. yilda ulasilir).
3. Kapi esikleri (tamami tutmalidir, olculen deger kullanilir; olcum hatasi payi eklenmistir):
   a. Katilim: uygun birimin yuzde 15 ile yuzde 38'i arasi (alt: amac; ust: ustunde sub. bedel gelirini asar).
   b. Genel bedel tahsilati en az yuzde 20; luks bedel tahsilati genel tahsilata bagli: genel yuzde 30 ise en az yuzde 18, yuzde 20 ise en az yuzde 23, yuzde 10 ise en az yuzde 29.
   c. Oturan odeme tahsilati en az yuzde 80; olculen hane geliri varsayilan gelir olcegi yuzde 85'inin altina dusmemeli.
   d. Bedel geliri / yillik subvansiyon, olculen degerlerle, en az 1,25.
4. Kapi tutmazsa kapsam genisletilmez, yeni yerlestirme durdurulur. Yerlesmis haneler korunur (cikarilmaz), bunun maliyeti mevcut hane kadardir.
5. Kapi verisi bagimsiz kurumca yayimlanir. Esikleri ve ayrintiyi yonetmelik belirler; bu taslak rakamlari baslangic degeri olarak verir, kanunlastirmaz.
6. Bitmemis stok icin on sekiz ay tamamlama suresi. Sure dolunca teminat yasagi dogrudan uygulanir.

## Ayrilabilirlik ve sok hukumleri

- Luks bedel ayri madde, ayri hukum. Luks bedelin iptali halinde genel bedel, katilim ve yerlestirme hukumleri yururlukte kalir (model: yalniz luks bedel iptali, tum bedelin iptali kadar zararlidir; zarar eden varyant %41 ile %74).
- Bedelin tamamen iptali halinde (en kotu hukuki sok): yeni yerlestirme otomatik durur, yerlesmis haneler korunur, mevcut sozlesmeler kira artis kuralina baglidir. Kademeli yururluk bu riski azaltir: 3. yilda iptal olursa yuk yaklasik 4 mr TL (20 yil), tam olcekte ise yaklasik 84 mr TL.
- Katilim guvencesi yok: beklenen reel konut artisi bugunkunden yaklasik 4 puan yukselirse katilim yuzde 15'in altina duser ve kapi genislemeyi durdurur. Bu hata degil, tasarimdir.

## Sinir

Bu metin mubadele, el koyma veya kamulastirma degil. Teklif reddedilebilir. Anayasa madde 35 ve 73 sinavi ayri. Yillik yuzde 5 luks bedel orantililik ve olcululuk itirazina acik; bedelin vergi mi harc mi oldugu tanimlanmadi. Etkin tahsilat model icin en zayif girdi: Irlanda'da isaretlenenin yaklasik yuzde 6'si bedele tabi kaldi, model Istanbul icin yuzde 30-40 varsayiyor. Oran gozlem degil.

## Model bagi

En olasi senaryo, Istanbul (`hekis/zones.py`, `hekis/final.py`, `hekis/horizon.py`, `hekis/social.py`): bos stok 450 bin (225-750 bin arasi tahmin), HEKIS bandi 183 bin, tampon 177 bin, luks 90 bin. Katilim tavani %25. Erozyonsuz tam olcek: yerlesen 37 bin (bos stok) ve duran insaattan yaklasik 6 bin; sub. 3,9 + 0,64 mr TL; bedel 9,4 mr TL. Olcek erozyonu varsayimiyla (tahsilat tam olcekte %25 azalir; veri yok) bedel 7,0 mr TL, oran 1,79. Kademeli yoldan tam olcege 7. yilda ulasilir; 10 yilda kumulatif net yaklasik +17 mr TL.
Etki kucuk: tam olcekte Gini -0,0007, goreli yoksulluk -0,16 puan, Istanbul kirasi yaklasik -%4,5 (esneklik 0,6; dogrulanmadi), yerel TUFE -0,3 puan, ulusal TUFE yaklasik -0,05 puan.
Sistemin finansmani luks bedele dayanir (gelirin yaklasik 6,5 mr TL'si), bu yuzden luks tahsilati kritik ve kademeli kapi onu olcmek icin tasarlandi. Sok testleri (150-300 cekim, duzeltilmis): bedel iptali yilinda yaklasik %60-65 cekimde 5 yil net negatif; agir krizde yaklasik %10; ralli ve gelir sokunda kapi genislemeyi durdurur. Belirsiz degerlerle yaklasik %40 cekimde kapi pilotta hic gecmez (katilim %15 altinda), yaklasik %50'sinde 7. yilda tam olcege ulasilir.
Dogrulanmayan: etkin tahsilat (%30/%40), erozyon (%25), kira esnekligi, duran insaat sayisi (30 bin), bos stok. Pilot verisi gelmeden bu metin hipotez.
