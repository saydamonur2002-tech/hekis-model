"""Mikro pilot: tek mahalle, 1.000 bos birim. Kademeli genisleme ve gerceklik testleri.

Kademeler her adimda tek parca ekler; oncekini bozmaz:
  K0 yalniz havuz, bedel yok      K1 + genel bedel %1        K2 + luks bedel (uc bolge)
  K3 + hedef primi (butce dengeli)
Sonra ayni kurallar buyuk olcege (ilce, Istanbul) tasinir.

    python -m hekis.pilot
"""

from __future__ import annotations

import math
import random

from hekis import evaluate as E
from hekis import final
from hekis.zones import LIKELY, run_three_zone, solve_premium

PILOT_STOK = 1_000
ILCE_STOK = 20_000

STAGES = (
    ("K0 yalniz havuz", dict(P={"fee": 0.0, "lux_fee": 0.0})),
    ("K1 + genel bedel %1", dict(P={"lux_fee": 0.0})),
    ("K2 + luks %5 (uc bolge)", dict()),
)


def run(stok: float, stage: dict | None = None, **kw) -> dict:
    stage = dict(stage or {})
    P = {"stok": stok, **stage.pop("P", {}), **kw.pop("P", {})}
    return run_three_zone(P=P, **stage, **kw)


def per_unit(z: dict) -> dict:
    n = max(z["N"], 1e-9)
    return {"daire": z["N"], "kapsam": z["N"] / z["S"][0] if z["S"][0] else 0.0, "sub_birim": z["sub1"] / n,
            "oran": z["ratio"], "cikan": (z["freed_buf"] + z["freed_lux"]) / (z["S"][0] + z["S"][1] + z["S"][2])}


def ladder() -> list[tuple[str, dict]]:
    rows = []
    for name, st in STAGES:
        rows.append((name, per_unit(run(PILOT_STOK, st))))
    z = solve_premium(P={"stok": PILOT_STOK})
    u = per_unit(z)
    u["prim"] = z["premium"]
    rows.append(("K3 + hedef primi", u))
    return rows


def scale_ladder() -> list[tuple[str, dict]]:
    return [(f"{name} ({stok:,})".replace(",", "."), per_unit(run(stok))) for name, stok in
            (("mahalle", PILOT_STOK), ("ilce", ILCE_STOK), ("Istanbul", int(E.BASE["stok"])))]


SAFETY = 1.25  # bedel/sub orani >= 1,25: tespit, tahsil ve idari maliyet modelde yok, %25 pay (karar)


def _ratio(**P) -> float:
    return run_three_zone(P={"stok": PILOT_STOK, **P})["ratio"]


def _smallest(key: str, target: float, **extra) -> float:
    lo, hi = 0.0, 1.0
    for _ in range(50):
        m = (lo + hi) / 2
        if _ratio(**{key: m, **extra}) >= target:
            hi = m
        else:
            lo = m
    return hi


def gates() -> dict:
    """Esikler modelden turetilir: orani SAFETY'ye tasiyan en kucuk tahsilat; olcum hatasi (95% GA) ayrica eklenir.
    Modelin %10 tahsilat tabani (AVOID_FLOOR) kaldirilir: yoksa tahsilat 0'da bile kendini finanse ediyor gorunur."""
    old = final.AVOID_FLOOR
    final.AVOID_FLOOR = 0.0
    try:
        b = run_three_zone(P={"stok": PILOT_STOK})
        n_lux = b["S"][2] * (1 - final.lux_response(0.05))
        n_gen = b["S"][0] * (1 - b["p"]) + b["S"][1] * (1 - final.lux_response(0.01))
        se = lambda n, p: 1.96 * math.sqrt(p * (1 - p) / n)
        frontier = [(g, _smallest("lux_coll", SAFETY, coll=g)) for g in (0.30, 0.20, 0.10)]
        cap_hi = _smallest_cap_max(SAFETY)
        c_ten = 1 - (b["ratio"] - SAFETY) / ((b["ratio"] - _ratio(alpha=0.30 * 0.6)) / 0.4)
        return {"frontier": frontier, "se_lux": se(n_lux, 0.2), "se_gen": se(n_gen, 0.2), "p_max": cap_hi, "ratio": b["ratio"],
                "tenant_min": c_ten, "se_p": se(b["S"][0], b["p"])}
    finally:
        final.AVOID_FLOOR = old


