# Mikro pilot ve kademeli genişleme

Çalıştır: `python -m hekis.pilot` (kod: `hekis/pilot.py`, 2 test `PilotTests`).
Kapsam: tek mahalle, 1.000 boş birim, İstanbul en olası senaryo. Senet, duran inşaat, Anadolu yok.

## Çıktı (model)
| kademe | yerleşen | kapsam | bedel/sub | not |
|---|---|---|---|---|
| K0 yalnız havuz | 78 | %19 | 0 | bedel yok, sub. karşılanmaz |
| K1 + genel bedel %1 | 82 | %20 | 0,72 | tek başına kendini finanse etmez |
| K2 + lüks %5 | 82 | %20 | 2,39 | finansmanı lüks bedel taşır |
| K3 + hedef primi | 95 | %23 | 2,06 | prim %4,66/yıl |

Ölçek: mahalle 82, ilçe (20 bin) 1.643, İstanbul 36.963 yerleşen; oran her yerde 2,39.

## Dürüst not
Ölçek değişmezliği modelin doğrusal olmasından gelir, kanıt değildir. Gerçek ölçek etkisini (tahsilat erozyonu, katılım doygunluğu) yalnız pilot verisi gösterir. Testler model tutarlılığını sınar; gerçeklik testi değildir.

## Kademe geçiş eşikleri (revize: modelden türetilmiş)
Eski eşikler (%15 / %25 / %30 / %30 / %90) dayanaksızdı; model çıktısının biraz altı olarak seçilmişti. Yeni kural: bedel/sub oranını ≥1,25'e (tespit, tahsil, idari maliyet modelde yok; %25 pay, karar) taşıyan en küçük değer; ölçüm hatası (%95 GA) üstüne eklenir. Kod: `pilot.gates()`.

| Ölçüm | Eski | Yeni | Dayanak |
|---|---|---|---|
| Katılım (uygun birim) | ≥%15 | %15-38 | alt: amaç (karar); üst: %38 üstünde sub. bedeli aşar |
| Genel bedel tahsilatı | ≥%25 | ≥%20 | lüks tahsilatla birlikte okunur (aşağı) |
| Lüks bedel tahsilatı | ≥%30 | ≥%18 (genel %20 ise) | sınır eğrisi: genel %30→lüks %13, %20→%18, %10→%24 |
| Kiracı ödeme/kira | ≤%30 | ≤%30 (tasarım) | değişmedi |
| Kiracı tahsilat | ≥%90 | finansal taban %38; operasyonel ≥%80 (karar) | %90 finansal değil, tahmindi |

Bulgular:
- Genel ve lüks tahsilat birbirinin yerine geçiyor; tek tek eşik yerine eğri. Lüksün yüksek olması genelin düşüklüğünü kapatır. Genel bedel tek başına (lüks yok) ancak %42 tahsilatla yeter: gerçekçi değil.
- Modelde %10 tahsilat tabanı vardı (AVOID_FLOOR, artık 0): tahsilat 0'da bile oran >1 görünüyordu, yani kendi kendini finanse etme sonucu varsayımla korunuyordu. Eşikler tabansız hesaplandı. Ana modelden de kaldırıldı (onay üzerine); hiçbir sonucu değiştirmedi.
- Mikro pilot lüks tahsilatını ölçemez: 1.000 birimde ~77 lüks vergilendirilen birim var, hata ±9 puan. ±5 puan için ~4.000 birim gerekir. Katılım (407 uygun birim, ±3,9) ölçülür.

