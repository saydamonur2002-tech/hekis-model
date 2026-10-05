"""Sosyal etki ve yasam maliyeti. "Sosyallesme" burada: bos stokun toplumsal kullanima acilma payi ve faydanin dagilimi.

Kira piyasasi etkisi esneklige (literatur tahmini, dogrulanmadi) ve segment varsayimina bagli: yerlesenler kiraci talebinden
cikar; serbest kalan lux/tampon birimlerin yalniz bir kismi (RENTED) kiraya gider. Kira TUFE agirligi %6,76 (TUIK 2026 sepeti).

    python -m hekis.social
"""

from __future__ import annotations

from hekis import final, politics
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
