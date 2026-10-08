"""Subvansiyon ayrimi: havuz sahibe piyasa kirasini oder, oturan sosyal kira oder, fark butcedir.

    python -m hekis.subsidy
"""

from __future__ import annotations

from dataclasses import replace

from hekis import activation
from hekis.bind import inflation_paths, load_obs
from hekis.model import simulate

N = 161_000  # mevcut karma senaryo, 450 bin bos stoktan


def units_with_tenant_share(obs: dict, share: float | None):
    """share None: sosyal kira (mevcut). Aksi halde oturan, sahibe odenen kiranin share'i kadar oder."""
    units = []
    for tier in ("orta", "ucuz"):
        for u in activation.tier_units(obs, tier, N * 0.5):
            units.append(u if share is None else replace(u, tenant_pay=u.rent * share))
    return units


def run(obs: dict, share: float | None):
    index = [1.0] * 20
    return simulate(units_with_tenant_share(obs, share), inflation_paths(obs)["ovp"], index, activation.params(obs))


def main() -> int:
    obs = load_obs()
    bn = lambda v: f"{v / 1e9:,.0f}".replace(",", ".")
    print(f"{N:,} daire, yari orta yari ucuz semt. Bugunku TL.".replace(",", "."))
    print(f"{'oturan oder':<30}{'yil-1 sub. (mr)':>17}{'20y yuk (mr)':>14}{'20y odenen':>12}")
    for label, share in (("sosyal kira (12/10/8 bin)", None), ("kiranin %60'i", 0.6), ("kiranin %80'i", 0.8), ("kiranin %100'u (sub. yok)", 1.0)):
        r = run(obs, share)
        first = r.rows[0].subsidy / (1 + r.rows[0].inflation)
        print(f"{label:<30}{bn(first):>17}{bn(r.total_fiscal_real):>14}{r.real_eroded:>12.0%}")
    r = run(obs, None)
    sub = sum(x.subsidy / x.cpi for x in r.rows)
    prem = sum(x.premium / x.cpi for x in r.rows)
    gap = sum(x.fiscal_gap / x.cpi for x in r.rows)
    print()
    print(f"Yuk kirilimi (sosyal kira): subvansiyon {bn(sub)} mr, prim {bn(prem)} mr, havuz acigi {bn(gap)} mr")
    per = sub / N
    print(f"Daire basina 20 yil subvansiyon: {per:,.0f} TL (yilda {per / 20:,.0f} TL, ayda {per / 240:,.0f} TL)".replace(",", "."))
    soc = obs["social_rent"]
    print(f"Sosyal kira 2+1 {soc['2+1']:,} TL, Esenyurt 2+1 piyasa {obs['rent']['esenyurt_2_1_tl']:,} TL, Istanbul ort. 2+1 {obs['rent']['istanbul_m2_tl'] * 95:,.0f} TL".replace(",", "."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