## Dış çapa: 2024 tasarruf finansman (benzetme yok)
`python -m hekis.anchor`. Sistem yalnız ölçek ve talep için dış kontrol; HEKİS tasarımı o sisteme benzemez (o: üye birikimi, sıra/çekiliş; HEKİS: boş stoğu havuza alan kira sistemi). Veri haber özetlerinden, doğrulanmamış; konut/taşıt ayrımı yok; baz yıl 2024, model 2026.
- 2024: sözleşme 498 mr TL, müşteri 630 bin, aktif 92 mr TL → müşteri başı ≈790 bin TL. HEKİS havuz birimi 2,41 mn TL; sözleşme birim değerin bir kısmı.
- HEKİS 36,9 bin hane = sistemin müşterisinin %5,9'u.
- Sistem aktifi mevduatın %0,29'u, senet %0,28'i (senet/aktif 0,97). En hızlı büyüyen 2024 kanalı bile mevduatın ~%0,3'ünü çekti: dolarizasyon kapasitesi ≈0 sonucuyla uyumlu.
- Sınır: müşteri tasarruf eden orta gelir, HEKİS'in uygun kiracısı (düz memur maaşı altı) başka nüfus. Talep kanıtı değil. Pilotun "kapsam" sütunu havuz stokunun katılımı; anchor'daki kapsam uygun kiracıya oranı (%6,6), ikisi aynı şey değil.

## Genişletilmiş lüks pilotu (karar)
Lüks tahsilatı mahalle pilotunda ölçülemediği için pilot ≈3.800 birime çıkarılır (`pilot.lux_pilot_size()`): lüks ölçüm hatası ±4,6 puan (1.000 birimde ±9), genel ±1,6, katılım ±2,0. Lüks bölgede ≈290 vergilendirilen birim.
Geçiş kuralı (okunan değer): genel tahsilat %30 ise lüks ≥%18 (13+4,6); %20 ise ≥%23; %10 ise ≥%29. Eşiğin altında kalırsa K3'e (hedef primi) geçilmez; ilk iş lüks bedel tahsilat yolu (tespit, yaptırım) düzeltilir.
Not: hata hesabı bağımsız birim varsayar; aynı sahibin birden fazla birimi, aynı mahallede kümelenme hatayı büyütür.

## 5 yıllık kademeli genişleme, ölçek erozyonu, şok direnci (`python -m hekis.horizon`)
Kurgu: 3.800 birimle başlar; her yıl ölçüm, eşik tutarsa ertesi yıl ölçek ×2,5 (tavan 450.000). Eşik: ölçülen tahsilatlarla oran ≥1,25, ölçülen katılım %15-38; tutmazsa dondurulur. Ölçek erozyonu (VARSAYIM, veri yok): tahsilat 3.800→450.000 arasında log ölçekte %25 düşer. Şok 3. yıldan itibaren. 300 çekim.

Önceki varsayımla (erozyon yok, büyüme sınırı yok) yerleşen: 312 / 1.249 / 4.994 / 19.977 / 36.963. Erozyon ve ×2,5 tavanıyla: 312 / 780 / 1.951 / 4.877 / 12.193; 5. yılda ölçek 148 bin (tüm İstanbul'a ulaşılmaz), 5 yıl net +2,1 mr TL (öncekinin +12,4'ü şişkindi). Oran 2,39'dan 1,93'e iner.
Erozyon duyarlılığı (0/25/50): 5. yıl yerleşen 11,9 / 11,7 / 11,0 bin, net 3,1 / 2,2 / 1,3 mr; %17 pilotta takılır.

Şok direnci (5. yıl medyan; zarar % = 5 yıl net negatif):
| şok | ölçek | yerleşen | net mr | zarar | oran<1 |
|---|---|---|---|---|---|
| yok | 148 bin | 11,7 bin | 2,2 | 0% | 0% |
| fiyat rallisi (g_e +10 puan) | 23,7 bin | 430 | 1,5 | 0% | 0% |
| lüks tahsilat çöküşü (×0,4) | 23,7 bin | 3,3 bin | 0,4 | 5% | 11% |
| genel tahsilat çöküşü (×0,5) | 148 bin | 11,1 bin | 1,5 | 0% | 0% |
| hane geliri −%30 | 148 bin | 10,5 bin | 1,5 | 0% | 2% |
| kombine (ralli + lüks ×0,5) | 23,7 bin | 430 | 1,0 | 0% | 0% |

