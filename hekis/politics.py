"""Dereceli kira, dereceli bos tutma bedeli ve kimin ne odedigi hesabi.

Gelir dagilimi: medyan ve ortalamaya uydurulmus lognormal. Sinavi: ust ve alt %20 payi.
Siyasi agirlik uretilmez. Kazanan ve kaybeden sayilari ve kisi basi tutarlar verilir.

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
COLLECTION = 0.60        # Irlanda: beyan edilenin yaklasik %59'u vergiye tabi. Varsayim
ND = NormalDist()
SIGMA = math.sqrt(2 * math.log(MEAN / MEDIAN))
MU = math.log(MEDIAN)


def hh_monthly(q: float) -> float:
    """q. yuzdelik dilimdeki hanenin 2026 aylik geliri."""
    return math.exp(MU + SIGMA * ND.inv_cdf(q)) * EQ_FACTOR / 12 * UPLIFT


def share_check() -> tuple[float, float]:
    top = 1 - ND.cdf(ND.inv_cdf(0.8) - SIGMA)
    bottom = ND.cdf(ND.inv_cdf(0.2) - SIGMA)
    return top, bottom


def graduated(rent: float, alpha: float, qcut: float, steps: int = 400) -> tuple[float, float]:
    """Uygun hane [0, qcut] araligindan kura ile secilir. Oturan min(kira, alpha x gelir) oder.
    Ortalama aylik odeme ve ortalama aylik subvansiyon."""
    pay_sum = 0.0
    for i in range(steps):
        q = qcut * (i + 0.5) / steps
        pay_sum += min(rent, alpha * hh_monthly(q))
    pay = pay_sum / steps
    return pay, rent - pay


def blend_units(obs: dict, n: float):
    units = activation.tier_units(obs, "orta", n * 0.5) + activation.tier_units(obs, "ucuz", n * 0.5)
    count = sum(u.count for u in units)
    rent = sum(u.rent * u.count for u in units) / count
    flat = sum((u.rent - u.tenant_pay) * u.count for u in units) / count
    value = sum(u.price * u.count for u in units) / count
    return rent, flat, value


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
    print("Kim kazanir, kim kaybeder (bedel %1, a=%30, kesim %40)")
    p = activation.participation(g, c, 0.01, 25.0, 0.40)
    k = stok * p
    own_stay = stok * (1 - p)
    fee_per_owner = value * 0.01
    print(f"  Daireye yerlesen hane: {tl(k)}, her biri ayda ortalama {tl(sub)} TL kazanir")
    print(f"  Uygun ama yerlesemeyen kiraci hane: {tl(tenants * 0.4 - k)} ({(tenants * 0.4 - k) / (tenants * 0.4):.0%}). Kuraya dayali, esitsiz.")
    print(f"  Bos tutmaya devam eden sahip: {tl(own_stay)}, her biri yilda {tl(fee_per_owner)} TL bedel (beyan/tahsilat %60: ~{tl(fee_per_owner * COLLECTION)})")
    print(f"  Genel hane: bedel geliri subvansiyonu karsilarsa ek yuk 0, karsilamazsa kisi basi yukarida")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
