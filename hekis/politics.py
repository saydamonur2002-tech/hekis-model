"""Dereceli kira, dereceli bos tutma bedeli ve kimin ne odedigi hesabi.

Gelir dagilimi: medyan ve ortalamaya uydurulmus lognormal. Sinavi: ust ve alt %20 payi.
Kim ne oder, kisi basi tutarlar. Siyasi degerlendirme yok.

    python -m hekis.politics
"""

from __future__ import annotations

import math
from statistics import NormalDist

from hekis import activation
from hekis.bind import load_obs

MEDIAN = 241_151.0
MEAN = 332_882.0
EQ_FACTOR = 2.0          # varsayim
UPLIFT = 28_075.5 / 17_002.0   # asgari ucret artisi 2024->2026, 2024 degeri hafizadan
HOUSEHOLDS = 28_000_000  # varsayim
TENANT_SHARE = 0.27
COLLECTION = 0.60        # VARSAYIM. Irlanda'dan turetilmedi: orada 50 bin isaretli konuttan yaklasik 3 bini vergiye tabi (~%6), %59 baska bir oran
ND = NormalDist()
SIGMA = math.sqrt(2 * math.log(MEAN / MEDIAN))
MU = math.log(MEDIAN)


def hh_monthly(q: float, uplift: float | None = None, eq: float | None = None) -> float:
    """q. yuzdelik dilimdeki hanenin 2026 aylik geliri."""
    return math.exp(MU + SIGMA * ND.inv_cdf(q)) * (EQ_FACTOR if eq is None else eq) / 12 * (UPLIFT if uplift is None else uplift)


def share_check() -> tuple[float, float]:
    top = 1 - ND.cdf(ND.inv_cdf(0.8) - SIGMA)
    bottom = ND.cdf(ND.inv_cdf(0.2) - SIGMA)
    return top, bottom


def graduated(rent: float, alpha: float, qcut: float, steps: int = 400,
              uplift: float | None = None, eq: float | None = None) -> tuple[float, float]:
    """Uygun hane [0, qcut] araligindan kura ile secilir. Oturan min(kira, alpha x gelir) oder.
    Ortalama aylik odeme ve ortalama aylik subvansiyon."""
    pay_sum = 0.0
    for i in range(steps):
        q = qcut * (i + 0.5) / steps
        pay_sum += min(rent, alpha * hh_monthly(q, uplift, eq))
    pay = pay_sum / steps
    return pay, rent - pay


def blend_units(obs: dict, n: float):
    units = activation.tier_units(obs, "orta", n * 0.5) + activation.tier_units(obs, "ucuz", n * 0.5)
    count = sum(u.count for u in units)
    rent = sum(u.rent * u.count for u in units) / count
    flat = sum((u.rent - u.tenant_pay) * u.count for u in units) / count
    value = sum(u.price * u.count for u in units) / count
    return rent, flat, value


def fee_economics(obs: dict, fee: float, sub: float, value: float, collection: float) -> tuple[float, float, float]:
    """Katilim, yillik subvansiyon, yillik bedel geliri (TL)."""
    g = activation.expected_real_growth(obs)
    c = activation.hold_cost_ratio(obs)
    stok = obs["bos_stok"]["ibb_elektrik_su_tabanli"]
    p = activation.participation(g, c, fee, 25.0, 0.40)
    return p, stok * p * sub * 12, stok * (1 - p) * value * fee * collection


def break_even_fee(obs: dict, sub: float, value: float, collection: float) -> float | None:
    lo, hi = 0.0, 0.30
    f = lambda fee: (lambda r: r[2] - r[1])(fee_economics(obs, fee, sub, value, collection))
    if f(hi) < 0:
        return None
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
    return hi


