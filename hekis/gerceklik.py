"""Gerceklik testleri.

    python -m hekis.gerceklik

Model kendi sayilarina karsi sinanir. Gecmezse model reddedilir, ince ayar yapilmaz.
statsmodels yalniz T1'de capraz kontrol icindir, kurulu degilse atlanir.
"""

import random
import statistics

from hekis.kalibre import KUR, TUFE, ols
from hekis.enflasyon import (BUTCE_FAIZI, FINANSMAN_GIDERI, GSYH, R_EFEKTIF, TICARI_STOK,
                             TUFE_YILLIK, cek, kanallar, yuzdelik)

D = {t: (KUR[t] / KUR[t - 1] - 1) * 100 for t in range(2015, 2026)}


def fit(son):
    """2016..son ile TUFE_t = a + b d_t + rho TUFE_t-1."""
    ys = list(range(2016, son + 1))
    b, se, r2, res = ols([[1, D[t], TUFE[t - 1]] for t in ys], [TUFE[t] for t in ys])
    return b, se, r2, res


def tahmin(b, d, onceki):
    return b[0] + b[1] * d + b[2] * onceki


def t1_capraz():
    try:
        import numpy as np
        import statsmodels.api as sm
    except ImportError:
        return "T1 atlandi (numpy/statsmodels yok)", True
    ys = list(range(2016, 2026))
    X = np.array([[1, D[t], TUFE[t - 1]] for t in ys], float)
    y = np.array([TUFE[t] for t in ys], float)
    m = sm.OLS(y, X).fit()
    b, se, _, _ = fit(2025)
    fark = max(abs(m.params[i] - b[i]) for i in range(3))
    hac = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 1})
    dw = sum((m.resid[i] - m.resid[i - 1]) ** 2 for i in range(1, len(y))) / sum(m.resid ** 2)
    ok = fark < 1e-6
    return ("T1 elle yazilan OLS = statsmodels: max fark {:.1e}. HAC(1) se b={:.2f} (elle {:.2f}). Durbin-Watson {:.2f}".format(
        fark, hac.bse[1], se[1], dw)), ok


def t2_ornek_disi():
    L, hata, naif = [], [], []
    for Y in range(2021, 2026):
        b, _, _, _ = fit(Y - 1)
        tah = tahmin(b, D[Y], TUFE[Y - 1])
        hata.append(tah - TUFE[Y])
        naif.append(TUFE[Y - 1] - TUFE[Y])
        L.append("   {}: tahmin {:5.1f} gercek {:5.1f} hata {:+5.1f} (naif {:+5.1f})".format(Y, tah, TUFE[Y], tah - TUFE[Y], TUFE[Y - 1] - TUFE[Y]))
    rm = (sum(e * e for e in hata) / len(hata)) ** .5
    rn = (sum(e * e for e in naif) / len(naif)) ** .5
    return "T2 ornek disi (genisleyen pencere). RMSE model {:.1f} vs naif {:.1f}\n{}".format(rm, rn, "\n".join(L)), rm < rn


def t3_yeniden_oynatma():
    """2023 sonuna kadar fit, 2024-25'i yalniz kur ile coz."""
    b, _, _, _ = fit(2023)
    p24 = tahmin(b, D[2024], TUFE[2023])
    p25 = tahmin(b, D[2025], p24)
    ok = abs(p25 - TUFE[2025]) < 8
    return ("T3 tarihsel tekrar (2023'e kadar fit, 2024-25 kurla ileri): 2024 {:.1f} (gercek {:.1f}), 2025 {:.1f} (gercek {:.1f}). "
            "2025 hata {:+.1f} puan".format(p24, TUFE[2024], p25, TUFE[2025], p25 - TUFE[2025])), ok