def _smallest_cap_max(target: float) -> float:
    lo, hi = 0.01, 1.0
    for _ in range(50):
        m = (lo + hi) / 2
        if run_three_zone(P={"stok": PILOT_STOK, "cap": m})["ratio"] >= target:
            lo = m
        else:
            hi = m
    return run_three_zone(P={"stok": PILOT_STOK, "cap": lo})["p"]


def tests() -> list[tuple[str, bool, str]]:
    out = []
    a, b = run(PILOT_STOK), run(int(E.BASE["stok"]))
    d = abs(a["ratio"] - b["ratio"]) / b["ratio"]
    out.append(("olcek degismezligi (yapi geregi dogrusal; zayif test, gercek olcek etkisini pilot olcer)", d < 0.01, f"fark %{d:.2%}"))
    n0, n1 = (run(PILOT_STOK, dict(P={"fee": f}))["N"] for f in (0.0, 0.01))
    out.append(("bedel artarsa yerlesen az olmaz", n1 >= n0, f"{n0:.0f} -> {n1:.0f}"))
    g = [run(PILOT_STOK, dict(P={"g_e": x}))["N"] for x in (-0.10, -0.037, 0.0, 0.05)]
    out.append(("beklenen reel artis yukselirse katilim artmaz", all(x >= y for x, y in zip(g, g[1:])), " > ".join(f"{x:.0f}" for x in g)))
    z = run(PILOT_STOK)
    out.append(("butce kimligi: bedel - sub - prim = denge", abs(z["rev"] - z["sub1"] - z["prem_cost"] - z["balance"]) < 1e-3 * max(z["rev"], 1), f"denge {z['balance']:,.0f}"))
    yield_ = z["sub1"] / z["N"] / z["V"][0]
    out.append(("birim sub. degerin %0-8'i (kira getirisi bandi)", 0 < yield_ < 0.08, f"%{yield_:.1%}"))
    p, n_elig = z["p"], z["S"][0]
    se = math.sqrt(p * (1 - p) / n_elig)
    out.append(("pilot katilimi ±10 puan icinde olcebilir (95% GA)", 1.96 * se < 0.10, f"katilim %{p:.0%} ±{1.96 * se:.1%}, uygun {n_elig:.0f} birim"))
    rng = random.Random(7)
    ok = tot = 0
    for _ in range(300):
        P = {k: rng.triangular(lo, hi, mode) for k, (lo, mode, hi) in E.SPACE.items() if k != "stok"}
        P["stok"] = PILOT_STOK
        zz = run_three_zone(P={**LIKELY, **P})
        tot += 1
        ok += zz["ratio"] >= 1.0
    out.append(("belirsizlik taramasi (bilgi): bedel >= sub orani, 300 cekim", ok / tot >= 0.5, f"%{ok / tot:.0%} cekimde oran >= 1"))
    return out


def main() -> int:
    print(f"Mikro pilot: tek mahalle, {PILOT_STOK:,} bos birim (en olasi senaryo)".replace(",", "."))
    print(f"{'kademe':<28}{'daire':>7}{'kapsam':>8}{'sub/birim yil-1':>17}{'bedel/sub':>11}{'bosaltan':>10}")
    for name, u in ladder():
        extra = f"  prim %{u['prim']:.2%}" if "prim" in u else ""
        print(f"{name:<28}{u['daire']:>7.0f}{u['kapsam']:>8.0%}{u['sub_birim']:>17,.0f}{u['oran']:>11.2f}{u['cikan']:>10.0%}{extra}".replace(",", "."))
    print("\nOlcek kademesi (K2 kurallari):")
    for name, u in scale_ladder():
        print(f"{name:<28}{u['daire']:>7.0f}{u['kapsam']:>8.0%}{u['sub_birim']:>17,.0f}{u['oran']:>11.2f}".replace(",", "."))
    g = gates()
    print("\nKademe gecis esikleri (modelden turetilmis, bedel/sub >= 1,25; havuz 1.000 birim):")
    for gen, lux in g["frontier"]:
        print(f"  genel tahsilat %{gen:.0%} ise luks tahsilat >= %{lux:.0%} (olcum hatasi ±{g['se_lux']:.0%} eklenir)")
    print(f"  katilim: en fazla %{g['p_max']:.0%} (ustunde sub. bedeli asar), alt sinir amaca bagli (karar), olcum ±{g['se_p']:.1%}")
    print(f"  kiraci odeme tahsilati: finansal taban %{g['tenant_min']:.0%}")
    print("\nGerceklik testleri (model tutarliligi; gercek dogrulama pilot verisiyle):")
    fails = 0
    for name, ok, note in tests():
        fails += not ok
        print(f"  [{'GECTI' if ok else 'KALDI'}] {name}: {note}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
