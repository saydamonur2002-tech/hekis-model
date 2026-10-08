"""Hane geliri medyani icin sendika verisiyle kalibrasyon ve basabas.

Anchor A: sendika, medyan isci ucreti ~ net asgari ucret, hane basina calisan sayisi varsayimi (yalniz ucret, alt sinir).
Anchor B: TUIK ulusal esdeger gelir, 2026'ya yukseltilmis. Anchor C: TUIK Istanbul (TR10) olcekli.
Gelir olcegi s: hane medyani = 66.316 TL x s.

    python -m hekis.union
"""

from __future__ import annotations

from hekis import evaluate as E, politics, reality

MIN_WAGE_NET = 28_075.5
EARNERS = 1.5   # hane basina ucretli calisan: varsayim
BASE_MEDIAN = politics.MEDIAN * politics.EQ_FACTOR / 12 * politics.UPLIFT  # s = 1 iken hane medyani


def scale_for_median(m: float) -> float:
    return m / BASE_MEDIAN


def breakeven_scale(params: dict | None = None) -> float | None:
    lo, hi = 0.3, 3.0
    f = lambda s: E.evaluate({**(params or {}), "inc_scale": s})["ratio"] - 1.0
    if f(lo) > 0:
        return lo
    if f(hi) < 0:
        return None
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
    return hi


IBB_POVERTY_LINE_2024 = 88_185.0  # IPA / TUIK, bolgesel esdeger medyanin %60'i, 2024 anketi (gelir yili 2023)
UPLIFT_CPI = 2.57   # 2023 ortalama -> 2026 ortasi, TUFE yaklasik
UPLIFT_WAGE = 2.82  # 2023 ortalama net asgari ucret 9.954 -> 28.075,5 (hafizadan)


def ibbs_median(uplift: float) -> float:
    return IBB_POVERTY_LINE_2024 / 0.6 * uplift * politics.EQ_FACTOR / 12


MEMUR_LOWEST = 70_224.0   # en dusuk memur maasi, aile yardimi dahil, Temmuz 2026
MEMUR_FLAT = 55_000.0     # duz memur (13/1), kaba aktarim


def quantile_of_income(monthly: float, scale: float = 1.0) -> float:
    """Model dagilimda hane aylik geliri monthly olan haneden daha az kazananlarin payi."""
    from statistics import NormalDist
    base = politics.MEDIAN * scale * politics.EQ_FACTOR / 12 * politics.UPLIFT
    return NormalDist().cdf((__import__("math").log(monthly / base)) / politics.SIGMA)


def memur_report() -> None:
    tl = lambda v: f"{v:,.0f}".replace(",", ".")
    print("Memur maasi / asgari ucret (data/MEMUR.md):")
    for name, m in (("en dusuk memur (aile yard. dahil)", MEMUR_LOWEST), ("duz memur (13/1), kaba", MEMUR_FLAT)):
        q = quantile_of_income(m)
        print(f"  {name:<34}{tl(m):>8} TL = asgari ucretin {m / MIN_WAGE_NET:.2f} kati, model hane dagiliminda yuzdelik {q:.0%}")
    be = breakeven_scale(dict(g_e=reality.G_ISTANBUL, cap=0.25, coll=0.30, fee=0.01, lux_fee=0.05, lux_coll=0.40, infl_first=reality.INFL_YEAREND_EXP))
    bm = BASE_MEDIAN * be
    print(f"  Basabas hane medyani {tl(bm)} TL = asgari ucretin {bm / MIN_WAGE_NET:.2f} kati; en dusuk memur maasina oran {bm / MEMUR_LOWEST:.3f}.")
    print()
    print("Uygunluk kesimi memur maasina baglanirsa (hane geliri bu seviyenin altindaysa uygun), en olasi senaryo:")
    print(f"{'kesim':<34}{'qcut':>6}{'uygun hane':>12}{'kapsam':>8}{'yil-1 sub':>10}{'oran':>6}{'20y yuk':>9}")
    likely = dict(g_e=reality.G_ISTANBUL, cap=0.25, coll=0.30, fee=0.01, lux_fee=0.05, lux_coll=0.40, infl_first=reality.INFL_YEAREND_EXP)
    for name, m in (("alt %40 (baz)", None), ("duz memur maasinin alti", MEMUR_FLAT), ("en dusuk memur maasinin alti", MEMUR_LOWEST)):
        q = 0.40 if m is None else quantile_of_income(m)
        o = E.evaluate({**likely, "qcut": q})
        eligible = politics.HOUSEHOLDS * politics.TENANT_SHARE * q
        print(f"{name:<34}{q:>6.2f}{tl(eligible):>12}{o['N'] / eligible:>8.1%}{o['sub1'] / 1e9:>10.1f}{o['ratio']:>6.2f}{o['yuk'] / 1e9:>9.0f}")
    print()


