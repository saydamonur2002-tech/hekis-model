"""Tek giris noktasi: parametre sozlugu -> cikti sozlugu. Duyarlilik, tornado ve Monte Carlo bunun uzerinde calisir.

Sistem: karma. Havuz aidati oder, oturan dereceli kira, abonelik tam subvanse, luks ust dilim havuz disi ve ayri bedel.
"""

from __future__ import annotations

import copy
import math
import random

from hekis import final, politics
from hekis.bind import load_obs

# ad: (alt, mod, ust). Mod bugunku en iyi tahmin, alt-ust makul aralik. Hepsi veri degil.
SPACE = {
    "g_e": (-0.15, -0.065, 0.15),          # beklenen reel konut artisi
    "cap": (0.10, 0.40, 0.60),             # katilim tavani
    "slope": (10.0, 25.0, 50.0),           # katilim egimi
    "fee": (0.005, 0.01, 0.05),            # genel bos tutma bedeli
    "coll": (0.15, 0.60, 0.90),            # genel etkin tahsilat
    "bakim": (0.005, 0.01, 0.02),
    "aidat_scale": (0.5, 1.0, 1.5),
    "alpha": (0.20, 0.30, 0.40),           # oturanin gelirden kira payi
    "qcut": (0.20, 0.40, 0.60),            # uygun gelir dilimi
    "uplift": (1.3, politics.UPLIFT, 2.0),
    "util_scale": (0.7, 1.0, 1.5),         # abonelik gider carpani
    "infl_shift": (-0.05, 0.0, 0.10),      # OVP yoluna eklenen enflasyon
    "cut": (0.10, 0.20, 0.50),             # ayrilan luks pay
    "sigma": (0.4, 0.6, 0.8),
    "lux_fee": (0.01, 0.05, 0.12),
    "lux_cap": (0.40, 0.65, 0.80),
    "lux_coll": (0.30, 0.60, 0.90),
    "stok": (225_000, 450_000, 750_000),
}
BASE = {k: v[1] for k, v in SPACE.items()}
BASE["eq"] = 2.0
BASE["rent_prop"] = True


def make_obs(P: dict) -> dict:
    obs = copy.deepcopy(load_obs())
    obs["aidat"]["istanbul_ortalama_tl_ay"] *= P["aidat_scale"]
    obs["bos_stok"]["esenyurt_aidat_varsayim_tl_ay"] *= P["aidat_scale"]
    obs["opex"]["bakim_orani_giris_degeri"] = P["bakim"]
    for k in ("elektrik_tl_kwh", "dogalgaz_tl_m3", "su_tl_m3"):
        obs["abonelik"][k] *= P["util_scale"]
    for y in ("2026", "2027", "2028", "2029"):
        obs["ovp_2027_2029"][y] = max(0.0, obs["ovp_2027_2029"][y] + P["infl_shift"])
    obs["bos_stok"]["ibb_elektrik_su_tabanli"] = P["stok"]
    return obs


def evaluate(P: dict | None = None) -> dict:
    P = {**BASE, **(P or {})}
    obs = make_obs(P)
    p, n, r, first, rev_ord = final.run_scenario(
        obs, P["cap"], P["fee"], P["coll"], P["cut"], P["sigma"], False,
        g=P["g_e"], slope=P["slope"], alpha=P["alpha"], qcut=P["qcut"], uplift=P["uplift"], eq=P["eq"], rent_prop=P["rent_prop"])
    _, _, rev_lux, resp = final.lux_economics(obs, P["sigma"], P["cut"], P["lux_fee"], P["lux_coll"], P["lux_cap"])
    revenue = rev_ord + rev_lux
    return {
        "p": p, "N": n, "sub1": first, "yuk": r.total_fiscal_real, "odenen": r.real_eroded,
        "entry": r.entry_value, "rev": revenue, "ratio": revenue / first if first > 0 else 0.0,
        "deficit": first - revenue, "lux_resp": resp,
    }


def monte_carlo(draws: int = 1500, seed: int = 42) -> tuple[list[dict], list[dict]]:
    rng = random.Random(seed)
    inputs, outputs = [], []
    for _ in range(draws):
        P = {k: rng.triangular(lo, hi, mode) for k, (lo, mode, hi) in SPACE.items()}
        inputs.append(P)
        outputs.append(evaluate(P))
    return inputs, outputs


def _ranks(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    rk = [0.0] * len(xs)
    for pos, i in enumerate(order):
        rk[i] = pos / (len(xs) - 1)
    return rk


def spearman(xs: list[float], ys: list[float]) -> float:
    rx, ry = _ranks(xs), _ranks(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0.0


def tornado() -> list[tuple[str, dict, dict]]:
    base = evaluate()
    rows = []
    for k, (lo, mode, hi) in SPACE.items():
        a, b = evaluate({k: lo}), evaluate({k: hi})
        rows.append((k, a, b))
    rows.sort(key=lambda t: -abs(t[2]["ratio"] - t[1]["ratio"]))
    return rows
