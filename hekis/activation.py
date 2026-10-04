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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
