"""Duran (natamam) insaat: tamamlanip HEKIS havuzuna entegre edilmesi. Kentsel donusum ve tadilat disindadir.

Mekanizma (model varsayimi): havuz tamamlama bedelini oder, daire tamamlanip kiralanir, net kira tamamlama bedelini geri
oder, sonra mulkiyet alici-sahipte kalir. Sahip daireyi kullanamaz, kira hakki havuzdadir. Boylece havuzun sermayesi
dairenin degeri degil, yalniz tamamlama bedelidir.

    python -m hekis.stalled
"""

from __future__ import annotations

from hekis import activation, politics, zones
from hekis.bind import load_obs
from hekis.model import holding_cost, pool_and_subsidy

N_STALLED = 100_000        # sektor iddiasi, resmi sayi degil
AREA = 100.0               # m2, varsayim (Endeksa Istanbul ortalama ~110)
COST_LOW, COST_MID, COST_HIGH = 19_800.0, 26_000.0, 33_900.0   # TL/m2, KDV haric, 2026 yapi yaklasik birim maliyeti


def unit_economics(obs: dict):
    """Esenyurt tipi (havuz bandi) ortalama daire: yillik net kira, subvansiyon (kira farki + abonelik), deger."""
    units = activation.tier_units(obs, "ucuz", 1000)
    n = sum(u.count for u in units)
    p = activation.params(obs)
    pool, _ = pool_and_subsidy(units, p)
    hold = holding_cost(units, p)
    net = (pool - hold) / n
    rent = sum(u.rent * u.count for u in units) / n
    value = sum(u.price * u.count for u in units) / n
    q_h = zones.union.quantile_of_income(zones.union.MEMUR_FLAT)
    pay, gap = politics.graduated(rent, 0.30, q_h)
    sub_year = (gap + politics.monthly_utilities(obs)) * 12 * (1 - p.vacancy)
    return {"net": net, "rent": rent, "value": value, "sub": sub_year, "q_h": q_h}


def main() -> int:
    obs = load_obs()
    tl = lambda v: f"{v:,.0f}".replace(",", ".")
    ue = unit_economics(obs)
    print("Duran insaat, HEKIS'e entegre (kentsel donusum ve tadilat disinda).")
    print(f"Esenyurt tipi daire: deger {tl(ue['value'])} TL, piyasa kirasi {tl(ue['rent'])} TL/ay, havuzun yillik net kirasi {tl(ue['net'])} TL,")
    print(f"yillik subvansiyon (kira farki + abonelik) {tl(ue['sub'])} TL.")
    print()
    print("Daire basina tamamlama bedeli (TL) = kalan pay x birim maliyet x 100 m2. Geri odeme suresi = bedel / yillik net kira.")
    print(f"{'kalan pay':>10}" + "".join(f"{f'{int(k):,} TL/m2'.replace(',', '.'):>30}" for k in (COST_LOW, COST_MID, COST_HIGH)))
    print(f"{'':>10}" + "".join(f"{'bedel, geri odeme, deger payi':>30}" for _ in range(3)))
    for r in (0.10, 0.20, 0.30):
        cells = []
        for k in (COST_LOW, COST_MID, COST_HIGH):
            c = r * k * AREA
            cells.append(f"{tl(c)}, {c / ue['net']:.1f} yil, {c / ue['value']:.0%}")
        print(f"{r:>10.0%}" + "".join(f"{x:>30}" for x in cells))
    print()
    r, k = 0.20, COST_MID
    c = r * k * AREA
    print(f"Orta durum: kalan %20, 26.000 TL/m2 -> {tl(c)} TL/daire, geri odeme {c / ue['net']:.1f} yil, degerin {c / ue['value']:.0%}'i.")
    print()
    print("Olcek (orta durum). Girenin payi: hukuki engeller ve uygun olmayanlar dusulur (varsayim). Havuz bandi: HEKIS gelir kesimine uygun daire payi.")
    print(f"{'giren':>7}{'bant':>6}{'daire':>9}{'sermaye mr':>12}{'yillik sub mr':>15}{'20 yil sub mr':>15}   mevcut bos stok sonucuna (37 bin daire) gore")
    for feasible in (0.25, 0.50, 1.00):
        for band in (zones.union.quantile_of_income(zones.union.MEMUR_FLAT), 1.0):
            n = N_STALLED * feasible * band
            cap = n * c
            sub = n * ue["sub"]
            print(f"{feasible:>7.0%}{band:>6.2f}{tl(n):>9}{cap / 1e9:>12.1f}{sub / 1e9:>15.1f}{sub * 20 / 1e9:>15.0f}   {n / 37_000:.1f} kat")
    print()
    print("Daire basina havuz sermayesi: mevcut bos stok (anapara = deger) " + f"{tl(ue['value'])} TL, duran insaat (anapara = tamamlama) {tl(c)} TL: {ue['value'] / c:.1f} kat daha az.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
