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


def run_three_zone(P: dict | None = None, q_h: float | None = None, cut: float = 0.20, sigma: float = 0.6,
                   fee_buffer: float | None = None, lux_vac: float | None = None, premium: float = 0.0,
                   pool_rent_mult: float = 1.0, senet_coupling: bool = True, obs_mut=None,
                   households: float | None = None, tenant_share: float | None = None) -> dict:
    """fee_buffer: tampon bedeli (varsayilan genel bedel). lux_vac: luks bandinin bos stoktaki payi (varsayilan cut: bosluk
    deger sirasina esit dagilmis). Daha buyukse bosluk luks bandina kaymistir, kalan havuz ve tampon arasinda
    q_h : (1 - q_h - cut) oraninda bolunur."""
    P = {**E.BASE, **LIKELY, **(P or {})}
    obs = E.make_obs(P)
    if obs_mut is not None:
        obs_mut(obs)
    q_h = union.quantile_of_income(union.MEMUR_FLAT) if q_h is None else q_h
    stok = P["stok"]
    fee_b = P["fee"] if fee_buffer is None else fee_buffer
    lv = cut if lux_vac is None else lux_vac
    S_l = stok * lv
    rest = stok - S_l
    S_h = rest * q_h / (q_h + (1 - q_h - cut))
    S_b = rest - S_h
    # havuz: Esenyurt tipi daireler
    units_probe = activation.tier_units(obs, "ucuz", 1000)
    cnt = sum(u.count for u in units_probe)
    val = sum(u.price * u.count for u in units_probe)
    p0 = activation.params(obs)
    hold = (p0.tax_rate * val + p0.unit_fixed * cnt + sum(u.aidat * 12 * u.count for u in units_probe)) / val
    # Sahibin senede karsilik kabul ettigi kira carpani: havuz m x piyasa kirasi alir, oturan payi ayri (dereceli).
    # Baglanti (varsayim): geri odeme (1-m) x brut kira kadar yavaslar, sahibin senet getirisi -lambda x (1-m).
    rent_full = sum(u.rent * u.count for u in units_probe) / cnt
    lam = rent_full * 12 * (1 - p0.vacancy) * p0.collection / (val / cnt)
    s_ret = -lam * (1 - pool_rent_mult) if senet_coupling else 0.0
    p = activation.participation(P["g_e"], hold + s_ret + premium, P["fee"], P["slope"], P["cap"])  # premium: katilan sahibe yillik odenen, degerin yuzdesi
    n = S_h * p
    rent = rent_full * pool_rent_mult
    pay, _ = politics.graduated(rent, P["alpha"], q_h, uplift=P["uplift"], eq=P["eq"], scale=P["inc_scale"])
    share = pay / rent
    housed = [replace(u, tenant_pay=u.rent * share) for u in activation.tier_units(obs, "ucuz", n, rent_mult=pool_rent_mult)]
    params = replace(activation.params(obs), utility_sub=politics.monthly_utilities(obs))
    r = simulate(housed, inflation_paths(obs)["ovp"], [1.0] * 20, params)
    first = r.rows[0].subsidy / (1 + r.rows[0].inflation)
    # bedel gelirleri
    orta = activation.tier_units(obs, "orta", 1000)
    mean_orta = sum(u.price * u.count for u in orta) / sum(u.count for u in orta)
    V_h = val / cnt
    rev_pool = S_h * (1 - p) * V_h * P["fee"] * P["coll"]
    V_b = mean_orta * band_factor(q_h, 1 - cut, sigma)
    resp_b = final.lux_response(fee_b)
    rev_buf = S_b * (1 - resp_b) * V_b * fee_b * final.effective_collection(fee_b, P["coll"])
    V_l = mean_orta * band_factor(1 - cut, 1.0, sigma)
    resp_l = final.lux_response(P["lux_fee"], P["lux_cap"])
    rev_lux = S_l * (1 - resp_l) * V_l * P["lux_fee"] * final.effective_collection(P["lux_fee"], P["lux_coll"])
    rev = rev_pool + rev_buf + rev_lux
    eligible = politics.HOUSEHOLDS * politics.TENANT_SHARE * q_h
    prem_cost = n * V_h * premium
    return {"q_h": q_h, "prem_cost": prem_cost, "balance": rev - first - prem_cost, "S": (S_h, S_b, S_l), "V": (V_h, V_b, V_l), "p": p, "N": n, "sub1": first, "yuk": r.total_fiscal_real,
            "rev": rev, "rev_parts": (rev_pool, rev_buf, rev_lux), "ratio": rev / first if first > 0 else 0.0,
            "coverage": n / eligible, "paid": r.real_eroded, "s_ret": s_ret, "freed_buf": S_b * resp_b, "freed_lux": S_l * resp_l, "entry": r.entry_value}


