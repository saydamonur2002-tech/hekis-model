"""5 yillik kademeli genisleme, olcek erozyonu ve sok direnci.

Her yil olcum yapilir; esik tutarsa ertesi yil olcek GROWTH_CAP kati buyur (tavan 450.000, tum Istanbul).
Esik: olculen tahsilatlarla bedel/sub >= 1,25 ve olculen katilim %15-38. Tutmazsa dondurulur (dongu duzeltme etkisi yok).
Olcek erozyonu (varsayim, veri yok): tahsilat, 3.800'den 450.000'e log olcekte `erosion` oraninda duser.
Sok: 3. yildan itibaren parametre bozulur. Olcum hatasi binom. Gercek degerler en olasi senaryo etrafinda ucgen dagilimdan.

    python -m hekis.horizon
"""

from __future__ import annotations

import math
import random
import statistics as st

from hekis import evaluate as E
from hekis import final
from hekis.zones import LIKELY, run_three_zone

START, FULL = 3_800, 450_000
GROWTH_CAP = 2.5
EROSION = 0.25
YEARS = 5
SHOCK_YEAR = 3
SAFETY = 1.25
P_RANGE = (0.15, 0.38)
UNCERTAIN = ("g_e", "cap", "coll", "lux_coll")

SHOCKS = {
    "yok": {},
    "fiyat rallisi (g_e +10 puan)": {"g_e_add": 0.10},
    "luks tahsilat cokusu (x0,4)": {"lux_mult": 0.4},
    "genel tahsilat cokusu (x0,5)": {"coll_mult": 0.5},
    "enflasyon sokunu (+10 puan)": {"infl_shift": 0.10},
    "hane geliri -%30": {"inc_mult": 0.7},
    "kombine (rally + luks x0,5)": {"g_e_add": 0.10, "lux_mult": 0.5},
    "bedel iptali (hukuki)": {"lux_mult": 0.0, "coll_mult": 0.0},
    "kur sokunu (enf +10; maliyet x1.3)": {"infl_shift": 0.10, "cost_mult": 1.3},
    "kismi iptal (yalniz luks bedel)": {"lux_mult": 0.0},
    "gelir erimesi (hane -%20, kiraci tahsilat x0.8)": {"inc_mult": 0.8, "alpha_mult": 0.8},
    "kur krizi + sermaye cikisi": {"infl_shift": 0.10, "cost_mult": 1.3, "g_e_add": 0.10, "lux_mult": 0.7},
    "agir kriz (ralli + luks iptali + gelir erimesi)": {"g_e_add": 0.10, "lux_mult": 0.0, "inc_mult": 0.8, "alpha_mult": 0.8},
}


def erosion_factor(size: float, erosion: float) -> float:
    return 1 - erosion * math.log(max(size, START) / START) / math.log(FULL / START)


def apply_shock(P: dict, shock: dict) -> dict:
    out = dict(P)
    out["g_e"] = P["g_e"] + shock.get("g_e_add", 0.0)
    out["lux_coll"] = P["lux_coll"] * shock.get("lux_mult", 1.0)
    out["coll"] = P["coll"] * shock.get("coll_mult", 1.0)
    if "infl_shift" in shock:
        out["infl_shift"] = shock["infl_shift"]
    if "cost_mult" in shock:
        out["util_scale"] = E.BASE["util_scale"] * shock["cost_mult"]
        out["aidat_scale"] = E.BASE["aidat_scale"] * shock["cost_mult"]
    if "alpha_mult" in shock:
        out["alpha"] = E.BASE["alpha"] * shock["alpha_mult"]
    if "inc_mult" in shock:
        out["inc_scale"] = E.BASE["inc_scale"] * shock["inc_mult"]
    return out


def draw(rng: random.Random) -> dict:
    out = {}
    for k in UNCERTAIN:
        lo, _, hi = E.SPACE[k]
        out[k] = rng.triangular(lo, LIKELY[k], hi)
    return out


def _binom(rng: random.Random, p: float, n: float) -> float:
    n = max(n, 1.0)
    return min(1.0, max(0.0, rng.gauss(p, math.sqrt(max(p * (1 - p), 1e-6) / n))))


def one_path(P: dict, rng: random.Random | None, shock: dict | None = None, erosion: float = EROSION,
             growth_cap: float = GROWTH_CAP) -> list[dict]:
    """rng None: kusursuz olcum."""
    P = {**{k: LIKELY[k] for k in UNCERTAIN}, **P}
    rows, size = [], float(START)
    for year in range(1, YEARS + 1):
        Pt = apply_shock(P, shock) if shock and year >= SHOCK_YEAR else dict(P)
        f = erosion_factor(size, erosion)
        Pt["coll"], Pt["lux_coll"] = Pt["coll"] * f, Pt["lux_coll"] * f
        z = run_three_zone(P={**LIKELY, **Pt, "stok": size})
        n_lux = z["S"][2] * (1 - final.lux_response(0.05))
        n_gen = z["S"][0] * (1 - z["p"]) + z["S"][1] * (1 - final.lux_response(0.01))
        rows.append({"yil": year, "stok": size, "N": z["N"], "sub": z["sub1"], "rev": z["rev"], "ratio": z["ratio"], "p": z["p"], "yuk": z["yuk"]})
        if rng is None:
            o_g, o_l, o_p = Pt["coll"], Pt["lux_coll"], z["p"]
        else:
            o_g, o_l, o_p = _binom(rng, Pt["coll"], n_gen), _binom(rng, Pt["lux_coll"], n_lux), _binom(rng, z["p"], z["S"][0])
        ratio_obs = run_three_zone(P={**LIKELY, **Pt, "stok": size, "coll": o_g, "lux_coll": o_l})["ratio"]
        passed = ratio_obs >= SAFETY and P_RANGE[0] <= o_p <= P_RANGE[1]
        rows[-1]["gecti"] = passed
        if passed:
            size = min(FULL, size * growth_cap)
    return rows


