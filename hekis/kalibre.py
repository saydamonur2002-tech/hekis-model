"""Doviz geciskenligi ve atalet kalibrasyonu.

    python -m hekis.kalibre

TUFE: Drive 'Secici_Kredi_Veri_MOBIL.pdf' V24 (TUIK Aralik/Aralik), 2015-2025.
Kur 2023-2025: ayni dosya V21 notu (29,40 / 35,22 / 42,88).
Kur 2014-2022: HAFIZADAN, yaklasik, dogrulanmadi. Gercek yil sonu TCMB serisiyle degistirin.
10 gozlem. Kur ve enflasyon ayni yillarda (2018, 2021-23) birlikte siciradigi icin
katsayilar saf kur etkisi degil, ortak sok dahil indirgenmis bicim.
"""

import math

KUR = {2014: 2.32, 2015: 2.92, 2016: 3.53, 2017: 3.77, 2018: 5.28, 2019: 5.94,
       2020: 7.34, 2021: 13.33, 2022: 18.70, 2023: 29.40, 2024: 35.22, 2025: 42.88}
TUFE = {2014: 8.2, 2015: 8.8, 2016: 8.5, 2017: 11.9, 2018: 20.3, 2019: 11.8,
        2020: 14.6, 2021: 36.1, 2022: 64.3, 2023: 64.8, 2024: 44.4, 2025: 30.9}


def ols(X, y):
    n = len(X[0])
    xtx = [[sum(r[i] * r[j] for r in X) for j in range(n)] for i in range(n)]
    xty = [sum(r[i] * v for r, v in zip(X, y)) for i in range(n)]
    m = [xtx[i][:] + [1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for i in range(n):
        p = max(range(i, n), key=lambda k: abs(m[k][i]))
        m[i], m[p] = m[p], m[i]
        pv = m[i][i]
        m[i] = [a / pv for a in m[i]]
        for k in range(n):
            if k != i:
                f = m[k][i]
                m[k] = [a - f * b for a, b in zip(m[k], m[i])]
    inv = [r[n:] for r in m]
    b = [sum(inv[i][j] * xty[j] for j in range(n)) for i in range(n)]
    res = [v - sum(bi * xi for bi, xi in zip(b, r)) for r, v in zip(X, y)]
    s2 = sum(e * e for e in res) / (len(y) - n)
    se = [math.sqrt(s2 * inv[i][i]) for i in range(n)]
    yb = sum(y) / len(y)
    r2 = 1 - sum(e * e for e in res) / sum((v - yb) ** 2 for v in y)
    return b, se, r2, res


def main() -> int:
    d = {t: (KUR[t] / KUR[t - 1] - 1) * 100 for t in range(2015, 2026)}
    ys = list(range(2016, 2026))
    b, se, r2, res = ols([[1, d[t], TUFE[t - 1]] for t in ys], [TUFE[t] for t in ys])
    print("TUFE_t = a + b*kur_t + rho*TUFE_t-1  (n=%d)" % len(ys))
    print("  b   (ayni yil geciskenlik) = %.2f (se %.2f)" % (b[1], se[1]))
    print("  rho (atalet)               = %.2f (se %.2f)" % (b[2], se[2]))
    print("  R2 = %.2f, uzun donem b/(1-rho) = %.2f (>1: ortak sok yukleniyor)" % (r2, b[1] / (1 - b[2])))
    print("  kalintilar: " + ", ".join("%d:%+.1f" % (t, e) for t, e in zip(ys, res)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
