"""Bos konut stokunu kullandirma katmani.

Soru: bos duran daireden kac tanesi sisteme girer, girenin bedeli ne olur.
Katilim orani gozlem degil, senaryo girdisidir. Kalibre edilmemis tek en onemli sayi budur.
Tadilat, kiraci bulma gecikmesi ve dairenin oturulabilir olup olmadigi bu blokta yok.

    python -m hekis.activation
"""

from __future__ import annotations

from dataclasses import replace

from hekis.bind import COUNTS, build_units, inflation_paths, load_obs
from hekis.model import Params, UnitType, holding_cost, simulate

TIERS = {
    "orta": ("hekis", "istanbul_ortalama_tl_ay"),
    "ucuz": ("esenyurt_sosyal", "esenyurt_aidat_varsayim_tl_ay"),
}


def tier_units(obs: dict, tier: str, n_units: float) -> list[UnitType]:
    mode, key = TIERS[tier]
    aidat = obs["bos_stok"][key] if key in obs["bos_stok"] else obs["aidat"][key]
    units, _ = build_units(obs, mode, "elektrik", aidat)
    total = sum(COUNTS.values())
    return [replace(u, count=round(n_units * COUNTS[u.name] / total)) for u in units]


def params(obs: dict) -> Params:
    return Params(
        vacancy=obs["vacancy"]["elektrik_abonelik_avrupa_yakasi"],
        collection=0.98,
        rent_index="tufe_ort12",
        horizon=20,
        opex_rate=obs["opex"]["bakim_orani_giris_degeri"],
        tax_rate=obs["opex"]["emlak_vergisi_orani"],
        unit_fixed=obs["opex"]["dask_tl_daire_yil"],
        vacant_aidat=True,
        prev_inflation=obs["inflation_annual"]["2026_agustos_yoy"],
    )


def run(obs: dict, shares: dict[str, float], n_units: float):
    units: list[UnitType] = []
    for tier, share in shares.items():
        units += tier_units(obs, tier, n_units * share)
    index = [1.0] * 20
    return simulate(units, inflation_paths(obs)["ovp"], index, params(obs), name="aktivasyon")


def owner_vacant_cost(obs: dict, tier: str) -> float:
    """Dairenin bos durmasinin sahibe yillik maliyeti. Bakim yok, oturulmayan daire."""
    p = params(obs)
    units = tier_units(obs, tier, sum(COUNTS.values()))
    value = sum(u.count * u.price for u in units)
    cost = (p.tax_rate * value + p.unit_fixed * sum(u.count for u in units)
            + sum(u.aidat * 12 * u.count for u in units))
    return cost / sum(u.count for u in units)


WINDOW = 1  # hekis.calibrate secti, ama farklar anlamsiz kucuk


def expected_real_growth(obs: dict, year: str | None = None, window: int | None = None) -> float:
    """Sahibin reel fiyat beklentisi: son `window` gozlemin ortalamasi.
    year verilirse o yildan onceki yillar, yoksa 2025 ve 2026 Agustos yillik dahil son gozlemler."""
    w = window or WINDOW
    k = obs["kfe_reel_yillik"]
    if year is None:
        series = [k[str(y)] for y in range(2013, 2026)] + [k["2026_agustos_yillik"]]
    else:
        series = [k[str(y)] for y in range(2013, int(year))]
    return sum(series[-w:]) / w


def participation(g_e: float, hold_cost: float, fee: float = 0.0, slope: float = 25.0, cap: float = 0.40) -> float:
    """Senet reel getirisi 0. Tutma getirisi g_e - maliyet - bos tutma bedeli.
    Katilim = cap * lojistik(slope * (maliyet + bedel - g_e)). slope ve cap kalibre degil, varsayimdir.
    cap: bos stoktan finansal amacla tutulan ve kullanima uygun pay."""
    import math
    adv = hold_cost + fee - g_e
    return cap / (1 + math.exp(-slope * adv))


def hold_cost_ratio(obs: dict) -> float:
    """Bos dairenin yillik gideri / deger, iki semtin agirlikli ortalamasi."""
    vals = []
    for tier in TIERS:
        units = tier_units(obs, tier, sum(COUNTS.values()))
        v = sum(u.count * u.price for u in units)
        vals.append((owner_vacant_cost(obs, tier) * sum(u.count for u in units)) / v)
    return sum(vals) / len(vals)