def solve_premium(**kw) -> dict:
    """Bedel gelirinin sub. ustunde kalan fazlasi katilim primine gider. Butce dengeli en buyuk prim, ama tavana
    ulasilinca durur (bundan sonraki prim bosa gider)."""
    base = run_three_zone(**kw)
    if base["balance"] <= 0:
        return {**base, "premium": 0.0, "base_N": base["N"]}
    cap_n = base["S"][0] * ({**E.BASE, **LIKELY, **kw.get("P", {})}["cap"])
    lo_p, hi_p = 0.0, 0.20
    best = 0.0
    for _ in range(50):
        mid = (lo_p + hi_p) / 2
        z = run_three_zone(premium=mid, **kw)
        if z["balance"] >= 0 and z["N"] < 0.99 * cap_n:
            best, lo_p = mid, mid
        else:
            hi_p = mid
    z = run_three_zone(premium=best, **kw)
    return {**z, "premium": best, "base_N": base["N"]}


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
    print()
    print("Varyantlar (en olasi senaryo): tampon bedeli ve bos konutun luks bandina kaymasi")
    print(f"{'varyant':<44}{'daire':>7}{'sub':>6}{'gelir':>7}{'oran':>6}{'yuk':>6}{'havuz':>9}{'luks':>9}{'cikan':>9}")
    variants = (
        ("temel: tampon %1, bosluk esit dagilmis", dict()),
        ("tampon bedelsiz", dict(fee_buffer=0.0)),
        ("bosluk luks bandinda %40", dict(lux_vac=0.40)),
        ("bosluk luks bandinda %60", dict(lux_vac=0.60)),
        ("tampon bedelsiz + luks %40", dict(fee_buffer=0.0, lux_vac=0.40)),
        ("tampon bedelsiz + luks %60", dict(fee_buffer=0.0, lux_vac=0.60)),
    )
    for name, kw in variants:
        zz = run_three_zone(**kw)
        freed = zz["freed_buf"] + zz["freed_lux"]
        print(f"{name:<44}{zz['N'] / 1000:>6.0f}b{bn(zz['sub1']):>6.1f}{bn(zz['rev']):>7.1f}{zz['ratio']:>6.2f}{bn(zz['yuk']):>6.0f}{tl(zz['S'][0]):>9}{tl(zz['S'][2]):>9}{tl(freed):>9}")
    print()
    print("Fazla gelir katilim primine gider: butce dengeli en buyuk prim (katilim tavanina ulasinca durur).")
    print(f"{'varyant':<36}{'daire once':>11}{'sonra':>8}{'prim %deger/yil':>17}{'prim mr':>9}{'kalan fazla':>13}{'kapsam':>8}{'20y yuk':>9}")
    for name, kw in (("temel", dict()), ("tampon bedelsiz", dict(fee_buffer=0.0)), ("luks %40", dict(lux_vac=0.40)), ("luks %60", dict(lux_vac=0.60))):
        z = solve_premium(**kw)
        print(f"{name:<36}{z['base_N'] / 1000:>10.0f}b{z['N'] / 1000:>7.0f}b{z['premium']:>17.2%}{bn(z['prem_cost']):>9.1f}{bn(z['balance']):>13.1f}{z['coverage']:>8.1%}{bn(z['yuk']):>9.0f}")
    print()
    print("Prim tavani asinca bosa gider: katilim tavani (kullanima uygun stok payi) bagli. Kalan fazla tavani %25'ten %40'a")
    print("cikaracak tadilat icin kullanilsa, daire basina yillik butce (tadilat maliyeti verisi yok, esik olarak):")
    for name, kw in (("temel", dict()), ("tampon bedelsiz", dict(fee_buffer=0.0)), ("luks %40", dict(lux_vac=0.40)), ("luks %60", dict(lux_vac=0.60))):
        z = solve_premium(**kw)
        extra = z["S"][0] * 0.15
        per = z["balance"] / extra if extra else 0.0
        print(f"  {name:<20}ek daire {extra / 1000:>5.1f} bin, kalan fazla {bn(z['balance']):>5.1f} mr/yil -> daire basina yillik {per:>10,.0f} TL".replace(",", "."))
    print()
    print("Sahibin senede karsilik kabul ettigi kira: havuz kirasi carpani m (piyasa kirasinin payi). Oturan payi ayri (dereceli, %30).")
    print("Baglanti kapali: yalniz sub. ve geri odeme degisir. Baglanti acik: sahibin senet getirisi -lambda x (1-m), katilim duser.")
    print(f"{'m':>5}{'baglanti':>10}{'senet getirisi':>16}{'daire':>8}{'yil-1 sub':>10}{'bedel':>7}{'oran':>6}{'odenen':>8}{'20y yuk':>9}")
    for m in (1.0, 0.9, 0.8, 0.7, 0.6):
        for coup in (False, True):
            if m == 1.0 and coup:
                continue
            zz = run_three_zone(pool_rent_mult=m, senet_coupling=coup)
            print(f"{m:>5.1f}{'acik' if coup else 'kapali':>10}{zz['s_ret']:>16.2%}{zz['N'] / 1000:>7.0f}b{bn(zz['sub1']):>10.1f}{bn(zz['rev']):>7.1f}{zz['ratio']:>6.2f}{zz['paid']:>8.0%}{bn(zz['yuk']):>9.0f}")
    print()
    print("Baglanti acik, beklenen reel artisa gore: m = 1,0 / 0,8 icin yerlesen daire (bin). Doygun bolgede (g_e cok negatif) m etkisiz, g_e yukselince isirir.")
    print(f"{'g_e':>7}{'m=1,0':>9}{'m=0,9':>9}{'m=0,8':>9}{'m=0,7':>9}{'0,8 / 1,0':>11}")
    for g in (-0.065, -0.037, -0.01, 0.0, 0.02, 0.04):
        ns = [run_three_zone(P={"g_e": g}, pool_rent_mult=m)["N"] for m in (1.0, 0.9, 0.8, 0.7)]
        print(f"{g:>7.1%}" + "".join(f"{x / 1000:>8.1f}b" for x in ns) + f"{ns[2] / ns[0] if ns[0] else 0:>11.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
