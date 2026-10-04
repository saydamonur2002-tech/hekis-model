"""Revize model, tek kosu: katilim x dereceli kira x abonelik subvansiyonu x bedel geliri.

Sabit tutulanlar: aidat havuzda, oturan dereceli kira (a %30, alt %40), abonelik tam sübvansiyon.

    python -m hekis.final
"""

from __future__ import annotations

from dataclasses import replace

from hekis import activation, politics
from hekis.bind import inflation_paths, load_obs
from hekis.model import simulate

SCENARIOS = (
    ("gonullu tek basina", 0.05, 0.0),
    ("karma (bedel %1, tavan %40)", 0.40, 0.01),
    ("Vancouver benzeri (bedel %3, tavan %55)", 0.55, 0.03),
)


def run_scenario(obs: dict, cap: float, fee: float, collection: float):
    g = activation.expected_real_growth(obs)
    c = activation.hold_cost_ratio(obs)
    stok = obs["bos_stok"]["ibb_elektrik_su_tabanli"]
    p = activation.participation(g, c, fee, 25.0, cap)
    n = stok * p
    rent, _, value = politics.blend_units(obs, max(n, 1000))
    pay, _ = politics.graduated(rent, 0.30, 0.4)
    share = pay / rent
    units = []
    for tier in ("orta", "ucuz"):
        units += [replace(u, tenant_pay=u.rent * share) for u in activation.tier_units(obs, tier, n * 0.5)]
    params = replace(activation.params(obs), utility_sub=politics.monthly_utilities(obs))
    r = simulate(units, inflation_paths(obs)["ovp"], [1.0] * 20, params)
    first = r.rows[0].subsidy / (1 + r.rows[0].inflation)
    revenue = stok * (1 - p) * value * fee * collection
    return p, n, r, first, revenue


def main() -> int:
    obs = load_obs()
    g = activation.expected_real_growth(obs)
    print(f"Beklenen reel konut artisi {g:.1%}, tutma maliyeti degerin %{activation.hold_cost_ratio(obs):.2%}'si. 450 bin bos stok.")
    print("Aidat havuzda, oturan dereceli kira (a=%30, alt %40), abonelik tam subvanse. Bugunku TL.")
    print()
    head = f"{'senaryo':<42}{'katilim':>8}{'daire':>9}{'giris mr':>10}{'odenen':>8}{'yil-1 sub':>10}{'20y yuk':>9}"
    print(head)
    for name, cap, fee in SCENARIOS:
        p, n, r, first, _ = run_scenario(obs, cap, fee, 0.6)
        print(f"{name:<42}{p:>8.1%}{n / 1000:>8.0f}b{r.entry_value / 1e9:>10.0f}{r.real_eroded:>8.0%}{first / 1e9:>10.1f}{r.total_fiscal_real / 1e9:>9.0f}")
    print()
    print("Bedel geliri / yil-1 subvansiyon, etkin tahsilat bazinda")
    print(f"{'senaryo':<42}" + "".join(f"{f'tahsilat %{int(c * 100)}':>14}" for c in (0.15, 0.30, 0.60, 0.90)))
    for name, cap, fee in SCENARIOS:
        row = []
        for coll in (0.15, 0.30, 0.60, 0.90):
            _, _, _, first, rev = run_scenario(obs, cap, fee, coll)
            row.append(f"{rev / first:>14.2f}")
        print(f"{name:<42}" + "".join(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
