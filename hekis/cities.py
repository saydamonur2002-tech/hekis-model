"""Istanbul ve 7 buyuksehir. Gerisi hesaba katilmaz.

Her sehir icin fiyat ve kira carpani Istanbul'a gore (ortalama satis fiyati ve ortalama kira orani), bos stok kisi basi
Istanbul ile ayni, hane ve kiraci payi ulusal, gelir dagilimi ulusal. Kocaeli, Konya, Adana fiyat/kira verisi yer tutucudur.

    python -m hekis.cities
"""

from __future__ import annotations

from hekis import evaluate as E, politics, reality
from hekis.bind import load_obs

CITIES = ("istanbul", "ankara", "izmir", "bursa", "antalya", "konya", "adana", "kocaeli")
TITLE = {"istanbul": "Istanbul", "ankara": "Ankara", "izmir": "Izmir", "bursa": "Bursa", "antalya": "Antalya",
         "konya": "Konya", "adana": "Adana", "kocaeli": "Kocaeli"}
LIKELY = dict(cap=0.25, coll=0.30, fee=0.01, lux_fee=0.05, lux_coll=0.40, infl_first=reality.INFL_YEAREND_EXP)
G_NATIONAL = -0.065


def city_inputs(obs: dict, city: str) -> dict:
    c = obs["sehirler"]
    d = c[city]
    ist = c["istanbul"]
    fp = d["satis"] / ist["satis"]
    fr = d["kira"] / ist["kira"]
    pop = d["nufus"]
    return {
        "fp": fp, "fr": fr, "pop": pop,
        "stok": pop * c["bos_stok_kisi_basi"],
        "households": pop / c["hane_buyuklugu"],
        "g_e": G_NATIONAL + d["reel_gelir_artis_farki"],
        "veri": d["veri"],
    }


def mutator(fp: float, fr: float):
    def mut(obs: dict) -> None:
        obs["sale"]["istanbul_m2_tl"] *= fp
        obs["sale"]["esenyurt_m2_tl"] *= fp
        for k in ("esenyurt_2_1_tl", "esenyurt_1_1_tl", "esenyurt_1_0_tl"):
            obs["rent"][k] *= fr
        for k in ("2+1", "1+1", "1+0"):
            obs["policy_rent"][k] *= fr
        obs["aidat"]["istanbul_ortalama_tl_ay"] *= fr
        obs["bos_stok"]["esenyurt_aidat_varsayim_tl_ay"] *= fr
    return mut


def run_city(obs: dict, city: str, P: dict | None = None) -> dict:
    ci = city_inputs(obs, city)
    params = {**LIKELY, **(P or {}), "stok": ci["stok"], "g_e": ci["g_e"]}
    o = E.evaluate(params, obs_mut=mutator(ci["fp"], ci["fr"]))
    o.update(ci)
    return o


def main() -> int:
    obs = load_obs()
    tl = lambda v: f"{v:,.0f}".replace(",", ".")
    print("Istanbul ve 7 buyuksehir, en olasi senaryo (tavan %25, bedel %1, tahsilat %30, luks bedel %5), guncel veri.")
    print("Gerisi (diger 22 buyuksehir ve iller) hesap disi.")
    print()
    print(f"{'sehir':<10}{'nufus mn':>9}{'bos stok':>10}{'fiyat/ist':>10}{'kira/ist':>9}{'g_e':>7}{'daire':>8}{'yil-1 sub':>10}{'bedel':>7}{'oran':>6}{'acik':>7}{'20y yuk':>9}  veri")
    rows = []
    for c in CITIES:
        o = run_city(obs, c)
        rows.append((c, o))
        print(f"{TITLE[c]:<10}{o['pop'] / 1e6:>9.2f}{tl(o['stok']):>10}{o['fp']:>10.2f}{o['fr']:>9.2f}{o['g_e']:>7.1%}{o['N'] / 1000:>7.0f}b{o['sub1'] / 1e9:>10.2f}{o['rev'] / 1e9:>7.2f}{o['ratio']:>6.2f}{o['deficit'] / 1e9:>7.2f}{o['yuk'] / 1e9:>9.0f}  {o['veri'].split(':')[0]}")
    tot = {k: sum(o[k] for _, o in rows) for k in ("N", "sub1", "rev", "yuk", "stok", "pop", "households", "deficit")}
    print(f"{'TOPLAM':<10}{tot['pop'] / 1e6:>9.2f}{tl(tot['stok']):>10}{'':>10}{'':>9}{'':>7}{tot['N'] / 1000:>7.0f}b{tot['sub1'] / 1e9:>10.2f}{tot['rev'] / 1e9:>7.2f}{tot['rev'] / tot['sub1']:>6.2f}{tot['deficit'] / 1e9:>7.2f}{tot['yuk'] / 1e9:>9.0f}")
    ist = rows[0][1]
    print(f"  mr TL/yil, bugunku TL. Istanbul payi: daire %{ist['N'] / tot['N']:.0%}, sub. %{ist['sub1'] / tot['sub1']:.0%}.")
    print(f"  8 sehir nufusu Turkiye'nin %{tot['pop'] / 86_092_168:.0%}'i, hane {tot['households'] / 1e6:.1f} mn, kiraci hane {tot['households'] * obs['sehirler']['kiraci_payi'] / 1e6:.1f} mn.")
    print()
    H = tot["households"]
    N, sub1 = tot["N"], tot["sub1"]
    B = sub1 / N
    g0, g1, p0, p1 = reality.gini_with_benefit(N, B, households=H)
    tenants = H * obs["sehirler"]["kiraci_payi"]
    eligible = tenants * 0.4
    print("Etki, 8 sehir nufusu uzerinde (gelir dagilimi ulusal varsayim):")
    print(f"  Yerlesen {tl(N)} hane (uygun alt %40 kiracinin %{N / eligible:.1%}'i), hane basina ayda {tl(B / 12)} TL")
    print(f"  Gini {g0:.4f} -> {g1:.4f} ({g1 - g0:+.4f}), goreli yoksulluk {p0:.2%} -> {p1:.2%} ({(p1 - p0) * 100:+.2f} puan)")
    ds = N / tenants
    print(f"  Kira piyasasi: kiraci haneye gore %{ds:.2%} -> kira yaklasik %{-ds / 0.3:+.1%} (esneklik 0,3) ile %{-ds / 1.0:+.1%} (esneklik 1,0)")
    print()
    print("Yalniz Istanbul ile 8 sehrin karsilastirmasi (ayni senaryo):")
    print(f"  Istanbul tek basina: {ist['N'] / 1000:.0f} bin daire, oran {ist['ratio']:.2f}, acik {ist['deficit'] / 1e9:.2f} mr")
    print(f"  8 sehir toplam:      {tot['N'] / 1000:.0f} bin daire, oran {tot['rev'] / tot['sub1']:.2f}, acik {tot['deficit'] / 1e9:.2f} mr")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
