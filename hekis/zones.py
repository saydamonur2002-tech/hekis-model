"""Uc bolge: HEKIS (gelir duz memur maasinin altinda), memur kesimi (tampon), luks (ust %20).

Bolgeler bos stokun deger sirasina gore boluk: alt q_h HEKIS havuzu, orta tampon, ust `cut` luks.
Tampon havuza girmez, luks gibi yuksek tarife de gormez: normal piyasa sistemi, genel bedel. Havuza girmeyen bolgeler
bosluga son verebilir (luks tepki fonksiyonu). Havuz Istanbul'un Esenyurt tipi (ucuz) stogundan kurulur, deger sirasinin
altinda yaklasik %41'i orta tip ortalamasinin ~yari degerindedir.

    python -m hekis.zones
"""

from __future__ import annotations

from dataclasses import replace
from statistics import NormalDist

from hekis import activation, final, politics, reality, union
from hekis import evaluate as E
from hekis.bind import inflation_paths, load_obs
from hekis.model import simulate

ND = NormalDist()
LIKELY = dict(g_e=reality.G_ISTANBUL, cap=0.25, coll=0.30, fee=0.01, lux_fee=0.05, lux_coll=0.40, infl_first=reality.INFL_YEAREND_EXP)


def band_factor(a: float, b: float, sigma: float) -> float:
    """Lognormal deger dagilimi, ortalama 1. Degere gore [a, b] yuzdelik bandinin ortalama degeri."""
    za, zb = ND.inv_cdf(a) if a > 0 else -9.0, ND.inv_cdf(b) if b < 1 else 9.0
    return (ND.cdf(zb - sigma) - ND.cdf(za - sigma)) / (b - a)


def run_three_zone(P: dict | None = None, q_h: float | None = None, cut: float = 0.20, sigma: float = 0.6) -> dict:
    P = {**E.BASE, **LIKELY, **(P or {})}
    obs = E.make_obs(P)
    q_h = union.quantile_of_income(union.MEMUR_FLAT) if q_h is None else q_h
    stok = P["stok"]
    S_h, S_l = stok * q_h, stok * cut
    S_b = stok - S_h - S_l
    # havuz: Esenyurt tipi daireler
    units_probe = activation.tier_units(obs, "ucuz", 1000)
    cnt = sum(u.count for u in units_probe)
    val = sum(u.price * u.count for u in units_probe)
    p0 = activation.params(obs)
    hold = (p0.tax_rate * val + p0.unit_fixed * cnt + sum(u.aidat * 12 * u.count for u in units_probe)) / val
    p = activation.participation(P["g_e"], hold, P["fee"], P["slope"], P["cap"])
    n = S_h * p
    rent = sum(u.rent * u.count for u in units_probe) / cnt
    pay, _ = politics.graduated(rent, P["alpha"], q_h, uplift=P["uplift"], eq=P["eq"], scale=P["inc_scale"])
    share = pay / rent
    housed = [replace(u, tenant_pay=u.rent * share) for u in activation.tier_units(obs, "ucuz", n)]
    params = replace(activation.params(obs), utility_sub=politics.monthly_utilities(obs))
    r = simulate(housed, inflation_paths(obs)["ovp"], [1.0] * 20, params)
    first = r.rows[0].subsidy / (1 + r.rows[0].inflation)
    # bedel gelirleri
    orta = activation.tier_units(obs, "orta", 1000)
    mean_orta = sum(u.price * u.count for u in orta) / sum(u.count for u in orta)
    V_h = val / cnt
    rev_pool = S_h * (1 - p) * V_h * P["fee"] * P["coll"]
    V_b = mean_orta * band_factor(q_h, 1 - cut, sigma)
    resp_b = final.lux_response(P["fee"])
    rev_buf = S_b * (1 - resp_b) * V_b * P["fee"] * final.effective_collection(P["fee"], P["coll"])
    V_l = mean_orta * band_factor(1 - cut, 1.0, sigma)
    resp_l = final.lux_response(P["lux_fee"], P["lux_cap"])
    rev_lux = S_l * (1 - resp_l) * V_l * P["lux_fee"] * final.effective_collection(P["lux_fee"], P["lux_coll"])
    rev = rev_pool + rev_buf + rev_lux
    eligible = politics.HOUSEHOLDS * politics.TENANT_SHARE * q_h
    return {"q_h": q_h, "S": (S_h, S_b, S_l), "V": (V_h, V_b, V_l), "p": p, "N": n, "sub1": first, "yuk": r.total_fiscal_real,
            "rev": rev, "rev_parts": (rev_pool, rev_buf, rev_lux), "ratio": rev / first if first > 0 else 0.0,
            "coverage": n / eligible, "freed_buf": S_b * resp_b, "freed_lux": S_l * resp_l, "entry": r.entry_value}