def simulate_outcome(obs: dict) -> None:
    tl = lambda v: f"{v:,.0f}".replace(",", ".")
    bn = lambda v: f"{v / 1e9:,.1f}".replace(",", ".")
    c = hold_cost_ratio(obs)
    print(f"Sahibin bos tutma maliyeti: degerin yilda %{c:.2%}")
    print()
    print("Geriye donuk: o yil bu kural isleseydi katilim ne olurdu (cap %40, slope 25: varsayim)")
    print(f"{'yil':<8}{'beklenen reel artis':>22}{'katilim (bedelsiz)':>20}")
    for y in range(2020, 2027):
        g = expected_real_growth(obs, str(y))
        print(f"{y:<8}{g:>22.1%}{participation(g, c):>20.1%}")
    g = expected_real_growth(obs)
    print(f"{'bugun':<8}{g:>22.1%}{participation(g, c):>20.1%}")
    print()
    stok = obs["bos_stok"]
    print("Bos tutma bedeli etkisi (yilda degerin yuzdesi), 225 bin / 450 bin bos stok, yari orta yari ucuz semt")
    print(f"{'rejim':<26}{'bedel':>7}{'katilim':>9}{'daire (225b)':>14}{'daire (450b)':>14}{'giris mr (450b)':>17}{'20y odenen':>12}{'yuk mr (450b)':>15}")
    regimes = (("bugun (durgun)", g), ("patlama (2023 beklentisi)", expected_real_growth(obs, "2023")))
    for name, ge in regimes:
        for fee in (0.0, 0.002, 0.01, 0.02):
            p = participation(ge, c, fee)
            n1, n2 = stok["elektrik_aboneligi_tabanli"] * p, stok["ibb_elektrik_su_tabanli"] * p
            if n2 < 1:
                print(f"{name:<26}{fee:>7.1%}{p:>9.1%}{tl(n1):>14}{tl(n2):>14}{'-':>17}{'-':>12}{'-':>15}")
                continue
            r = run(obs, {"orta": 0.5, "ucuz": 0.5}, n2)
            print(f"{name:<26}{fee:>7.1%}{p:>9.1%}{tl(n1):>14}{tl(n2):>14}{bn(r.entry_value):>17}{r.real_eroded:>12.0%}{bn(r.total_fiscal_real):>15}")
    print()
    n = stok["ibb_elektrik_su_tabanli"] * participation(g, c, 0.01)
    print(f"Ornek: bedel %1, bugunku rejim, 450 bin: {tl(n)} daire = Istanbul stokunun %{n / stok['istanbul_konut_stoku']:.1%}")


def main() -> int:
    obs = load_obs()
    tl = lambda v: f"{v:,.0f}".replace(",", ".")
    bn = lambda v: f"{v / 1e9:,.1f}".replace(",", ".")
    n = 1000
    print("Daire basina (1000 daire, 40/40/20 tip dagilimi). Bugunku TL.")
    print(f"{'semt':<6}{'fiyat':>12}{'sahip bos maliyeti/yil':>26}{'sosyal sub./yil':>18}{'20y odenen':>12}{'yuk/daire (20y)':>17}")
    for tier in TIERS:
        r = run(obs, {tier: 1.0}, n)
        value = r.entry_value / n
        sub = r.rows[0].subsidy / (1 + r.rows[0].inflation) / n
        print(f"{tier:<6}{tl(value):>12}{tl(owner_vacant_cost(obs, tier)):>26}{tl(sub):>18}{r.real_eroded:>12.0%}{tl(r.total_fiscal_real / n):>17}")
    print()
    print("Olcek: Istanbul bos stoku x katilim, yarisi orta yarisi ucuz semt (oran varsayim).")
    stok = obs["bos_stok"]
    print(f"{'bos stok':<26}{'katilim':>9}{'daire':>10}{'giris degeri mr':>17}{'20y odenen':>12}{'yuk mr (20y)':>14}")
    for label, v in (("225 bin (elektrik)", stok["elektrik_aboneligi_tabanli"]), ("450 bin (IBB)", stok["ibb_elektrik_su_tabanli"])):
        for take in (0.05, 0.10, 0.25):
            units = v * take
            r = run(obs, {"orta": 0.5, "ucuz": 0.5}, units)
            print(f"{label:<26}{take:>9.0%}{tl(units):>10}{bn(r.entry_value):>17}{r.real_eroded:>12.0%}{bn(r.total_fiscal_real):>14}")
    print()
    simulate_outcome(obs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
