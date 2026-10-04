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


def lux_factors(sigma: float, cut: float) -> tuple[float, float]:
    """Lognormal deger dagilimi, ortalama sabit. Ust `cut` payi disarida birakilinca:
    kalan ortalama deger carpani, ayrilan ust dilimin ortalama deger carpani."""
    if cut <= 0:
        return 1.0, 0.0
    from statistics import NormalDist
    nd = NormalDist()
    z = nd.inv_cdf(1 - cut)
    low_share = nd.cdf(z - sigma)
    return low_share / (1 - cut), (1 - low_share) / cut


def run_scenario(obs: dict, cap: float, fee: float, collection: float, cut: float = 0.0, sigma: float = 0.6,
                 fee_on_lux: bool = False):
    """cut: orta (Istanbul ortalamasi) tipteki bos stoktan ayrilan luks ust dilim payi. Ucuz (Esenyurt) tipte luks yok varsayilir.
    Luks daireler havuzdan cikar. fee_on_lux: yine de bos tutma bedeli odesinler mi."""
    f_low, f_top = lux_factors(sigma, cut)
    g = activation.expected_real_growth(obs)
    stok_all = obs["bos_stok"]["ibb_elektrik_su_tabanli"]
    stok = stok_all * (1 - 0.5 * cut)
    s_orta = 0.5 * (1 - cut) / (1 - 0.5 * cut)
    # tutma maliyeti orani, kalan karisim
    orta = [replace(u, price=u.price * f_low) for u in activation.tier_units(obs, "orta", 1000 * s_orta)]
    ucuz = activation.tier_units(obs, "ucuz", 1000 * (1 - s_orta))
    mix = orta + ucuz
    cnt = sum(u.count for u in mix)
    val = sum(u.price * u.count for u in mix)
    p0 = activation.params(obs)
    hold = (p0.tax_rate * val + p0.unit_fixed * cnt + sum(u.aidat * 12 * u.count for u in mix)) / val
    p = activation.participation(g, hold, fee, 25.0, cap)
    n = stok * p
    avg_value = val / cnt
    rent = sum(u.rent * u.count for u in mix) / cnt
    pay, _ = politics.graduated(rent, 0.30, 0.4)
    share = pay / rent
    units = []
    units += [replace(u, price=u.price * f_low, tenant_pay=u.rent * share) for u in activation.tier_units(obs, "orta", n * s_orta)]
    units += [replace(u, tenant_pay=u.rent * share) for u in activation.tier_units(obs, "ucuz", n * (1 - s_orta))]
    params = replace(activation.params(obs), utility_sub=politics.monthly_utilities(obs))
    r = simulate(units, inflation_paths(obs)["ovp"], [1.0] * 20, params)
    first = r.rows[0].subsidy / (1 + r.rows[0].inflation)
    revenue = stok * (1 - p) * avg_value * fee * collection
    if fee_on_lux and cut > 0:
        orta_value = [u for u in activation.tier_units(obs, "orta", 1000)]
        mean_orta = sum(u.price * u.count for u in orta_value) / sum(u.count for u in orta_value)
        lux_count = stok_all * 0.5 * cut
        revenue += lux_count * mean_orta * f_top * fee * collection
    return p, n, r, first, revenue


def compare_lux(obs: dict) -> None:
    bn = lambda v: f"{v / 1e9:,.0f}".replace(",", ".")
    print("Luks ust dilim ayrimi: orta tipteki bos stoktan en pahali %20 havuz disi, bos olsa bile. Deger dagilimi lognormal sigma 0,6 (varsayim).")
    print(f"{'sistem':<40}{'durum':<20}{'daire':>8}{'giris mr':>10}{'yil-1 sub':>10}{'20y yuk':>9}{'gelir/sub':>11}")
    for name, cap, fee in SCENARIOS:
        for label, cut, lux_fee in (("tum stok", 0.0, False), ("luks ayrildi", 0.2, False), ("luks ayrildi+bedel", 0.2, True)):
            p, n, r, first, rev = run_scenario(obs, cap, fee, 0.6, cut, 0.6, lux_fee)
            print(f"{name:<40}{label:<20}{n / 1000:>7.0f}b{bn(r.entry_value):>10}{first / 1e9:>10.1f}{bn(r.total_fiscal_real):>9}{rev / first if first else 0:>11.2f}")
        print()
    print("Duyarlilik, karma sistem: luks dilim payi x deger dagilimi sigma (daire bin / 20y yuk mr / gelir-sub., luks bedel disi)")
    print(f"{'ayrilan pay':<14}" + "".join(f"{f'sigma {sg}':>26}" for sg in (0.4, 0.6, 0.8)))
    for cut in (0.2, 0.35, 0.5):
        cells = []
        for sg in (0.4, 0.6, 0.8):
            p, n, r, first, rev = run_scenario(obs, 0.40, 0.01, 0.6, cut, sg)
            cells.append(f"{n / 1000:>6.0f}b /{bn(r.total_fiscal_real):>5} /{rev / first:>5.2f}")
        print(f"{cut:<14.0%}" + "".join(f"{x:>26}" for x in cells))