def main() -> int:
    tl = lambda v: f"{v:,.0f}".replace(",", ".")
    bn = lambda v: v / 1e9
    two = E.evaluate(LIKELY)
    q_h = union.quantile_of_income(union.MEMUR_FLAT)
    z = run_three_zone()
    print(f"Uc bolge, en olasi senaryo, Istanbul. HEKIS: gelir duz memur maasinin ({tl(union.MEMUR_FLAT)} TL) altinda = alt %{q_h:.0%}.")
    print(f"Bos stok {tl(E.BASE['stok'])}: HEKIS havuzu {tl(z['S'][0])}, memur kesimi (tampon) {tl(z['S'][1])}, luks {tl(z['S'][2])}.")
    print(f"Ortalama deger (mn TL): havuz {z['V'][0] / 1e6:.2f}, tampon {z['V'][1] / 1e6:.2f}, luks {z['V'][2] / 1e6:.2f}")
    print()
    print(f"{'':<30}{'iki bolge (onceki)':>20}{'uc bolge (tampon)':>20}")
    rows = (
        ("yerlesen daire (bin)", two["N"] / 1000, z["N"] / 1000, "{:.0f}"),
        ("yil-1 sub. (mr TL)", bn(two["sub1"]), bn(z["sub1"]), "{:.1f}"),
        ("bedel geliri (mr TL)", bn(two["rev"]), bn(z["rev"]), "{:.1f}"),
        ("gelir / sub.", two["ratio"], z["ratio"], "{:.2f}"),
        ("20 yil yuk (mr TL)", bn(two["yuk"]), bn(z["yuk"]), "{:.0f}"),
    )
    for name, a, b, f in rows:
        print(f"{name:<30}{f.format(a):>20}{f.format(b):>20}")
    print(f"{'kapsam (uygun kiraciya)':<30}{'':>20}{z['coverage']:>20.1%}")
    print()
    print(f"Bedel geliri parcalari (mr TL): havuza girmeyen {bn(z['rev_parts'][0]):.2f}, tampon {bn(z['rev_parts'][1]):.2f}, luks {bn(z['rev_parts'][2]):.2f}")
    print(f"Bosluktan cikan (havuz disi, ozel piyasaya): tampon {tl(z['freed_buf'])}, luks {tl(z['freed_lux'])} daire")
    print()
    print("Tampon genisligine duyarlilik (HEKIS ust kesimi q_h degisir, luks %20 sabit):")
    print(f"{'q_h':>6}{'hane geliri esigi':>19}{'daire':>8}{'yil-1 sub':>10}{'oran':>6}{'20y yuk':>9}{'tampon payi':>13}")
    for q in (0.30, 0.41, 0.53, 0.65):
        zz = run_three_zone(q_h=q)
        inc = politics.hh_monthly(q)
        print(f"{q:>6.2f}{tl(inc):>19}{zz['N'] / 1000:>7.0f}b{bn(zz['sub1']):>10.1f}{zz['ratio']:>6.2f}{bn(zz['yuk']):>9.0f}{zz['S'][1] / E.BASE['stok']:>13.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
