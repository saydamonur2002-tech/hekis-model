# Yaptirim kanun taslagi

Bu metin yururluk taslagi degil. Modeldeki karar kuralinin madde iskeleti. Oranlar gozlem degil, esik. Finansal sistem ve senet bu metne girmez.

## Amac

Mevcut konut rezervini isler kilmak. Bitmemis insaati bitirtmek. Duran tamamlanmis stoku sisteme almak. Sermayeyi konutun satis fiyatinda tutmamak.

## Kapsam

Turkiye sinirlari icindeki bagimsiz bolumler. Birincil konut, ikinci konut, ucuncu ve sonraki konut ayri rejim. Insaat halinde stok ayri rejim.

## Tanimlar

Birincil konut: malikin veya esinin adreste fiilen oturdugu tek bagimsiz bolum.
Ikinci konut: birincil disindaki ilk bolum.
Ucuncu ve sonrasi: ayni gercek veya tuzel kisinin, es ve kontrol ettigi sirketlerle birlikte sayilan ucuncu bolumden itibaren her birim.
Duran stok: iskani olup son on iki ayda oturulmayan veya kiralanmayan bolum.
Bitmemis stok: iskani olmayan, yapi kayit veya kaba insaat asamasi dahil bolum.
Havuz teklifi: sistemin alis bedeli. Piyasa fiyati vermek zorunda degil.
Hasilat donusu: satis bedelinin sistem senedine yazilmasi. Daire, doviz, altin ve fon sayilmaz.

## Rejim

1. Birincil konut bos tutma bedelinden muaf. Oturma belgesi yoksa muafiyet dusur.
2. Ikinci konut yillik binde 2. Bu oran modelde stok getirmez. Yerinde birakilirsa semboliktir.
3. Ucuncu ve sonraki duran her birim icin yillik bedel, beyan edilen satis degerinin yuzde 4'u. Modelde havuz piyasanin yuzde 80'ini verdiginde bes yilda satis karari ureten esik budur. Yuzde 2 yetmez, on yil dayanir.
4. Bedel bos ay uzerinden hesaplanir. Yil icinde oturulursa veya sisteme girerse kalan ay dusulur.
5. Bitmemis stok satis tesviki alamaz. Iskan alinmadan teminat, ipotek devri ve satis vaadi gosterilemez. Bitirme suresi ruhsat yasina gore ayri yonetmelik.
6. Satis hasilati ancak sisteme donerse gelir vergisinden istisna edilir. Baska varliga donen hasilat istisna disidir ve artan oranli vergilendirilir.
7. Havuz teklifini reddetmek serbest. Ret, bos tutma bedelini durdurmaz.
8. Kira indirimi bu kanunun konusu degil. Oturan faturasi ile havuz nakdi ayri satirdir. Indirim havuzdan kesilemez.

## Beyan

Malik, es ve kontrol edilen sirketlerdeki bolumleri tek bildirimde sayar. Bildirmeyen ucuncu ve sonrasi rejimine yuksek dilimden girer. Deger, belediye rayicinden az olamaz. Rayic ile ilan ortalamasi arasinda sistem ilan ortalamasini esas alir.

## Gecis

Ilk yil oranin yarisi. Ikinci yildan itibaren tam oran. Yarim ilk yil satis suresini 5,0'dan 5,5 yila uzatir (`hekis/blokaj.py`). Bitmemis stok icin on sekiz ay tamamlama suresi. Sure dolunca teminat yasagi dogrudan uygulanir.

## Uygulama blokaji

Bu blok yururluk maddesi degil. `hekis/blokaj.py` modelinin bulgusundan cikan madde iskeleti. Tez: merkez resmen toplanir, fiilen dagilir. Yetki ve imza yukaridadir, tahakkuk kararini hizip konumundaki aktorlerin sahasi belirler. Denetim kaydi olayi bilir, yaptirima cevrilemez. Suc ust baglantiyla kapanir, mevzuat gerekcesi uretilir, fatura alt kademeye ve devlet bilancosuna yazilir. Oranlar gozlem degil, esik. Hizip payi, tespit orani ve kapanma orani veriden olculmedi.

Modelin bulgulari:

