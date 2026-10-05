"""Sosyal etki ve yasam maliyeti. "Sosyallesme" burada: bos stokun toplumsal kullanima acilma payi ve faydanin dagilimi.

Kira piyasasi etkisi esneklige (literatur tahmini, dogrulanmadi) ve segment varsayimina bagli: yerlesenler kiraci talebinden
cikar; serbest kalan lux/tampon birimlerin yalniz bir kismi (RENTED) kiraya gider. Kira TUFE agirligi %6,76 (TUIK 2026 sepeti).

    python -m hekis.social
"""

from __future__ import annotations

from hekis import final, horizon, politics
from hekis.bind import load_obs
from hekis.reality import gini_with_benefit
from hekis.zones import run_three_zone

W_KIRA = 0.0676
RENTED = 0.5          # serbest kalan birimlerin kiraya giden payi (varsayim)
ELASTICITY = (0.3, 0.6, 1.0)
TENANTS = politics.HOUSEHOLDS * politics.TENANT_SHARE
STOCK = 4_500_000


def social(z: dict | None = None) -> dict:
    z = z or run_three_zone()
    N, B = z["N"], z["sub1"] / max(z["N"], 1)
    g0, g1, p0, p1 = gini_with_benefit(N, B)
    elig = TENANTS * z["q_h"]
    rows = []
    for lo, hi in ((0.0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, z["q_h"])):
        q = (lo + hi) / 2
        inc = politics.hh_monthly(q) * 12
        rows.append((lo, hi, inc, B / inc))
    return {"N": N, "B": B, "gini": (g0, g1), "poverty": (p0, p1), "rows": rows, "elig": elig,
            "coverage": N / elig, "of_stock": N / STOCK, "of_vacant": N / 450_000, "of_tenants": N / TENANTS}


def cost_of_living(z: dict | None = None, N: float | None = None, freed: float | None = None) -> dict:
    z = z or run_three_zone()
    N = z["N"] if N is None else N
    freed = (z["freed_buf"] + z["freed_lux"]) if freed is None else freed
    demand = N / TENANTS
    both = (N + RENTED * freed) / TENANTS
    out = {"demand": demand, "both": both, "rent": {}, "cpi": {}}
    for e in ELASTICITY:
        out["rent"][e] = (-demand / e, -both / e)
        out["cpi"][e] = (W_KIRA * -demand / e * 100, W_KIRA * -both / e * 100)   # TUFE puani, tek seferlik duzey etkisi
    fee_pool = z["V"][0] * 0.01 * 0.30
    fee_lux = z["V"][2] * 0.05 * final.effective_collection(0.05, 0.40)
    out["fee_pool"], out["fee_lux"] = fee_pool, fee_lux
    out["fiscal_net"] = z["rev"] - z["sub1"]
    out["per_hh_cost"] = z["rev"] / politics.HOUSEHOLDS
    out["per_hh_benefit"] = z["sub1"] / politics.HOUSEHOLDS
    return out


