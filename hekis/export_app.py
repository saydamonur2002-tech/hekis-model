"""Uygulama (app/) icin sabitleri disa aktarir: sehir bazli bolge buyuklukleri, degerler, tutma maliyeti, birim subvansiyon tablosu.

JS modeli (app/model.js) run_three_zone'un ilk yil hesabini kapali formda yeniden uretir; bu dosyadaki sabitler Python'dan gelir.
Dogrulama: node app/verify.js (Python ciktisiyla karsilastirir).

    python -m hekis.export_app
"""

from __future__ import annotations

import json
import math

from hekis import anadolu, cities, evaluate as E, final, politics, zones
from hekis.bind import load_obs

INC = (0.5, 0.7, 0.85, 1.0, 1.2, 1.5)
ALPHA = (0.4, 0.6, 0.8, 1.0, 1.2)
COST = (1.0, 1.3)
LIKELY = zones.LIKELY


def city_block(name: str, stok: float, g_base: float, s: float, q_h: float | None, mut, households: float, tariff: dict) -> dict:
    def run(**P):
        kw = {"obs_mut": mut} if mut else {}
        if q_h is not None:
            kw["q_h"] = q_h
        return zones.run_three_zone(P={**tariff, "stok": stok, "g_e": g_base, "inc_scale": s, **P}, households=households, **kw)

    z = run()
    cap, fee = {**E.BASE, **LIKELY, **tariff}["cap"], {**E.BASE, **LIKELY, **tariff}["fee"]
    logit = lambda p: math.log(p / (1 - p))
    holds = []
    for cm in COST:
        zz = run(util_scale=cm, aidat_scale=cm)
        holds.append(logit(zz["p"] / cap) / 25.0 - fee + g_base)
    B = [[[run(inc_scale=s * m, alpha=E.BASE["alpha"] * a, util_scale=c, aidat_scale=c)["sub1"] / run(inc_scale=s * m, alpha=E.BASE["alpha"] * a, util_scale=c, aidat_scale=c)["N"]
           for c in COST] for a in ALPHA] for m in INC]
    return {"ad": name, "stok": stok, "g_base": g_base, "fS": [x / stok for x in z["S"]], "V": list(z["V"]), "hold": holds, "B": B,
            "households": households, "q_h": z["q_h"]}


def main() -> int:
    obs = load_obs()
    out = {"inc": INC, "alpha": ALPHA, "cost": COST, "sistem": {}}
    ist = city_block("Istanbul", float(E.BASE["stok"]), LIKELY["g_e"], 1.0, None, None, politics.HOUSEHOLDS, {})
    out["sistem"]["istanbul"] = {"ad": "Istanbul", "tarife": [0.01, 0.05], "sehirler": [ist], "full": E.BASE["stok"], "households": politics.HOUSEHOLDS,
                                  "eligible": politics.HOUSEHOLDS * politics.TENANT_SHARE * ist["q_h"]}
    blocks, hh, elig = [], 0.0, 0.0
    for c in anadolu.ANADOLU:
        cs = anadolu.city_setup(obs, c)
        blk = city_block(cities.TITLE[c], cs["stok"], cs["g_e"], cs["s"], cs["q_h"], cities.mutator(cs["fp"], cs["fr"]), cs["households"], {"fee": 0.005, "lux_fee": 0.03})
        blocks.append(blk)
        hh += cs["households"]
        elig += cs["households"] * politics.TENANT_SHARE * cs["q_h"]
    out["sistem"]["anadolu"] = {"ad": "Anadolu (7 sehir)", "tarife": [0.005, 0.03], "sehirler": blocks, "full": sum(b["stok"] for b in blocks), "households": hh, "eligible": elig}
    out["sabit"] = {"slope": 25.0, "lux_cap": final.LUX_CAP, "lux_fs": final.LUX_FS, "avoid_start": final.AVOID_START, "avoid_slope": final.AVOID_SLOPE,
                    "mu": politics.MU, "sigma": politics.SIGMA, "eq": politics.EQ_FACTOR, "uplift": politics.UPLIFT, "tenant_share": politics.TENANT_SHARE,
                    "w_kira": 0.0676, "rented": 0.5, "national_hh": 86_092_168 / 3.09}
    json.dump(out, open("app/constants.json", "w"), ensure_ascii=False, indent=1)
    print("yazildi app/constants.json", sum(len(v["sehirler"]) for v in out["sistem"].values()), "sehir bloku")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
