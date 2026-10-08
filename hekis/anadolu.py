"""Anadolu buyuksehirleri (Ankara, Izmir, Bursa, Antalya, Konya, Adana, Kocaeli): uc bolgeli model ve tarife.

Sehre ozgu: fiyat/kira carpani (Istanbul'a gore), hane buyuklugu, gelir olcegi, HEKIS gelir esigi (duz memur maasi ulusal sabit,
sehir gelirleri farkli oldugu icin ayni maas farkli yuzdelige denk gelir), bos stok (kisi basi Istanbul ile ayni, varsayim).

    python -m hekis.anadolu
"""

from __future__ import annotations

from hekis import cities, politics, union, zones
from hekis.bind import load_obs

ANADOLU = ("ankara", "izmir", "bursa", "antalya", "konya", "adana", "kocaeli")
GRID_FEE = (0.0025, 0.005, 0.0075, 0.01, 0.015)
GRID_LUX = (0.01, 0.02, 0.03, 0.04, 0.05)


def city_setup(obs: dict, city: str) -> dict:
    d = obs["sehirler"][city]
    ci = cities.city_inputs(obs, city)
    s = d["gelir_orani"] / politics.ISTANBUL_TR10_RATIO   # Istanbul bazi = 1,0
    return {
        **ci, "s": s, "hh_size": d["hane_buyuklugu"],
        "households": d["nufus"] / d["hane_buyuklugu"],
        "q_h": union.quantile_of_income(union.MEMUR_FLAT, scale=s),
    }


def run(obs: dict, city: str, fee: float | None = None, lux_fee: float | None = None, **kw) -> dict:
    cs = city_setup(obs, city)
    P = {"stok": cs["stok"], "g_e": cs["g_e"], "inc_scale": cs["s"]}
    if fee is not None:
        P["fee"] = fee
    if lux_fee is not None:
        P["lux_fee"] = lux_fee
    z = zones.run_three_zone(P=P, q_h=cs["q_h"], obs_mut=cities.mutator(cs["fp"], cs["fr"]),
                             households=cs["households"], **kw)
    return {**z, **{k: cs[k] for k in ("pop", "stok", "s", "q_h", "households", "veri")}}


def main() -> int:
    obs = load_obs()
    tl = lambda v: f"{v:,.0f}".replace(",", ".")
    print("Anadolu buyuksehirleri, uc bolgeli model, Istanbul tarifesi (genel %1, luks %5), en olasi senaryo, guncel veri.")
    print(f"{'sehir':<9}{'nufus mn':>9}{'HEKIS esigi':>12}{'bos stok':>10}{'daire':>7}{'sub mr':>8}{'bedel':>7}{'oran':>6}{'yuk mr':>8}{'kapsam':>8}  veri")
    tot = {"N": 0.0, "sub1": 0.0, "rev": 0.0, "yuk": 0.0, "stok": 0.0, "elig": 0.0}
    for c in ANADOLU:
        o = run(obs, c)
        elig = o["households"] * politics.TENANT_SHARE * o["q_h"]
        print(f"{cities.TITLE[c]:<9}{o['pop'] / 1e6:>9.2f}{o['q_h']:>12.0%}{tl(o['stok']):>10}{o['N'] / 1000:>6.0f}b{o['sub1'] / 1e9:>8.2f}{o['rev'] / 1e9:>7.2f}{o['ratio']:>6.2f}{o['yuk'] / 1e9:>8.0f}{o['coverage']:>8.1%}  {obs['sehirler'][c]['gelir_veri'].split(':')[0]}")
        for k, v in (("N", o["N"]), ("sub1", o["sub1"]), ("rev", o["rev"]), ("yuk", o["yuk"]), ("stok", o["stok"]), ("elig", elig)):
            tot[k] += v
    print(f"{'TOPLAM':<9}{'':>9}{'':>12}{tl(tot['stok']):>10}{tot['N'] / 1000:>6.0f}b{tot['sub1'] / 1e9:>8.2f}{tot['rev'] / 1e9:>7.2f}{tot['rev'] / tot['sub1']:>6.2f}{tot['yuk'] / 1e9:>8.0f}{tot['N'] / tot['elig']:>8.1%}")
    print()
    print("Ayni oran icin gereken en dusuk tarife (genel bedel, luks bedel) sehir sehir, oran >= 1,0 ve >= 1,2:")
    print(f"{'sehir':<9}{'oran>=1,0':>22}{'oran>=1,2':>22}")
    for c in ANADOLU:
        res = []
        for target in (1.0, 1.2):
            best = None
            for fee in GRID_FEE:
                for lux in GRID_LUX:
                    r = run(obs, c, fee=fee, lux_fee=lux)["ratio"]
                    if r >= target and (best is None or (fee + lux / 5, fee, lux) < (best[0] + best[1] / 5, best[0], best[1])):
                        best = (fee, lux, r)
            res.append("hicbiri yetmez" if best is None else f"genel {best[0]:.2%}, luks {best[1]:.0%}")
        print(f"{cities.TITLE[c]:<9}{res[0]:>22}{res[1]:>22}")
    print()
    print("Tarife secenekleri, 7 sehir toplami: finansman (oran) ve bosluktan cikan daire (havuz disi, ozel piyasaya).")
    print(f"{'genel':>7}{'luks':>6}{'HEKIS daire':>13}{'sub mr':>8}{'bedel mr':>9}{'oran':>6}{'bosluktan cikan':>17}{'20y yuk':>9}")
    for fee, lux in ((0.0025, 0.01), (0.005, 0.02), (0.005, 0.03), (0.0075, 0.03), (0.01, 0.05)):
        n = sub = rev = yuk = freed = 0.0
        for c in ANADOLU:
            o = run(obs, c, fee=fee, lux_fee=lux)
            n += o["N"]; sub += o["sub1"]; rev += o["rev"]; yuk += o["yuk"]; freed += o["freed_buf"] + o["freed_lux"]
        print(f"{fee:>7.2%}{lux:>6.0%}{n / 1000:>12.0f}b{sub / 1e9:>8.2f}{rev / 1e9:>9.2f}{rev / sub:>6.2f}{tl(freed):>17}{yuk / 1e9:>9.0f}")
    print()
    print("Sehir bazli esikler: luks (deger siralamasinin ust %20'si, sigma 0,6) ve HEKIS gelir esigi (duz memur maasi 55.000 TL).")
    print(f"{'sehir':<9}{'ort. deger':>12}{'luks esigi TL':>15}{'HEKIS altin %':>15}")
    import math
    from statistics import NormalDist
    z80 = NormalDist().inv_cdf(0.8)
    for c in ("istanbul",) + ANADOLU:
        d = obs["sehirler"][c]
        q = city_setup(obs, c)["q_h"]
        thr = d["satis"] * math.exp(-0.6 ** 2 / 2 + 0.6 * z80)
        print(f"{cities.TITLE[c]:<9}{tl(d['satis']):>12}{tl(thr):>15}{q:>14.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
