"""5 yillik kademeli genisleme. Her yil olcum yapilir; esik tutarsa bir sonraki yil olcek bir kademe buyur.

Kademeler (birim, bos stok): 3.800 pilot, 20.000 ilce, 100.000, 450.000 (tum Istanbul). Esik: olculen tahsilatlarla
bedel/sub >= 1,25 ve olculen katilim %15-38. Olcum hatasi binom (95% GA formulundeki ayni n). Esik tutmazsa ayni
kademede kalinir ve duzeltme etkisi varsayilmaz (muhafazakar). Gercek degerler en olasi senaryo etrafinda
ucgen dagilimdan cekilir. Olcek erozyonu (kademe buyudukce tahsilat dusmesi) modelde yok.

    python -m hekis.horizon
"""

from __future__ import annotations

import math
import random
import statistics as st

from hekis import evaluate as E
from hekis import final
from hekis.zones import LIKELY, run_three_zone

STEPS = (3_800, 20_000, 100_000, 450_000)
YEARS = 5
SAFETY = 1.25
P_RANGE = (0.15, 0.38)
UNCERTAIN = ("g_e", "cap", "coll", "lux_coll")


def draw(rng: random.Random) -> dict:
    out = {}
    for k in UNCERTAIN:
        lo, _, hi = E.SPACE[k]
        out[k] = rng.triangular(lo, LIKELY[k], hi)
    return out


def _binom(rng: random.Random, p: float, n: float) -> float:
    n = max(n, 1.0)
    return min(1.0, max(0.0, rng.gauss(p, math.sqrt(max(p * (1 - p), 1e-6) / n))))


def one_path(P: dict, rng: random.Random | None) -> list[dict]:
    """rng None: kusursuz olcum."""
    old = final.AVOID_FLOOR
    rows, step = [], 0
    for year in range(1, YEARS + 1):
        stok = STEPS[step]
        z = run_three_zone(P={**LIKELY, **P, "stok": stok})
        n_lux = z["S"][2] * (1 - final.lux_response(0.05))
        n_gen = z["S"][0] * (1 - z["p"]) + z["S"][1] * (1 - final.lux_response(0.01))
        rows.append({"yil": year, "stok": stok, "N": z["N"], "sub": z["sub1"], "rev": z["rev"], "ratio": z["ratio"], "p": z["p"]})
        if rng is None:
            o_g, o_l, o_p = P.get("coll", LIKELY["coll"]), P.get("lux_coll", LIKELY["lux_coll"]), z["p"]
        else:
            o_g = _binom(rng, P["coll"], n_gen)
            o_l = _binom(rng, P["lux_coll"], n_lux)
            o_p = _binom(rng, z["p"], z["S"][0])
        ratio_obs = run_three_zone(P={**LIKELY, **P, "stok": stok, "coll": o_g, "lux_coll": o_l})["ratio"]
        passed = ratio_obs >= SAFETY and P_RANGE[0] <= o_p <= P_RANGE[1]
        rows[-1]["gecti"] = passed
        if passed and step < len(STEPS) - 1:
            step += 1
    return rows


def monte_carlo(draws: int = 400, seed: int = 11) -> list[list[dict]]:
    rng = random.Random(seed)
    return [one_path(draw(rng), rng) for _ in range(draws)]


def summarize(paths: list[list[dict]]) -> dict:
    n = len(paths)
    return {
        "p_full_y4": sum(p[3]["stok"] == STEPS[-1] for p in paths) / n,
        "p_full_y5": sum(p[4]["stok"] == STEPS[-1] for p in paths) / n,
        "p_stuck_pilot": sum(p[4]["stok"] == STEPS[0] for p in paths) / n,
        "N5": st.median(p[4]["N"] for p in paths),
        "cum_net": st.median(sum(r["rev"] - r["sub"] for r in p) for p in paths),
        "size": [st.median(p[i]["stok"] for p in paths) for i in range(YEARS)],
        "false_pass": sum(p[4]["stok"] == STEPS[-1] and p[4]["ratio"] < 1.0 for p in paths) / n,
        "missed": sum(p[4]["stok"] < STEPS[-1] and p[4]["ratio"] >= SAFETY for p in paths) / n,
        "deficit_share": sum(sum(r["rev"] - r["sub"] for r in p) < 0 for p in paths) / n,
    }


def main() -> int:
    bn = lambda v: v / 1e9
    det = one_path({}, None)
    print("Kusursuz olcum, en olasi senaryo (esikler her yil tutar):")
    print(f"{'yil':>4}{'olcek (birim)':>15}{'yerlesen':>10}{'sub (mr)':>10}{'bedel (mr)':>12}{'oran':>7}")
    for r in det:
        print(f"{r['yil']:>4}{r['stok']:>15,}{r['N']:>10,.0f}{bn(r['sub']):>10.2f}{bn(r['rev']):>12.2f}{r['ratio']:>7.2f}".replace(",", "."))
    print(f"5 yil toplam net (bedel - sub): {bn(sum(r['rev'] - r['sub'] for r in det)):.1f} mr TL")
    s = summarize(monte_carlo())
    print("\nBelirsiz gercek degerler + olcum hatasi (400 cekim):")
    print("medyan olcek (birim) yil1..5: " + " / ".join(f"{x:,.0f}" for x in s["size"]).replace(",", "."))
    print(f"tum Istanbul'a 4. yilda ulasma %{s['p_full_y4']:.0%}, 5. yilda %{s['p_full_y5']:.0%}; pilotta takili kalma %{s['p_stuck_pilot']:.0%}")
    print(f"5. yil medyan yerlesen {s['N5']:,.0f}; 5 yil medyan net {bn(s['cum_net']):.1f} mr TL; toplam net negatif olan %{s['deficit_share']:.0%}".replace(",", "."))
    print(f"yanlis gecis (tam olcege ulasti ama gercek oran <1) %{s['false_pass']:.1%}; yanlis ret (gercek oran >=1,25 ama takildi) %{s['missed']:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