Okuma: sistem finansal olarak şoka dirençli (kapı büyümeyi durdurur, zarar sınırlı) ama küçülerek: fiyat rallisinde katılım %15'in altına iner (+4,1 puan yeter), program 430 haneye kalır. Yani zayıflık finansal değil, ölçek: beklenen fiyat artışı dönerse sistem boşalır. Finansal kırılma noktası lüks tahsilat (en olası değerin ×0,17'si, yani %7); genel tahsilat tek başına kırmaz, lüks yerindeyse sıfıra inse bile.
Eklenen şoklar (3. yıldan itibaren):
| şok | ölçek | yerleşen | 5y net mr | zarar | 20y yük (5. yıl ölçeğinde, mr) |
|---|---|---|---|---|---|
| enflasyon +10 puan | 148 bin | 11,7 bin | 2,2 | 0% | 25,7 (şoksuz 26,6) |
| kur şoku (enf +10, maliyet ×1,3) | 148 bin | 11,8 bin | 2,1 | 0% | 27,2 |
| bedel iptali (hukuki, gelir 0) | 23,7 bin | 1,9 bin | −0,4 | %78 | 4,3 (yıllık açık +0,2 mr) |

Okuma: enflasyon sistemi bozmuyor, hatta yükü hafif düşürüyor: kira ve anapara TÜFE endeksli, tasarım nötr. Bu iyi haber olmayabilir: modelde oturanın geliri endekslenmiyor, ödeme gücü erimesi (kiracı tahsilatı) ölçülmedi. Kur şoku yalnız enflasyon + maliyet vekiliyle modellendi (yük +%2); sermaye çıkışı, dolarizasyon, senet etkisi yok. Bedel iptali en sert şok: %78'de 5 yıl net negatif; ama kapı iptalden sonra büyümeyi durdurduğu için kayıp küçük (medyan −0,4 mr, 20 yıl yük 4,3 mr). Aynı iptal tam ölçekte (450 bin) gelseydi bedel geliri (9,4 mr/yıl) kaybolur, 20 yıl sübvansiyon yükü ≈84 mr TL reel olurdu: kademeli büyümenin asıl değeri bu risk farkı (≈20 kat). Yerleşmiş hanelerin çıkarılamayacağı varsayıldı.
Eklenen şoklar (hepsi 3. yıldan itibaren; 5. yıl medyan):
| şok | ölçek | yerleşen | 5y net mr | zarar | 20y yük mr |
|---|---|---|---|---|---|
| kısmi iptal (yalnız lüks bedel) | 23,7 bin | 1,9 bin | +0,1 | %37 | 4,4 |
| gelir erimesi (hane −%20, kiracı tahsilat ×0,8) | 148 bin | 10,2 bin | 1,3 | %2 | 32,4 |
| kur krizi + sermaye çıkışı (enf +10, maliyet ×1,3, g_e +10, lüks ×0,7) | 23,7 bin | 446 | 1,2 | %0 | 1,0 |
| ağır kriz (ralli + lüks iptali + gelir erimesi) | 23,7 bin | 430 | 0,3 | %12 | 1,4 |

Okuma: (1) Yalnız lüks bedelin iptali neredeyse tüm bedelin iptali kadar zararlı (%37 vs %78 çekimde zarar): sistemin finansmanı lüks bedele dayanıyor, hukuki risk de orada yoğun. (2) Gelir erimesi kapıyı geçiyor ve büyümeye devam ediyor, çünkü kapı kiracı tahsilatını ölçmüyor; 20 yıl yükü %22 artıyor (26,6 → 32,4). Bu bir tasarım açığı: kapıya kiracı tahsilat/gelir ölçümü eklenmeli. (3) Kur krizi + sermaye çıkışı finansal zarar vermez (program küçülür, 446 haneye iner): ralli katılımı çökertir. (4) Ağır kriz tek başına en kötü durum: %12 zarar, program 430 hane; kapı sayesinde yük 1,4 mr ile sınırlı.
Varsayımlar: kur krizi ve sermaye çıkışı kurulmuş bir model değil, parametre vekili (g_e +10 puan = TL'de konutun reel savunma değeri). Kısmi iptal binary (lüks ×0). Gelir erimesi tek seferlik düzey şoku, yıllık erime değil.
Sınırlar: erozyon oranı varsayım; şokta geri çekilme/küçülme kuralı yok (yalnız dondurma); ölçüm başına tam yıl; gerçek değerler doğrulanmamış aralıklardan.

