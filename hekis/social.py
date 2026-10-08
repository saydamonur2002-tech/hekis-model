"""Sosyal etki ve yasam maliyeti, iki ayri HEKIS sistemi (Istanbul, Anadolu) icin. "Sosyallesme": bos stokun toplumsal
kullanima acilma payi ve faydanin dagilimi.

Kira piyasasi etkisi esneklige (literatur tahmini, dogrulanmadi) ve segment varsayimina bagli: yerlesenler kiraci talebinden
cikar; serbest kalan lux/tampon birimlerin yalniz bir kismi (RENTED) kiraya gider. Kira TUFE agirligi %6,76 (TUIK 2026 sepeti).
Yerel TUFE puani: sistemin kendi sehirlerinde; ulusal puan: ayni etki hane payi kadar (ulusal hane sayisi yaklasik).

    python -m hekis.social
"""

from __future__ import annotations

from hekis import horizon, politics
from hekis.reality import gini_with_benefit
from hekis.systems import ANADOLU, ISTANBUL, System

W_KIRA = 0.0676
RENTED = 0.5          # serbest kalan birimlerin kiraya giden payi (varsayim)
ELASTICITY = (0.3, 0.6, 1.0)


def social(z: dict, system: System = ISTANBUL) -> dict:
    N, B = z["N"], z["sub1"] / max(z["N"], 1)
    g0, g1, p0, p1 = gini_with_benefit(N, B, households=system.households)
    s = system.extra.get("s", 1.0)
    q_h = system.eligible / system.tenants
    rows = []
    for lo, hi in ((0.0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, q_h)):
        inc = politics.hh_monthly((lo + hi) / 2, scale=s) * 12
        rows.append((lo, hi, inc, B / inc))
    return {"N": N, "B": B, "gini": (g0, g1), "poverty": (p0, p1), "rows": rows,
            "coverage": N / system.eligible, "of_tenants": N / system.tenants, "of_vacant": N / system.full}


def cost_of_living(N: float, freed: float, system: System = ISTANBUL) -> dict:
    demand = N / system.tenants
    both = (N + RENTED * freed) / system.tenants
    out = {"demand": demand, "both": both, "rent": {}, "cpi": {}, "cpi_nat": {}}
    for e in ELASTICITY:
        out["rent"][e] = (-demand / e, -both / e)
        out["cpi"][e] = (W_KIRA * -demand / e * 100, W_KIRA * -both / e * 100)   # yerel TUFE puani, tek seferlik duzey etkisi
        out["cpi_nat"][e] = tuple(x * system.national_share for x in out["cpi"][e])
    return out


