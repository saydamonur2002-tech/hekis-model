"""TCMB resmi serisi: finans disi firmalarin net doviz pozisyonu (NOP).

Kaynak: data/fkdfdvy_2026_07.json (TCMB FKDFDVY, 2008-12..2026-07, mlr $ olarak burada).
NOP: pozitif = acik. DNOP_t = NOP_t - NOP_{t-1}: yillik acik artisi.
"""

import json
import os
import random

from hekis.kalibre import KUR, ols

_YOL = os.path.join(os.path.dirname(__file__), "..", "data", "fkdfdvy_2026_07.json")
_D = json.load(open(_YOL))
DONEM = _D["donem"]
S = {k: [None if v is None else v / 1000.0 for v in vs] for k, vs in _D["seri"].items()}
YIL = {int(p[:4]): i for i, p in enumerate(DONEM) if p.endswith("-12")}

NOP = {t: -S["NOP"][i] for t, i in YIL.items()}              # mlr $, pozitif acik
NOP_2026_07 = -S["NOP"][DONEM.index("2026-07")]
KV_NET = {t: S["KV_NET"][i] for t, i in YIL.items()}
KV_NET_2026_07 = S["KV_NET"][DONEM.index("2026-07")]
DNOP = {t: NOP[t] - NOP[t - 1] for t in range(2009, 2026)}

FAIZ = {2015: 7.6, 2016: 7.6, 2017: 8.0, 2018: 15.6, 2019: 20.6, 2020: 10.2, 2021: 17.8,
        2022: 12.9, 2023: 18.6, 2024: 48.7, 2025: 43.2}  # Drive V22
DEP = {t: (KUR[t] / KUR[t - 1] - 1) * 100 for t in range(2015, 2026)}
CARRY = {t: FAIZ[t] - DEP[t] for t in range(2015, 2026)}
YILLAR = list(range(2015, 2026))


def fit(yillar=YILLAR):
    b, se, r2, res = ols([[1, CARRY[t]] for t in yillar], [DNOP[t] for t in yillar])
    return b, se, r2, res


def bootstrap(n=3000, tohum=5, yillar=YILLAR):
    """(a, c) ciftleri: DNOP = a + c*carry, yillar uzerinden cift yeniden ornekleme."""
    rng = random.Random(tohum)
    out = []
    while len(out) < n:
        ornek = [rng.choice(yillar) for _ in yillar]
        if len(set(CARRY[t] for t in ornek)) < 3:
            continue
        b, _, _, _ = ols([[1, CARRY[t]] for t in ornek], [DNOP[t] for t in ornek])
        out.append((b[0], b[1]))
    return out


_BOOT = None


def boot_havuzu():
    global _BOOT
    if _BOOT is None:
        _BOOT = bootstrap()
    return _BOOT