def monte_carlo(draws: int = 300, seed: int = 11, shock: dict | None = None, erosion: float = EROSION) -> list[list[dict]]:
    rng = random.Random(seed)
    return [one_path(draw(rng), rng, shock, erosion) for _ in range(draws)]


def summarize(paths: list[list[dict]]) -> dict:
    n = len(paths)
    net = [sum(r["rev"] - r["sub"] for r in p) for p in paths]
    return {
        "size5": st.median(p[4]["stok"] for p in paths),
        "N5": st.median(p[4]["N"] for p in paths),
        "net": st.median(net),
        "deficit": sum(x < 0 for x in net) / n,
        "yuk20": st.median(p[4]["yuk"] for p in paths),
        "acik5": st.median(p[4]["sub"] - p[4]["rev"] for p in paths),
        "ratio_lt1": sum(p[4]["ratio"] < 1.0 for p in paths) / n,
        "full5": sum(p[4]["stok"] >= FULL for p in paths) / n,
        "stuck": sum(p[4]["stok"] <= START for p in paths) / n,
    }


def breakpoints() -> dict:
    """Tam olcekte (450.000), kusursuz olcum, erozyon yok: oranin 1'e dustugu tahsilat carpani ve katilimin %15'in
    altina indigi beklenen reel artis (g_e) sokusu."""
    def run(**kw):
        return run_three_zone(P={**LIKELY, "stok": FULL, **kw})

    def smallest(f, lo=0.0, hi=1.0):
        for _ in range(50):
            m = (lo + hi) / 2
            if f(m):
                hi = m
            else:
                lo = m
        return hi

    lux = smallest(lambda m: run(lux_coll=LIKELY["lux_coll"] * m)["ratio"] >= 1)
    gen = smallest(lambda m: run(coll=LIKELY["coll"] * m)["ratio"] >= 1)
    ge = smallest(lambda d: run(g_e=LIKELY["g_e"] + d)["p"] < P_RANGE[0], 0.0, 0.4)
    return {"lux_carpan": lux, "genel_carpan": gen, "g_e_artis": ge, "ratio_now": run()["ratio"]}


def main() -> int:
    bn = lambda v: v / 1e9
    det = one_path({}, None, erosion=0.0, growth_cap=4.0)
    print("Kusursuz olcum, en olasi senaryo, erozyon yok, buyume tavani yok (onceki varsayim):")
    print(f"  yerlesen: " + " / ".join(f"{r['N']:,.0f}" for r in det).replace(",", "."))
    det2 = one_path({}, None)
    print(f"Kusursuz olcum, erozyon %{EROSION:.0%}, yillik buyume tavani x{GROWTH_CAP}:")
    print(f"{'yil':>4}{'olcek':>10}{'yerlesen':>10}{'sub (mr)':>10}{'bedel (mr)':>12}{'oran':>7}")
    for r in det2:
        print(f"{r['yil']:>4}{r['stok']:>10,.0f}{r['N']:>10,.0f}{bn(r['sub']):>10.2f}{bn(r['rev']):>12.2f}{r['ratio']:>7.2f}".replace(",", "."))
    print(f"5 yil toplam net: {bn(sum(r['rev'] - r['sub'] for r in det2)):.2f} mr TL")
    print("\nErozyon duyarliligi (300 cekim, sok yok):")
    print(f"{'erozyon':>8}{'5. yil olcek':>14}{'yerlesen':>10}{'5y net mr':>11}{'takili':>8}")
    for e in (0.0, 0.25, 0.5):
        r = summarize(monte_carlo(erosion=e))
        print(f"{e:>8.0%}{r['size5']:>14,.0f}{r['N5']:>10,.0f}{bn(r['net']):>11.2f}{r['stuck']:>8.0%}".replace(",", "."))
    print(f"\nSok direnci ({SHOCK_YEAR}. yildan itibaren, 300 cekim, erozyon %{EROSION:.0%}):")
    print(f"{'sok':<34}{'5. yil olcek':>13}{'yerlesen':>10}{'5y net mr':>11}{'zarar %':>9}{'oran<1 %':>10}")
    for name, sh in SHOCKS.items():
        r = summarize(monte_carlo(shock=sh))
        print(f"{name:<34}{r['size5']:>13,.0f}{r['N5']:>10,.0f}{bn(r['net']):>11.2f}{r['deficit']:>9.0%}{r['ratio_lt1']:>10.0%}".replace(",", "."))
    print("\n20 yillik yuk (5. yildaki olcekte, reel mr TL) ve 5. yil yillik acik (sub - bedel; negatif = fazla):")
    print(f"{'sok':<44}{'20y yuk':>9}{'5.yil acik':>12}")
    for name in SHOCKS:
        r = summarize(monte_carlo(shock=SHOCKS[name]))
        print(f"{name:<44}{bn(r['yuk20']):>9.1f}{bn(r['acik5']):>12.2f}")
    b = breakpoints()
    print(f"\nKirilma noktalari (tam olcek, oran {b['ratio_now']:.2f}):")
    print(f"  luks tahsilat en olasi degerin x{b['lux_carpan']:.2f}'ine inerse (%{LIKELY['lux_coll'] * b['lux_carpan']:.0%}) oran 1'e iner")
    print(f"  genel tahsilat x{b['genel_carpan']:.2f}'ine inerse oran 1'e iner (luks yerindeyken)")
    print(f"  beklenen reel konut artisi +{b['g_e_artis']:.1%} puan yukselirse katilim %15'in altina iner (finansal degil, olcek sorunu)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