def by_year(paths: list[list[dict]] | None = None, shock: dict | None = None, years: int = horizon.YEARS,
            system: System = ISTANBUL) -> list[dict]:
    """Yil bazli etki. paths None: kusursuz olcum yolu; verilirse yil basina medyan."""
    if paths is None:
        paths = [horizon.one_path({}, None, shock, years=years, system=system)]
    out = []
    for t in range(len(paths[0])):
        med = lambda k: sorted(p[t][k] for p in paths)[len(paths) // 2]
        N, sub, rev, freed = med("N"), med("sub"), med("rev"), med("freed")
        g0, g1, p0, p1 = gini_with_benefit(N, sub / max(N, 1), households=system.households)
        cum = sorted(sum(r["rev"] - r["sub"] for r in p[: t + 1]) for p in paths)[len(paths) // 2]
        c = cost_of_living(N, freed, system)
        out.append({"yil": t + 1, "olcek": med("stok"), "N": N, "kapsam": N / system.eligible, "sub": sub, "rev": rev, "cum": cum,
                    "dgini": g1 - g0, "dpov": (p1 - p0) * 100, "rent": c["rent"][0.6][0] * 100, "cpi": c["cpi"][0.6][0],
                    "cpi_all": c["cpi"][0.6][1], "cpi_nat": c["cpi_nat"][0.6][0]})
    return out


def print_by_year(rows: list[dict], title: str) -> None:
    print(title)
    print(f"{'yil':>4}{'olcek':>9}{'yerlesen':>10}{'kapsam':>8}{'sub mr':>8}{'bedel mr':>9}{'kum net':>8}{'dGini':>9}{'dYoks.':>8}{'kira%':>7}{'TUFE yerel':>11}{'(+arz)':>8}{'TUFE ulusal':>12}")
    for r in rows:
        print(f"{r['yil']:>4}{r['olcek']:>9,.0f}{r['N']:>10,.0f}{r['kapsam']:>8.2%}{r['sub'] / 1e9:>8.2f}{r['rev'] / 1e9:>9.2f}{r['cum'] / 1e9:>8.2f}{r['dgini']:>9.5f}{r['dpov']:>8.3f}{r['rent']:>7.2f}{r['cpi']:>11.3f}{r['cpi_all']:>8.3f}{r['cpi_nat']:>12.4f}".replace(",", "."))


def main() -> int:
    tl = lambda v: f"{v:,.0f}".replace(",", ".")
    for sys_ in (ISTANBUL, ANADOLU):
        z = sys_.runner({**sys_.base}, sys_.full)
        s = social(z, sys_)
        print(f"== {sys_.name}: tam olcek (erozyonsuz, tarife genel {sys_.base['fee']:.2%} / luks {sys_.base['lux_fee']:.0%})")
        print(f"  Yerlesen {tl(s['N'])} hane; hane basina yilda {tl(s['B'])} TL (ayda {tl(s['B'] / 12)}). Kapsam: uygun kiraciya {s['coverage']:.1%}, tum kiraciya {s['of_tenants']:.1%}, bos stoka {s['of_vacant']:.1%}")
        print(f"  Gini {s['gini'][0]:.4f} -> {s['gini'][1]:.4f} ({s['gini'][1] - s['gini'][0]:+.4f}); goreli yoksulluk {s['poverty'][0]:.2%} -> {s['poverty'][1]:.2%}")
        print("  Fayda / gelir (yerlesen hane): " + "; ".join(f"alt %{lo * 100:.0f}-{hi * 100:.0f}: {r:.0%}" for lo, hi, inc, r in s["rows"]))
        c = cost_of_living(z["N"], z["freed_buf"] + z["freed_lux"], sys_)
        print(f"  Yasam maliyeti (esneklik 0,3 / 0,6 / 1,0): kira (yalniz talep) " + " / ".join(f"{c['rent'][e][0]:.1%}" for e in ELASTICITY) +
              "; yerel TUFE puani " + " / ".join(f"{c['cpi'][e][0]:.2f}" for e in ELASTICITY) + f"; ulusal TUFE puani (hane payi {sys_.national_share:.0%}) " + " / ".join(f"{c['cpi_nat'][e][0]:.3f}" for e in ELASTICITY))
        print()
    for years, title in ((5, "5 YIL"), (10, "10 YIL")):
        for sys_ in (ISTANBUL, ANADOLU):
            print_by_year(by_year(years=years, system=sys_), f"{sys_.name}: YIL BAZLI ({title}, kusursuz olcum, erozyon %25, buyume x2,5, esneklik 0,6)")
            print()
    ist, ana = by_year(years=10, system=ISTANBUL), by_year(years=10, system=ANADOLU)
    print("IKI SISTEM TOPLAMI (10 yil, kusursuz olcum)")
    print(f"{'yil':>4}{'yerlesen':>10}{'sub mr':>8}{'bedel mr':>9}{'kum net':>9}{'ulusal TUFE':>12}")
    for a, b in zip(ist, ana):
        print(f"{a['yil']:>4}{a['N'] + b['N']:>10,.0f}{(a['sub'] + b['sub']) / 1e9:>8.2f}{(a['rev'] + b['rev']) / 1e9:>9.2f}{(a['cum'] + b['cum']) / 1e9:>9.2f}{a['cpi_nat'] + b['cpi_nat']:>12.4f}".replace(",", "."))
    print("(Ulusal TUFE puani: hane payina gore, Istanbul kirasi daha yuksek oldugundan gercek pay biraz buyuk; toplanmis degerler tek seferlik duzey etkisi.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
