# Esenyurt satis gozlemi, teyit 2026-10-04

## Teyit edilen

Endeksa Istanbul Esenyurt satilik konut sayfasi, Agustos 2026 sonu. Duz sayfa okumasi betik yuzunden bos dondu. Arama dokumu ayni URL'den su satirlari verdi. Emlakjet ilce kutusu ayni ortalamayi bagimsiz tekrarliyor.

| Alan | Deger | Teyit |
| --- | --- | --- |
| Ortalama m2 satis | 34.475 TL | Endeksa + Emlakjet |
| Ortalama brut alan | 105 m2 | Endeksa |
| Ortalama konut fiyati | 3.619.875 TL | Endeksa + Emlakjet |
| Geri donus | 10 yil | Endeksa + Emlakjet |
| Getiri | %10,04 | Endeksa + Emlakjet |
| Son 1 yil nominal artis | %32,18 | Endeksa |
| Ortalama kira | 25.955 TL | Emlakjet ilce kutusu |
| Kira m2 | 288 TL | Emlakjet ilce kutusu |
| Birim fiyat araligi 20.455-53.333 | kullanici aktarimi | bu turda sayfada gorulmedi, teyitsiz |

34.475 x 105 = 3.619.875. Aritmetik tutuyor.

Kaynaklar:
- https://www.endeksa.com/tr/analiz/turkiye/istanbul/esenyurt/index/satilik/konut
- Emlakjet Esenyurt ilce kutusu, ayni 34.475 / 3.619.875 / 10 yil / %10,04 / 288 TL m2 kira

## Modele eklenen

`data/istanbul_2026.json` icinde `esenyurt_m2_tl` 34475, ortalama fiyat 3619875, ortalama alan 105, amortisman 10, getiri 0.1004. Kod satis fiyatini bu m2 ile carpiyor. 18 yil turevi dusuruldu.

Min-maks json'da duruyor ama teyitsiz isaretli. Kosuya girmiyor.

## Carpisma

10 yil, aylik kirayi yaklasik 30.166 TL varsayar. 288 TL/m2 x 105 m2 = 30.240 TL. Endeksa-Emlakjet cifti kendi icinde kapaniyor.

KiraMetre 2+1 medyani 20.000 TL, m2 kira 231 TL, 2.212 kayit. i24Haber'in aktardigi Endeksa Mart 2026 kira m2 degeri 228 TL. Bu, Agustos satis ciftinin kirasi degil. 20 binlik medyanla 10 yil yazmak cifte yazimdir.

Sub20 kosu tip medyan kira + teyitli m2 satis + TUFE + yuzde 20 butce subvansiyonu olarak duruyor. Endeksa cifti ayri okunur: 3,62 milyon, 10 yil, getiri %10,04.