def sensitivity(obs: dict) -> None:
    """a=%30, kesim %40. Tahsilat x gelir artisi x esdeger-hane katsayisi."""
    rent, _, value = blend_units(obs, 161_000)
    print("Bedel geliri subvansiyonu karsilayan en dusuk bedel (basabas), alt %40, a=%30")
    print(f"{'tahsilat':>9}{'gelir artisi':>14}{'esdeger k.':>12}{'ort. sub. TL/ay':>17}{'sub. mr/yil':>13}{'basabas bedel':>15}{'gelir/sub. @%3':>16}")
    for coll in (0.3, 0.6, 0.9):
        for uplift in (1.3, UPLIFT, 2.0):
            for eq in (1.8, 2.0, 2.2):
                if (uplift != UPLIFT and eq != 2.0):
                    continue
                _, sub = graduated(rent, 0.30, 0.4, uplift=uplift, eq=eq)
                be = break_even_fee(obs, sub, value, coll)
                p, s_year, rev = fee_economics(obs, 0.03, sub, value, coll)
                be_txt = "yok (>%30)" if be is None else f"%{be:.1%}"
                print(f"{coll:>9.0%}{uplift:>14.2f}{eq:>12.1f}{sub:>17,.0f}{s_year / 1e9:>13.1f}{be_txt:>15}{rev / s_year:>16.2f}".replace(",", "."))


def main() -> int:
    obs = load_obs()
    tl = lambda v: f"{v:,.0f}".replace(",", ".")
    top, bottom = share_check()
    print(f"Dagilim sinavi: ust %20 payi model %{top:.1%} (TUIK %48), alt %20 model %{bottom:.1%} (TUIK %6,4). Lognormal sigma {SIGMA:.3f}")
    print(f"2026 hane aylik geliri: alt %10 {tl(hh_monthly(0.1))}, alt %20 {tl(hh_monthly(0.2))}, medyan {tl(hh_monthly(0.5))}, ust %20 siniri {tl(hh_monthly(0.8))} TL")
    print()
    n = 161_000
    rent, flat, value = blend_units(obs, n)
    print(f"Ortalama daire: kira {tl(rent)} TL/ay, deger {tl(value)} TL. Mevcut sosyal kira modelinde aylik subvansiyon {tl(flat)} TL")
    tenants = HOUSEHOLDS * TENANT_SHARE
    print()
    print("Dereceli kira: oturan min(kira, a x gelir) oder. Uygun kitle gelir dilimi [0, kesim], kura ile. 161 bin daire.")
    print(f"{'a':>5}{'kesim':>8}{'ort. odeme':>12}{'ort. sub.':>11}{'yillik sub. mr':>16}{'kapsam (uygun kiraciya)':>26}")
    for alpha in (0.20, 0.30, 0.40):
        for qcut in (0.2, 0.4, 0.6):
            pay, sub = graduated(rent, alpha, qcut)
            print(f"{alpha:>5.0%}{qcut:>8.0%}{tl(pay):>12}{tl(sub):>11}{n * sub * 12 / 1e9:>16.1f}{n / (tenants * qcut):>26.1%}")
    print(f"Duz sosyal kira referansi: yillik {n * flat * 12 / 1e9:.1f} mr TL")
    print()
    print("Bos tutma bedeli geliri, subvansiyonu karsilar mi? (450 bin bos stok, mevcut karma kural, a=%30, kesim %40, tahsilat %60)")
    g = activation.expected_real_growth(obs)
    c = activation.hold_cost_ratio(obs)
    stok = obs["bos_stok"]["ibb_elektrik_su_tabanli"]
    _, sub = graduated(rent, 0.30, 0.4)
    print(f"{'bedel':>7}{'katilim':>9}{'giren':>10}{'sub. mr/yil':>13}{'bedel geliri mr/yil':>21}{'gelir/sub.':>12}{'vergi mukellefi basi TL/yil':>29}")
    for fee in (0.005, 0.01, 0.02, 0.03):
        p = activation.participation(g, c, fee, 25.0, 0.40)
        k = stok * p
        subsidy = k * sub * 12
        revenue = stok * (1 - p) * value * fee * COLLECTION
        gap = max(0.0, subsidy - revenue)
        print(f"{fee:>7.1%}{p:>9.1%}{tl(k):>10}{subsidy / 1e9:>13.1f}{revenue / 1e9:>21.1f}{revenue / subsidy:>12.1f}{gap / HOUSEHOLDS:>29,.0f}".replace(",", "."))
    print()
    print("Kim ne oder (bedel %1, a=%30, kesim %40)")
    p = activation.participation(g, c, 0.01, 25.0, 0.40)
    k = stok * p
    own_stay = stok * (1 - p)
    fee_per_owner = value * 0.01
    print(f"  Daireye yerlesen hane: {tl(k)}, her biri ayda ortalama {tl(sub)} TL kazanir")
    print(f"  Uygun ama yerlesemeyen kiraci hane: {tl(tenants * 0.4 - k)} ({(tenants * 0.4 - k) / (tenants * 0.4):.0%}). Kuraya dayali, esitsiz.")
    print(f"  Bos tutmaya devam eden sahip: {tl(own_stay)}, her biri yilda {tl(fee_per_owner)} TL bedel (beyan/tahsilat %60: ~{tl(fee_per_owner * COLLECTION)})")
    print(f"  Genel hane: bedel geliri subvansiyonu karsilarsa ek yuk 0, karsilamazsa kisi basi yukarida")
    print()
    sensitivity(obs)
    print()
    utility_subsidy_report()
    return 0