LUX_CAP = 0.65      # varsayim: bedel ne olursa olsun bosluk bitirebilecek en yuksek pay
LUX_FS = 1.69       # Vancouver ankoru: %3 bedelde bosluk %54 azaldi -> 1 - exp(-3/fs) = 0,54/0,65


def lux_response(fee: float, cap: float = LUX_CAP, fs_pct: float = LUX_FS) -> float:
    """Luks bos daire sahibinin bosluguna son verme orani (satis, kiralama, kendi oturmasi). Havuza girmezler."""
    import math
    return cap * (1 - math.exp(-fee * 100 / fs_pct))


def lux_economics(obs: dict, sigma: float, cut: float, fee_lux: float, collection: float, cap: float = LUX_CAP):
    """Ayrilan luks dilim: adet, ortalama deger, bedel geliri (TL/yil), bosluk bitirme orani."""
    from hekis import politics  # noqa: F401
    f_low, f_top = lux_factors(sigma, cut)
    stok_all = obs["bos_stok"]["ibb_elektrik_su_tabanli"]
    orta = activation.tier_units(obs, "orta", 1000)
    mean_orta = sum(u.price * u.count for u in orta) / sum(u.count for u in orta)
    count = stok_all * 0.5 * cut
    value = mean_orta * f_top
    r = lux_response(fee_lux, cap)
    return count, value, count * (1 - r) * value * fee_lux * collection, r


def compare_lux_fee(obs: dict) -> None:
    sigma, cut = 0.6, 0.2
    print("Luks ust dilim havuz disi, ayri bedel tarifesi. Tepki: Vancouver ankorlu (bedel %3'te bosluk %54 azalir), tavan %65.")
    count, value, _, _ = lux_economics(obs, sigma, cut, 0.03, 0.6)
    print(f"Ayrilan luks bos daire {count:,.0f}, ortalama deger {value / 1e6:.1f} mn TL (orta tip ortalamasinin {lux_factors(sigma, cut)[1]:.1f} kati)".replace(",", "."))
    print()
    for name, cap, fee in SCENARIOS[1:]:
        p, n, r, first, rev_ord = run_scenario(obs, cap, fee, 0.6, cut, sigma, False)
        print(f"{name}: genel bedel {fee:.0%}, yil-1 sub. {first / 1e9:.1f} mr, genel bedel geliri {rev_ord / 1e9:.1f} mr ({rev_ord / first:.2f})")
        print(f"{'luks bedel':>11}{'bosluk biter':>14}{'luks gelir mr':>15}{'toplam gelir/sub':>18}{'(tahsilat luks %40 / %80)':>28}")
        for fl in (0.01, 0.02, 0.03, 0.05, 0.08, 0.12):
            _, _, rev_l, resp = lux_economics(obs, sigma, cut, fl, 0.6)
            lo = lux_economics(obs, sigma, cut, fl, 0.4)[2]
            hi = lux_economics(obs, sigma, cut, fl, 0.8)[2]
            print(f"{fl:>11.0%}{resp:>14.0%}{rev_l / 1e9:>15.1f}{(rev_ord + rev_l) / first:>18.2f}{(rev_ord + lo) / first:>14.2f} /{(rev_ord + hi) / first:>5.2f}")
        # basabas luks bedeli
        need = first - rev_ord
        be = None
        for i in range(1, 400):
            fl = i / 1000
            if lux_economics(obs, sigma, cut, fl, 0.6)[2] >= need:
                be = fl
                break
        print(f"  Luks dilimden kendini finanse etmek icin gereken bedel (tahsilat %60): " + (f"%{be:.1%}" if be else "%40 bile yetmez") + "\n")


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
    print()
    compare_lux(obs)
    print()
    compare_lux_fee(obs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
