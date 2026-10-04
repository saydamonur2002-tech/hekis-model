# HEKIS modeli

Hedef Endeksli Kapalı İç Senet. Kapalı kira-üretim devresinin stok-akım hesabı.

Bu bir politika vaadi değil, üç defteri ayıran bir hesap makinesidir. Mülkiyet, oturan ve senet aynı sayıyı taşımak zorunda değildir. Eşit göstermek çifte yazımdır.

Repo özeldir. Çalışma taslağıdır, doğrulanmış bir kamu maliyesi modeli değildir. Not kopyası: `saydamonur2002-tech/modeller` içinde `HEKIS_Kapali_Kira_Uretim_Devresi.md`.

## Ne ölçer

- Konut havuza HEKİS olarak kilitlenirse servet içeride kalır. Nakit ödenirse `leakage_rate` kadar altın, döviz veya arsaya kaçar.
- Aidat borç servisine girmez. Havuz neti `(kira - aidat) * 12 * (1 - boşluk) * tahsilat`.
- Yoksul hanenin ödediği kira ile muhasebe kirası ayrıdır. Fark bütçe transferidir.
- Anapara TÜFE ile yürür. Reel kupon varsayılan sıfırdır. Bu gelir koruma değil, finansal baskıdır.
- Hedef primi fiziki endeks eşiği geçince ödenir, anaparanın `premium_cap` oranı ile tavanlanır. Prim bütçeden gider, havuzdan değil.
- Endeks eşiğin altında kalırsa kota `quota_cut` ile kesilir. Üretim payı havuzdan kesilirse anapara erimesi yavaşlar.

## Çalıştırma

Python 3 yeter. Ek paket yok.

```bash
python -m hekis.simulate
```

Tek senaryo:

```bash
python -m hekis.simulate scenarios/baseline.json
```

Çıktı `outputs/` altına JSON yazılır. Baz senaryo 1000 adet 2+1, 1000 adet 1+1, 500 adet 1+0 kullanır. Fiyatlar 7,5 / 5,5 / 3,5 milyon TL. Kiralar 20 / 15 / 10 bin, aidat 3 bin, oturan ödemesi 10 / 8 / 6 bin.

Baz koşu: statik geri dönüş 40,6 yıl. HEKİS kilidinde 20 yılda reel anaparanın yüzde 10,4'ü erir. Nakit ödemede 14,75 milyarlık girişin 10,33 milyarları kaçar.

## Kimlikler

Yıllık havuz:

\[
N = \sum_i (K_i - A_i)\, 12\, n_i\, (1-v)\, c
\]

Bütçe farkı, senet hesabına yazılmaz:

\[
S = \sum_i \max(0, K_i - T_i)\, 12\, n_i\, (1-v)
\]

Anapara endeksi:

\[
P_t = P^{reel}_t \prod_{s=1}^{t}(1+\pi_s)
\]

Reel erime, kupon sıfır ve prim bütçedeyken:

\[
\Delta P^{reel}_t = -\min\left(P^{reel}_{t-1},\; \frac{N - Q_t}{\mathrm{CPI}_t}\right)
\]

Prim, tavanlı:

\[
\Pi_t = \min\left(\alpha \max(0, x_t - x^*) P_t,\; \bar\pi P_t\right)
\]

\(x_t < x^*\) ise \(\Pi_t = 0\) ve kota yarıya iner.

## Sınır

Statik geri dönüş bu kiralarla 30 yılın üstündedir. Model yeni konut iştahını kapatmaz. Onu kapatan kredi/değer tavanıdır, bu repoda yok. Fiziki endeks dışarıdan verilir. Ton sayımının ithal ara malıyla şişmesi modelin içinde çözülmez. Varlık şirketinin konut üreticisine dönmesi de burada bir bayrak değil, kullanıcının kendi ihlalidir.