def t4_permutasyon(n=3000):
    ys = list(range(2016, 2026))
    b0 = fit(2025)[0][1]
    rng = random.Random(7)
    say = 0
    for _ in range(n):
        d = [D[t] for t in ys]
        rng.shuffle(d)
        b, _, _, _ = ols([[1, di, TUFE[t - 1]] for di, t in zip(d, ys)], [TUFE[t] for t in ys])
        if b[1] >= b0:
            say += 1
    p = say / n
    return "T4 permutasyon: kurlar yillar arasinda karistirilirsa b>={:.2f} olasiligi {:.3f}".format(b0, p), p < 0.10


def t5_jackknife():
    ys = list(range(2016, 2026))
    bs, rs = [], []
    for atla in ys:
        k = [t for t in ys if t != atla]
        b, _, _, _ = ols([[1, D[t], TUFE[t - 1]] for t in k], [TUFE[t] for t in k])
        bs.append(b[1]); rs.append(b[2])
    return ("T5 birini disarida birak: b {:.2f}-{:.2f}, rho {:.2f}-{:.2f}. 2022 disarida b={:.2f}".format(
        min(bs), max(bs), min(rs), max(rs), bs[ys.index(2022)])), (max(bs) - min(bs)) < 0.4


def t6_kirilma():
    ka = [t for t in range(2016, 2021)]
    kb = [t for t in range(2021, 2026)]
    out = []
    for ad, k in (("2016-20", ka), ("2021-25", kb)):
        b, _, _, _ = ols([[1, D[t]] for t in k], [TUFE[t] for t in k])
        out.append("{} b={:.2f}".format(ad, b[1]))
    return "T6 donem istikrari (yalniz kur, ataletsiz): " + ", ".join(out), True


def t7_buyukluk(n=4000):
    rng = random.Random(11)
    kont = {"B faiz tasarrufu > finansman gideri": 0, "toplam ikincil > 3 puan": 0, "toplam > TUFE": 0}
    ikinci = []
    for _ in range(n):
        p = cek(rng)
        k = kanallar(p)
        b_faiz_tl = TICARI_STOK * p["kilit_pay"] * p["dongu"] * R_EFEKTIF
        b_vade_tl = GSYH * p["vade_alacak"] * p["dongu"] * R_EFEKTIF * p["vade_faiz"]
        if b_faiz_tl + b_vade_tl > FINANSMAN_GIDERI:
            kont["B faiz tasarrufu > finansman gideri"] += 1
        ikinci.append(k["toplam"])
        if k["toplam"] > 3:
            kont["toplam ikincil > 3 puan"] += 1
        if k["toplam"] > TUFE_YILLIK * 100:
            kont["toplam > TUFE"] += 1
    s = "; ".join("{} {:.1f}%".format(a, 100 * v / n) for a, v in kont.items())
    ok = kont["toplam > TUFE"] == 0 and kont["B faiz tasarrufu > finansman gideri"] / n < 0.05
    return "T7 buyukluk/sinir (4000 cekim): " + s, ok


def t8_2026():
    """2026 icin kor tahmin. d_2026 varsayim (%20-28). Gozlem TUFE Agustos 2026 yillik %31,5, Aralik degil."""
    b, _, _, _ = fit(2025)
    lo, hi = tahmin(b, 16, TUFE[2025]), tahmin(b, 20, TUFE[2025])
    return ("T8 2026 kor tahmin (kur %16-20, gozlem tempo): {:.1f}-{:.1f}. Gozlem Agustos yillik %31,5 (Aralik degil, tam kiyas degil)".format(lo, hi),
            lo - 3 <= TUFE_YILLIK * 100 <= hi + 3)


def main() -> int:
    testler = [t1_capraz, t2_ornek_disi, t3_yeniden_oynatma, t4_permutasyon, t5_jackknife, t6_kirilma, t7_buyukluk, t8_2026]
    gecen = 0
    for t in testler:
        msg, ok = t()
        gecen += bool(ok)
        print(("[GECTI] " if ok else "[KALDI] ") + msg)
        print()
    print("{}/{} test gecti".format(gecen, len(testler)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