1. Yuzde 4 esigi sifir sizintiyla kurulmus. Gecis yarim yili dahil edince sifir sizintida satis 5,5 yil, tespit yuzde 90 ise ortalama yolda 6,1 yil. Madde 3'teki "bes yil" yalniz kusursuz uygulamada tutar.
2. Kapanma yillik tespit gibi kismi degil, kalicidir. Kapanan dosya bedelin bir kismini degil, hic odemez. Beklenti hesabi bunu ortalama gosterir (hizip icin 9,8 yil), gercekte iki mod vardir: acik dosya normal yilda satar, kapali dosya hic satmaz.
3. Hizip payi yuzde 30, kapanma yuzde 40 alininca stok cikisi yuzde 88'den yuzde 78'e iner. Hizip baglantili birimlerde yuzde 52'de kalir, siradan malikte yuzde 89. Toplam bedelin yuzde 80'ini siradan malik oder, oysa birimlerin yuzde 70'i siradandir. Kanun hizip disi stogu tasir, hizip stogunu yerinde birakir. Amac duran stogu isler kilmakti, sonuc ters secim.
4. Uc kapi ayni cikti verir: yasal bosluk (l), siyasi hat (b), ele gecirilmis organ (c). Cikti kapiyi ayirt etmez, cozum ayirt eder. Yalniz yazim duzeltmesi yalniz l'ye bakar. Otomatik tahakkuk b'ye bakar. Tahakkuk hattinin disindaki kurumun veri eslesmesi c'ye bakar. Yanlis teshis bosa gitmekle kalmaz: otomatik tahakkuk organ ele gecirilmisse, dis veri yasal bosluktaysa stok cikisi yuzde 78'in altina duser, cunku onlem yeni bir muafiyet kapisi (m) acar.

Madde iskeleti:

9. Bedel idari takdire bagli degil. Tahakkuk veri eslesmesiyle kendiliginden olur. Madde 3 ve 4'teki oran ve bos ay hesabi formuldur, karar degil.
10. Tahakkuku durduran, erteleyen veya kapatan her islem gerekcesiyle kamuya acik sicile yazilir. Kapatma gerekceleri kapali listedir. Listede olmayan gerekce hukuki sonuc dogurmaz.
11. Tapu ile elektrik ve su abonelik verisinin eslestirilmesi tahakkuk hattinin disindaki kurumca yapilir. Bu kurum tahakkuk karari vermez, yalniz eslesme listesi uretir.
12. Tahakkuku durduran islemde sorumluluk imza sahibindedir. Alt kademe yazili talimata dayansa da tek basina sorumlu tutulamaz. Talimat sicile girmemisse sorumluluk talimat verene gecer.
13. Muafiyet belgesi (oturma) tek kurumdan alinmaz, elektrik tuketim esigiyle capraz dogrulanir. Capraz dogrulamayi gecemeyen belge muafiyet saglamaz.

Kapiyi ayirt eden gozlem. Bu tabloyu model degil kayit doldurur:

| Gozlem | Hangi kapi |
| --- | --- |
| Kapatma gerekcesi mevzuata atif yapar ve ayni gerekce hizip disi dosyada da ayni sonucu verir | l, yasal bosluk |
| Kapatma sikligi malikin kimligine veya siyasi hatta gore degisir, iktidar degisince ters doner | b, siyasi hat |
| Dosya denetim kaydina hic girmez, denetim biriminin atamalari ayni hattan gelir | c, ele gecirilmis organ |

Kanit sirasi onemli. Ucuncusunu kanitlamadan birinciyi ve ikinciyi elemek tezi kapali devreye sokar: kapanan her dosya tezi dogrular, acilan dosya istisna sayilir. Madde 10 sicili bu yuzden gerekli: sicil olmadan uc kapiyi ayirmanin verisi yok.

Modelin kendi sinirlari. Hizip bir parametredir, kimlik degil: kimin hizip baglantili sayilacagini model vermez, bunu tanimlayan kanun metni de bir kapidir. Onlem carpanlari varsayim. Otomatiklesme siyasi takdiri kaldirmaz, onu veriyi ureten kuruma tasir (m). Madde 11 ve 13 bu kaymayi daraltir, kapatmaz. Tek mekanizma anlatisi tehlikelidir: bazi dosyalarda denetim gercekten bilmez (tespit d dusuk, kapanma degil), bazi dosyalarda alt kademe saf gunah kecisi degil rantin ortagidir, bazi dosyada ust hat kapatamaz cunku dosya baska hizbin elindedir. Rakip hizipler birbirini denetlerse bu denetim degil klikler arasi pazarliktir, modelde bu durum yok. Yaptirim tekelini merkez secici kullaniyorsa model pasifligi kanitlamaz: edilgenlik bagimlilik kurma teknigi de olabilir, bu durumda kayip devlet bilancosunda gorunur, kazanc hizbin konumunda birikir. Bu ayrimi model ayirmaz.

## Sinir

Bu metin mubadele, el koyma veya kamulastirma degil. Teklif reddedilebilir. Bedel, farki kapatmayan oranda sembolik kalir. Anayasa madde 35 ve 73 sinavi ayri. Yuzde 4 yillik bedel, degerin hizla erimesi gerekcesiyle oran disi bulunabilir. O sinav bu taslagin yerine gecmez.

## Model bagi

Esenyurt ortalama 3.619.875 TL. Havuz yuzde 80 teklif, fark 723.975 TL. Yuzde 4 yillik bedel yaklasik 144.800 TL. Fark bes yilda kapanir. Bu hesap `hekis/owner.py` kuraliyla ayni. Oran gozlem degil.