def main() -> int:
    tl = lambda v: f"{v:,.0f}".replace(",", ".")
    anchors = (
        ("A sendika, yalniz ucret (alt sinir)", MIN_WAGE_NET * EARNERS),
        ("B TUIK ulusal, 2026'ya yukseltilmis", BASE_MEDIAN),
        ("C TUIK Istanbul (TR10) olcekli", BASE_MEDIAN * politics.ISTANBUL_TR10_RATIO),
        ("D IPA/TUIK TR10 yoksulluk siniri, TUFE", ibbs_median(UPLIFT_CPI)),
        ("D IPA/TUIK TR10 yoksulluk siniri, ucret", ibbs_median(UPLIFT_WAGE)),
    )
    likely = dict(g_e=reality.G_ISTANBUL, cap=0.25, coll=0.30, fee=0.01, lux_fee=0.05, lux_coll=0.40, infl_first=reality.INFL_YEAREND_EXP)
    print(f"Hane geliri medyani, en olasi senaryo (Istanbul). Sendika: ucretlilerin %46,7'si asgari ucret ve altinda, medyan isci ~ {tl(MIN_WAGE_NET)} TL net.")
    print(f"Anchor A: {tl(MIN_WAGE_NET)} x {EARNERS} calisan (varsayim). Turk-Is tek isci yasam maliyeti 47.758 TL, medyan isci bunun altinda.")
    print()
    print(f"{'anchor':<38}{'hane medyani':>14}{'s':>6}{'daire':>8}{'yil-1 sub':>10}{'bedel':>7}{'oran':>6}{'20y yuk':>9}{'kapsam':>8}{'Gini d.':>9}")
    for name, med in anchors:
        sc = scale_for_median(med)
        o = E.evaluate({**likely, "inc_scale": sc})
        eligible = politics.HOUSEHOLDS * politics.TENANT_SHARE * 0.4
        B = o["sub1"] / max(o["N"], 1)
        g0, g1, _, _ = reality.gini_with_benefit(o["N"], B, scale=sc)
        print(f"{name:<38}{tl(med):>14}{sc:>6.2f}{o['N'] / 1000:>7.0f}b{o['sub1'] / 1e9:>10.1f}{o['rev'] / 1e9:>7.1f}{o['ratio']:>6.2f}{o['yuk'] / 1e9:>9.0f}{o['N'] / eligible:>8.1%}{g1 - g0:>9.4f}")
    print()
    be = breakeven_scale(likely)
    if be:
        print(f"Basabas: kendini finanse etmek icin hane medyani en az {tl(BASE_MEDIAN * be)} TL/ay (s = {be:.2f}).")
        print(f"  Bu, net asgari ucretin {BASE_MEDIAN * be / MIN_WAGE_NET:.2f} kati. Anchor A {MIN_WAGE_NET * EARNERS / MIN_WAGE_NET:.1f} kati.")
    print()
    print("Hane basina ucretli calisan sayisina duyarlilik (anchor A), en olasi senaryo:")
    print(f"{'calisan':>8}{'hane medyani':>14}{'oran':>7}{'yil-1 sub':>10}{'20y yuk':>9}")
    for k in (1.2, 1.5, 1.8, 2.0, 2.4):
        sc = scale_for_median(MIN_WAGE_NET * k)
        o = E.evaluate({**likely, "inc_scale": sc})
        print(f"{k:>8.1f}{tl(MIN_WAGE_NET * k):>14}{o['ratio']:>7.2f}{o['sub1'] / 1e9:>10.1f}{o['yuk'] / 1e9:>9.0f}")
    print()
    memur_report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
