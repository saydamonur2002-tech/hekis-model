"""JS modeli icin Python referans ciktilari (app/expected.json): rastgele parametre noktalari, kusursuz olcum yollari, gini."""

from __future__ import annotations

import json
import random

from hekis import horizon
from hekis.reality import gini_with_benefit
from hekis.systems import ANADOLU, ISTANBUL
from hekis.zones import LIKELY

SYS = {"istanbul": ISTANBUL, "anadolu": ANADOLU}


def main() -> int:
    rng = random.Random(5)
    zone = []
    for key, s in SYS.items():
        for _ in range(40):
            st = {"g_e": rng.uniform(-0.12, 0.08), "cap": rng.uniform(0.1, 0.5), "coll": rng.uniform(0.05, 0.8), "lux_coll": rng.uniform(0.05, 0.9),
                  "fee": rng.uniform(0.0, 0.02), "lux_fee": rng.uniform(0.0, 0.08), "inc": rng.uniform(0.6, 1.4), "alpha": rng.uniform(0.5, 1.1), "cost": rng.uniform(1.0, 1.3)}
            size = rng.uniform(0.02, 1.0) * s.full
            P = {**s.base, "g_e": st["g_e"], "cap": st["cap"], "coll": st["coll"], "lux_coll": st["lux_coll"], "fee": st["fee"], "lux_fee": st["lux_fee"],
                 "inc_scale": 1.0 * st["inc"], "alpha": 0.30 * st["alpha"], "util_scale": st["cost"], "aidat_scale": st["cost"]}
            z = s.runner({**LIKELY, **P}, size)
            zone.append({"sistem": key, "st": st, "size": size, "N": z["N"], "sub": z["sub1"], "rev": z["rev"], "ratio": z["ratio"]})
    paths = []
    names = {"yok": None, "Fiyat rallisi (beklenen reel artis +10 puan)": "fiyat rallisi (g_e +10 puan)", "Bedel iptali (hukuki, tum bedel)": "bedel iptali (hukuki)",
             "Kismi iptal (yalniz luks bedel)": "kismi iptal (yalniz luks bedel)", "Agir kriz (ralli + luks iptali + gelir erimesi)": "agir kriz (ralli + luks iptali + gelir erimesi)",
             "Gelir erimesi (hane -%20, kiraci tahsilat x0,8)": "gelir erimesi (hane -%20, kiraci tahsilat x0.8)"}
    for key, s in SYS.items():
        for js_name, py_name in names.items():
            rows = horizon.one_path({}, None, horizon.SHOCKS[py_name] if py_name else None, years=10, system=s)
            paths.append({"sistem": key, "shock": js_name if py_name else None, "rows": [{"N": r["N"]} for r in rows]})
    z = ISTANBUL.runner({**ISTANBUL.base}, ISTANBUL.full)
    g0, g1, p0, p1 = gini_with_benefit(z["N"], z["sub1"] / z["N"], households=ISTANBUL.households)
    json.dump({"zone": zone, "path": paths, "gini": {"N": z["N"], "B": z["sub1"] / z["N"], "households": ISTANBUL.households, "g0": g0, "g1": g1, "p0": p0, "p1": p1}},
              open("app/expected.json", "w"))
    print("app/expected.json yazildi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
