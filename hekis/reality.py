"""En olasi senaryo, guncel veriyle. Faiz kanali, gini, yoksulluk, konut yuku ve kira piyasasi etkisi.

    python -m hekis.reality
"""

from __future__ import annotations

import math

from hekis import evaluate as E, politics
from hekis.bind import load_obs

POLICY_RATE = 0.37
INFL_AUG = 0.3151
INFL_SEP_EXP = 0.3016
INFL_YEAREND_EXP = 0.2966
RR_NOW = (1 + POLICY_RATE) / (1 + INFL_AUG) - 1

# Faiz kanali: gecelik borc alma faizinin reel hali (data/FAIZ_KUR.md), reel konut artisi (data/KFE.md)
RR_HIST = {2019: -0.012, 2020: 0.008, 2021: -0.173, 2022: -0.346, 2023: -0.144, 2024: 0.011, 2025: 0.043}
G_HIST = {2019: -0.018, 2020: 0.152, 2021: 0.202, 2022: 0.533, 2023: 0.111, 2024: -0.104, 2025: -0.015}


def ols(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    a = my - b * mx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    return a, b, 1 - ss_res / ss_tot


def gini_with_benefit(n_housed: float, benefit_year: float, households: float = politics.HOUSEHOLDS, grid: int = 4000):
    """Hane geliri dagilimi (lognormal). Alt %40'tan n_housed hane yillik benefit_year TL alir (kura).
    Doner: gini once, gini sonra, goreli yoksulluk once/sonra (medyanin %50'si, gelir ilavesi sonrasi sabit cizgi)."""
    phi = min(1.0, n_housed / (0.4 * households))
    base, after = [], []
    for i in range(grid):
        q = (i + 0.5) / grid
        inc = politics.hh_monthly(q) * 12
        w = 1 / grid
        base.append((inc, w))
        if q < 0.4:
            after.append((inc + benefit_year, w * phi))
            after.append((inc, w * (1 - phi)))
        else:
            after.append((inc, w))
    line = 0.5 * politics.hh_monthly(0.5) * 12

    def gini(cells: list[tuple[float, float]]) -> float:
        cells = sorted(cells)
        tot_w = sum(w for _, w in cells)
        tot_y = sum(i * w for i, w in cells)
        cum_w = cum_y = area = 0.0
        for inc, w in cells:
            y = inc * w
            area += (cum_y + y / 2) * w
            cum_y += y
            cum_w += w
        return 1 - 2 * area / (tot_w * tot_y)

    pov = lambda cells: sum(w for i, w in cells if i < line) / sum(w for _, w in cells)
    return gini(base), gini(after), pov(base), pov(after)


def main() -> int:
    obs = load_obs()
    print("1) Guncel veri (data/GUNCEL.md)")
    print(f"   TUFE Agustos %{INFL_AUG:.2%}, Eylul beklentisi %{INFL_SEP_EXP:.2%}, yil sonu %{INFL_YEAREND_EXP:.2%} (OVP %28,4)")
    print(f"   Politika faizi %{POLICY_RATE:.0%}, reel faiz Agustos'a gore %{RR_NOW:.1%}")
    print("   Kira artis ust siniri (12 aylik TUFE ort.) %31,79, yeni kiraci %34,5, Gini 0,410")
    print()
    xs = [RR_HIST[y] for y in sorted(RR_HIST)]
    ys = [G_HIST[y] for y in sorted(RR_HIST)]
    a, b, r2 = ols(xs, ys)
    g_pred = a + b * RR_NOW
    print("2) Faiz kanali: reel konut artisi = a + b x reel faiz (2019-2025, n=7)")
    print(f"   a = {a:.3f}, b = {b:.2f}, R2 = {r2:.2f}. Bugunku reel faizde ({RR_NOW:.1%}) tahmin {g_pred:.1%}, gozlenen (KFE Agustos) -%6,5")
    print("   Not: n=7, 2022 sicramasi egimi belirliyor. Nedensellik degil, ortusme.")
    print()
    g_use = max(-0.15, min(0.15, g_pred))
    scenarios = {
        "en olasi (orta yaptirim, zayif tahsilat)": dict(g_e=-0.065, cap=0.25, coll=0.30, fee=0.01, lux_fee=0.05, lux_coll=0.40, infl_first=INFL_YEAREND_EXP),
        "en olasi, faiz kanali g_e": dict(g_e=g_use, cap=0.25, coll=0.30, fee=0.01, lux_fee=0.05, lux_coll=0.40, infl_first=INFL_YEAREND_EXP),
        "iyimser (guclu yaptirim, iyi tahsilat)": dict(g_e=-0.065, cap=0.55, coll=0.60, fee=0.03, lux_fee=0.05, lux_coll=0.60, infl_first=INFL_YEAREND_EXP),
        "kotumser (gonullu, zayif tahsilat)": dict(g_e=-0.065, cap=0.08, coll=0.15, fee=0.005, lux_fee=0.03, lux_coll=0.30, infl_first=INFL_YEAREND_EXP),
    }
    bn = lambda v: v / 1e9
    print("3) Senaryolar, guncel veriyle")
    print(f"{'senaryo':<44}{'daire':>8}{'yil-1 sub':>10}{'bedel':>7}{'oran':>6}{'acik':>7}{'20y yuk':>9}")
    res = {}
    for name, P in scenarios.items():
        o = E.evaluate(P)
        res[name] = o
        print(f"{name:<44}{o['N'] / 1000:>7.0f}b{bn(o['sub1']):>10.1f}{bn(o['rev']):>7.1f}{o['ratio']:>6.2f}{bn(o['deficit']):>7.1f}{bn(o['yuk']):>9.0f}")
    print(f"   (mr TL/yil, bugunku TL; acik = sub. - bedel, negatif fazla)")
    print()
    likely = res["en olasi (orta yaptirim, zayif tahsilat)"]
    N, B = likely["N"], likely["sub1"] / max(likely["N"], 1)
    g0, g1, p0, p1 = gini_with_benefit(N, B)
    print("4) Etki: en olasi senaryo")
    print(f"   Yerlesen {N:,.0f} hane, her biri yilda {B:,.0f} TL (ayda {B / 12:,.0f}) fayda".replace(",", "."))
    print(f"   Gini (hane geliri, lognormal): {g0:.4f} -> {g1:.4f}  (degisim {g1 - g0:+.4f})")
    print(f"   Goreli yoksulluk (medyanin %50'si, model): %{p0:.2%} -> %{p1:.2%}  ({(p1 - p0) * 100:+.2f} puan)")
    print()
    mk_rent = 0.4 * 20_000 + 0.4 * 17_000 + 0.2 * 14_250
    util = politics.monthly_utilities(obs)
    print("   Yerlesen hanenin konut yuku (gelire oran, piyasa kirasi + abonelik / program):")
    print(f"   {'gelir dilimi':<14}{'hane geliri/ay':>16}{'programsiz':>12}{'programli':>11}{'kazanc (TL/ay)':>16}")
    for q in (0.10, 0.20, 0.30, 0.40):
        inc = politics.hh_monthly(q)
        without = (mk_rent + util) / inc
        pay = min(mk_rent, 0.30 * inc)
        print(f"   alt %{int(q * 100):<10}{inc:>16,.0f}{without:>12.0%}{pay / inc:>11.0%}{mk_rent + util - pay:>16,.0f}".replace(",", "."))
    print()
    tenants = politics.HOUSEHOLDS * politics.TENANT_SHARE
    ds = N / tenants
    print("5) Kira piyasasi: yerlesenler piyasa talebinden cikar (veya arz eklenir). Kiraci hane " + f"{tenants / 1e6:.1f} mn, etki {ds:.2%}")
    for eps in (0.3, 0.6, 1.0):
        print(f"   talep esnekligi {eps}: piyasa kirasi yaklasik {-ds / eps:+.2%}")
    print("   Esneklik degerleri literatur tahmini, bu oturumda kaynakla dogrulanmadi.")
    print()
    c_hold = 0.0105
    rr_star = (c_hold - a) / b
    print("6) Faiz esigi: tutma maliyeti (%1,05) beklenen reel artisi asarsa katilim cokmeye baslar.")
    print(f"   Regresyonla bu reel faiz esigi {rr_star:.1%}. Bugunku reel faiz {RR_NOW:.1%}, tampon {(RR_NOW - rr_star) * 100:.1f} puan.")
    print(f"   {'reel faiz':>10}{'beklenen reel artis':>21}{'yerlesen daire':>16}")
    base_P = scenarios["en olasi (orta yaptirim, zayif tahsilat)"]
    for rr in (0.08, RR_NOW, 0.02, 0.0, -0.02, -0.05, -0.10, -0.20):
        g = max(-0.15, min(0.15, a + b * rr))
        o = E.evaluate({**base_P, "g_e": g})
        print(f"   {rr:>10.1%}{g:>21.1%}{o['N'] / 1000:>15.0f}b")
    print("   Ornek: politika faizi %37 iken enflasyon %37'ye cikarsa reel faiz sifir, katilim yaklasik %30 duser, reel faiz -%5'te dortte birine iner.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