def monthly_utilities(obs: dict) -> float:
    """Daire basina aylik abonelik gideri, bugunku TL. Dogalgaz ve su kalemi eksik veya eski, alt sinir."""
    a = obs["abonelik"]
    return (a["elektrik_kwh_ay"] * a["elektrik_tl_kwh"] + a["dogalgaz_m3_yil"] * a["dogalgaz_tl_m3"] / 12
            + a["su_m3_ay"] * a["su_tl_m3"])


def utility_subsidy_report() -> None:
    from dataclasses import replace

    from hekis.bind import inflation_paths
    from hekis.model import simulate

    obs = load_obs()
    util = monthly_utilities(obs)
    n = 161_000
    rent, _, _ = blend_units(obs, n)
    pay, _ = graduated(rent, 0.30, 0.4)
    share = pay / rent
    units = []
    for tier in ("orta", "ucuz"):
        units += [replace(u, tenant_pay=u.rent * share) for u in activation.tier_units(obs, tier, n * 0.5)]
    print(f"Abonelik: elektrik {obs['abonelik']['elektrik_kwh_ay'] * obs['abonelik']['elektrik_tl_kwh']:,.0f} + dogalgaz {obs['abonelik']['dogalgaz_m3_yil'] * obs['abonelik']['dogalgaz_tl_m3'] / 12:,.0f} + su {obs['abonelik']['su_m3_ay'] * obs['abonelik']['su_tl_m3']:,.0f} = {util:,.0f} TL/ay".replace(",", "."))
    print(f"{'':<34}{'yil-1 sub. mr':>14}{'20y yuk mr':>12}{'20y odenen':>12}")
    for label, u in (("sadece dereceli kira", 0.0), ("+ abonelik sübvansiyonu", util)):
        p = replace(activation.params(obs), utility_sub=u)
        r = simulate(units, inflation_paths(obs)["ovp"], [1.0] * 20, p)
        first = r.rows[0].subsidy / (1 + r.rows[0].inflation)
        print(f"{label:<34}{first / 1e9:>14.1f}{r.total_fiscal_real / 1e9:>12.0f}{r.real_eroded:>12.0%}")
    print("Oturanin gelire oranla konut gideri (kira a=%30 + abonelik):")
    for q in (0.1, 0.2, 0.3, 0.4):
        inc = hh_monthly(q)
        rpay = min(rent * share, 0.30 * inc)
        print(f"  q{int(q * 100)}: abonelik sub. yokken %{(rpay + util) / inc:.0%}, sub. varken %{rpay / inc:.0%}")

if __name__ == "__main__":
    raise SystemExit(main())