def by_year(paths: list[list[dict]] | None = None, shock: dict | None = None, years: int = horizon.YEARS) -> list[dict]:
    """Yil bazli etki. paths None: kusursuz olcum yolu; verilirse yil basina medyan (yerlesen, sub, bedel, serbest kalan)."""
    if paths is None:
        paths = [horizon.one_path({}, None, shock, years=years)]
    out = []
    for t in range(len(paths[0])):
        med = lambda k: sorted(p[t][k] for p in paths)[len(paths) // 2]
        N, sub, rev, freed = med("N"), med("sub"), med("rev"), med("freed")
        B = sub / max(N, 1)
        g0, g1, p0, p1 = gini_with_benefit(N, B)
        cum = sorted(sum(r['rev'] - r['sub'] for r in p[: t + 1]) for p in paths)[len(paths) // 2]
        c = cost_of_living(N=N, freed=freed, z={"N": N, "freed_buf": 0, "freed_lux": 0, "V": (0, 0, 0), "rev": rev, "sub1": sub})
        out.append({"yil": t + 1, "olcek": med("stok"), "N": N, "kapsam": N / (TENANTS * 0.41), "sub": sub, "rev": rev, "cum": cum,
                    "dgini": g1 - g0, "dpov": (p1 - p0) * 100, "rent": c["rent"][0.6][0] * 100, "cpi": c["cpi"][0.6][0], "cpi_all": c["cpi"][0.6][1]})
    return out


def print_by_year(rows: list[dict], title: str) -> None:
    print(title)
    print(f"{'yil':>4}{'olcek':>9}{'yerlesen':>10}{'kapsam':>8}{'sub mr':>8}{'bedel mr':>9}{'kum net':>8}{'dGini':>9}{'dYoks.':>8}{'kira%':>7}{'TUFE':>7}{'TUFE(+arz)':>11}")
    for r in rows:
        print(f"{r['yil']:>4}{r['olcek']:>9,.0f}{r['N']:>10,.0f}{r['kapsam']:>8.2%}{r['sub'] / 1e9:>8.2f}{r['rev'] / 1e9:>9.2f}{r['cum'] / 1e9:>8.2f}{r['dgini']:>9.5f}{r['dpov']:>8.3f}{r['rent']:>7.2f}{r['cpi']:>7.3f}{r['cpi_all']:>11.3f}".replace(",", "."))


def main() -> int:
    z = run_three_zone()
    s = social(z)
    tl = lambda v: f"{v:,.0f}".replace(",", ".")
    print("SOSYAL ETKI (en olasi, tam olcek: 37 bin hane)")
    print(f"  Yerlesen {tl(s['N'])} hane; her biri yilda {tl(s['B'])} TL ({tl(s['B'] / 12)} TL/ay) fayda")
    print(f"  Kapsam: uygun kiraciya {s['coverage']:.1%}, tum kiraciya {s['of_tenants']:.1%}, bos stoka {s['of_vacant']:.1%}, toplam stoka {s['of_stock']:.2%}")
    print(f"  Gini {s['gini'][0]:.4f} -> {s['gini'][1]:.4f} ({s['gini'][1] - s['gini'][0]:+.4f}); goreli yoksulluk {s['poverty'][0]:.2%} -> {s['poverty'][1]:.2%}")
    print("  Fayda / gelir (yerlesen hane, gelir dilimine gore):")
    for lo, hi, inc, r in s["rows"]:
        print(f"    alt %{lo * 100:.0f}-{hi * 100:.0f}: yillik gelir {tl(inc)} TL, fayda gelirin {r:.0%}'i")
    print("  Kura rastlantisal: ayni dilimde yerlesen/yerlesmeyen hane arasinda adalet sorunu (yalniz %6,6 kapsam). Mekansal yogunlasma (Esenyurt tipi stokta) ilce verisi olmadigindan olculmedi.")
    c = cost_of_living(z)
    print("\nYASAM MALIYETI")
    print(f"  Kiraci hane {tl(TENANTS)}. Yerlesenler talebi {c['demand']:.1%} azaltir; serbest kalan birimlerin {RENTED:.0%}'i kiraya gitse arz payi toplam {c['both']:.1%}.")
    print("  Piyasa kirasi (tek seferlik duzey etkisi) ve TUFE puani, esneklik (literatur tahmini):")
    print(f"  {'esneklik':>9}{'sadece talep':>14}{'talep+arz':>11}{'TUFE puan (talep)':>20}{'(talep+arz)':>13}")
    for e in ELASTICITY:
        r, cp = c["rent"][e], c["cpi"][e]
        print(f"  {e:>9.1f}{r[0]:>14.1%}{r[1]:>11.1%}{cp[0]:>20.2f}{cp[1]:>13.2f}")
    print("  Not: serbest kalan birimler lux/tampon segmentinde; dusuk gelirli kiraci piyasasina etkisi dolayli. 'Talep+arz' ust sinir.")
    print(f"  5. yil (12 bin hane, 5 yillik yol): talep etkisi {-11_500 / TENANTS / 0.6:.1%} (esneklik 0,6), TUFE {W_KIRA * -11_500 / TENANTS / 0.6 * 100:.2f} puan")
    print(f"  Maliyeti kim oder: havuz sinifi bos birim sahibi yilda ~{tl(c['fee_pool'])} TL, luks bos birim sahibi ~{tl(c['fee_lux'])} TL (etkin tahsilatla beklenen)")
    print(f"  Hane basina ortalama (Istanbul, {politics.HOUSEHOLDS / 1e6:.1f} mn hane): bedel {tl(c['per_hh_cost'])} TL/yil (yalniz bos birim sahibi oder, dagilim esit degil), sub. {tl(c['per_hh_benefit'])} TL/yil; net kamu fazlasi {c['fiscal_net'] / 1e9:.1f} mr TL (vergi/para basimi yok)")
    print()
    print_by_year(by_year(), "YIL BAZLI ETKI (kusursuz olcum, erozyon %25, buyume x2,5; kira esnekligi 0,6; TUFE puan = kira agirligi %6,76)")
    print()
    mc = horizon.monte_carlo(200)
    print_by_year(by_year(mc), "YIL BAZLI ETKI (belirsiz degerler + olcum hatasi, 200 cekim medyan)")
    print()
    print_by_year(by_year(years=10), "10 YILLIK UFUK (kusursuz olcum)")
    mc10 = horizon.monte_carlo(200, years=10)
    print()
    print_by_year(by_year(mc10), "10 YILLIK UFUK (belirsiz degerler + olcum hatasi, 200 cekim medyan)")
    print("(TUFE puani tek seferlik duzey etkisi, yillik enflasyona eklenmez; birikimli degil.) dGini/dYoks. puan; TUFE(+arz) ust sinir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
