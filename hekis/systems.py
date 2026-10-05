"""Iki ayri HEKIS sistemi, ayni islev: Istanbul ve Anadolu (7 buyuksehir). Kademeli genisleme, sok ve sosyal etki ayri ayri islenir.

Her sistemin: tam olcegi (bos stok), kendi tarifesi, hane/kiraci sayisi, uygun kiraci sayisi ve calistirici (runner). Anadolu runner'i
7 sehri kendi fiyat/kira/gelir/hane verisiyle calistirir ve toplar; olcek sehirlere bos stok payina gore bolunur.
Anadolu pilotu da toplam olarak 3.800 birimle baslar (sehirlere paylastirilmis; tek sehir pilotu daha gercekci olur).

    python -m hekis.systems
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from hekis import anadolu, cities, evaluate as E, politics, zones
from hekis.bind import load_obs

NATIONAL_POP = 86_092_168
NATIONAL_HH_SIZE = 3.09   # Istanbul degeri; ulusal ortalama icin yaklasik, dogrulanmadi


@dataclass
class System:
    name: str
    full: float
    base: dict
    households: float
    eligible: float                 # uygun kiraci hane (gelir esiginin altindaki kiraci)
    runner: Callable[[dict, float], dict]
    key: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def tenants(self) -> float:
        return self.households * politics.TENANT_SHARE

    @property
    def national_share(self) -> float:
        return self.households / (NATIONAL_POP / NATIONAL_HH_SIZE)


def _istanbul() -> System:
    base = {"fee": 0.01, "lux_fee": 0.05}
    q_h = zones.run_three_zone()["q_h"]
    hh = politics.HOUSEHOLDS
    return System("Istanbul", float(E.BASE["stok"]), base, hh, hh * politics.TENANT_SHARE * q_h,
                  lambda P, stok: zones.run_three_zone(P={**zones.LIKELY, **P, "stok": stok}), key="istanbul")


def _anadolu(tariff: tuple[float, float] = (0.005, 0.03)) -> System:
    obs = load_obs()
    setups = {c: anadolu.city_setup(obs, c) for c in anadolu.ANADOLU}
    total = sum(cs["stok"] for cs in setups.values())
    hh = sum(cs["households"] for cs in setups.values())
    elig = sum(cs["households"] * politics.TENANT_SHARE * cs["q_h"] for cs in setups.values())

    def runner(P: dict, stok: float) -> dict:
        agg = {"N": 0.0, "sub1": 0.0, "rev": 0.0, "yuk": 0.0, "freed_buf": 0.0, "freed_lux": 0.0}
        S = [0.0, 0.0, 0.0]
        for c, cs in setups.items():
            Pc = {k: v for k, v in P.items() if k not in ("stok", "g_e", "inc_scale")}
            Pc["stok"] = stok * cs["stok"] / total
            Pc["g_e"] = cs["g_e"] + (P.get("g_e", zones.LIKELY["g_e"]) - zones.LIKELY["g_e"])
            Pc["inc_scale"] = cs["s"] * P.get("inc_scale", E.BASE["inc_scale"]) / E.BASE["inc_scale"]
            z = zones.run_three_zone(P={**zones.LIKELY, **Pc}, q_h=cs["q_h"], obs_mut=cities.mutator(cs["fp"], cs["fr"]),
                                     households=cs["households"])
            for k in agg:
                agg[k] += z[k]
            for i in range(3):
                S[i] += z["S"][i]
        agg["S"] = tuple(S)
        agg["ratio"] = agg["rev"] / agg["sub1"] if agg["sub1"] > 0 else 0.0
        agg["p"] = agg["N"] / S[0] if S[0] > 0 else 0.0
        agg["V"] = (0.0, 0.0, 0.0)
        return agg

    s_avg = sum(cs["s"] * cs["households"] for cs in setups.values()) / hh
    return System("Anadolu (7 sehir)", total, {"fee": tariff[0], "lux_fee": tariff[1]}, hh, elig, runner, key="anadolu", extra={"s": s_avg})


ISTANBUL = _istanbul()
ANADOLU = _anadolu()


def main() -> int:
    tl = lambda v: f"{v:,.0f}".replace(",", ".")
    print(f"{'sistem':<20}{'tam olcek (bos stok)':>22}{'hane mn':>9}{'kiraci mn':>11}{'uygun kiraci':>14}{'tarife (genel/luks)':>21}")
    for s in (ISTANBUL, ANADOLU):
        print(f"{s.name:<20}{tl(s.full):>22}{s.households / 1e6:>9.2f}{s.tenants / 1e6:>11.2f}{tl(s.eligible):>14}{s.base['fee']:>12.2%}/{s.base['lux_fee']:.0%}")
        z = s.runner({**zones.LIKELY, **s.base}, s.full)
        print(f"{'':<20}tam olcek: {tl(z['N'])} hane, sub {z['sub1'] / 1e9:.2f} mr, bedel {z['rev'] / 1e9:.2f} mr, oran {z['ratio']:.2f}, kapsam %{z['N'] / s.eligible:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
