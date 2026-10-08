"""Duyarlilik ve kuresel testler.

  1) Tornado: her parametre tek tek alt/ust uca, gelir/sub. orani ve yerlesen daire.
  2) Monte Carlo: tum parametreler ayni anda, ucgen dagilim, dagilim ve kendini finanse oranı.
  3) Rank korelasyonu: hangi parametre sonucu en cok belirliyor (kuresel duyarlilik).
  4) Ters stres: kendini finanse eden cekilislerde parametreler nerede.

    python -m hekis.analysis
"""

from __future__ import annotations

import statistics

from hekis import evaluate as E


def pct(xs: list[float], q: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))]


def main() -> int:
    base = E.evaluate()
    bn = lambda v: v / 1e9
    print("Baz: yerlesen {:,.0f} daire, yil-1 sub. {:.1f} mr, bedel geliri {:.1f} mr (oran {:.2f}), 20y yuk {:.0f} mr, geri odenen {:.0%}".format(
        base["N"], bn(base["sub1"]), bn(base["rev"]), base["ratio"], bn(base["yuk"]), base["odenen"]).replace(",", "."))
    alt = E.evaluate({"rent_prop": False})
    print("Yapisal secim: orta tip kirasi degerle orantili (baz) / sabit politika kirasi")
    print("  oran {:.2f} / {:.2f}, yil-1 sub. {:.1f} / {:.1f} mr, 20y yuk {:.0f} / {:.0f} mr, geri odenen {:.0%} / {:.0%}".format(
        base["ratio"], alt["ratio"], bn(base["sub1"]), bn(alt["sub1"]), bn(base["yuk"]), bn(alt["yuk"]), base["odenen"], alt["odenen"]))
    print()
    print("1) Tornado (her parametre tek basina alt / ust uc). Gelir/sub. orani ve yerlesen daire (bin).")
    print(f"{'parametre':<13}{'alt':>10}{'ust':>10}   {'oran alt':>9}{'oran ust':>9}{'oynama':>8}   {'daire alt':>10}{'daire ust':>10}")
    for k, a, b in E.tornado():
        lo, _, hi = E.SPACE[k]
        fmt = lambda v: f"{v:,.3g}" if abs(v) < 1e5 else f"{v / 1000:,.0f}b"
        print(f"{k:<13}{fmt(lo):>10}{fmt(hi):>10}   {a['ratio']:>9.2f}{b['ratio']:>9.2f}{abs(b['ratio'] - a['ratio']):>8.2f}   {a['N'] / 1000:>10.0f}{b['N'] / 1000:>10.0f}")
    print()
    inputs, outs = E.monte_carlo(1500)
    ratio = [o["ratio"] for o in outs]
    n = [o["N"] for o in outs]
    yuk = [bn(o["yuk"]) for o in outs]
    deficit = [bn(o["deficit"]) for o in outs]
    print("2) Monte Carlo, 1500 cekilis (ucgen dagilim, tohum 42). Yuzdelikler %5 / %50 / %95")
    print(f"  yerlesen daire (bin):   {pct(n, .05) / 1000:>7.0f} / {pct(n, .5) / 1000:>7.0f} / {pct(n, .95) / 1000:>7.0f}")
    print(f"  20 yil yuk (mr TL):     {pct(yuk, .05):>7.0f} / {pct(yuk, .5):>7.0f} / {pct(yuk, .95):>7.0f}")
    print(f"  yillik acik (mr TL):    {pct(deficit, .05):>7.1f} / {pct(deficit, .5):>7.1f} / {pct(deficit, .95):>7.1f}")
    print(f"  gelir / sub. orani:     {pct(ratio, .05):>7.2f} / {pct(ratio, .5):>7.2f} / {pct(ratio, .95):>7.2f}")
    print(f"  kendini finanse eden (oran >= 1): %{sum(r >= 1 for r in ratio) / len(ratio):.1%}")
    print(f"  oran >= 0,5: %{sum(r >= 0.5 for r in ratio) / len(ratio):.1%}")
    print()
    print("3) Rank korelasyonu (Spearman). Sonucu en cok kimin belirledigi.")
    print(f"{'parametre':<13}{'oran':>8}{'daire':>8}{'yuk':>8}")
    rows = []
    for k in E.SPACE:
        xs = [P[k] for P in inputs]
        rows.append((k, E.spearman(xs, ratio), E.spearman(xs, n), E.spearman(xs, [o['yuk'] for o in outs])))
    rows.sort(key=lambda t: -abs(t[1]))
    for k, a, b, c in rows:
        print(f"{k:<13}{a:>8.2f}{b:>8.2f}{c:>8.2f}")
    print()
    print("Olcek ve finansman: kendini finanse eden (oran >= 1) cekilislerin payi, yerlesen daire dilimine gore")
    print("Kucuk olcekte oran yapay sisebilir: alici az, bedel tabani genis.")
    print(f"  Spearman(daire, oran) = {E.spearman(n, ratio):.2f}")
    print(f"{'yerlesen daire':<18}{'cekilis':>9}{'oran>=1':>10}{'medyan oran':>13}")
    for lo, hi in ((0, 25_000), (25_000, 75_000), (75_000, 150_000), (150_000, 10 ** 9)):
        sel = [r for r, x in zip(ratio, n) if lo <= x < hi]
        if sel:
            label = f"{lo // 1000}-{hi // 1000} bin" if hi < 10 ** 9 else f">{lo // 1000} bin"
            print(f"{label:<18}{len(sel):>9}{sum(r >= 1 for r in sel) / len(sel):>10.0%}{statistics.median(sel):>13.2f}")
    print()
    good = [(P, o) for P, o in zip(inputs, outs) if o["ratio"] >= 1.0]
    print(f"4) Ters stres: kendini finanse eden {len(good)} cekilis. Parametre ortalamasi, tum cekilislere gore:")
    if good:
        print(f"{'parametre':<13}{'finanse eden':>14}{'tum cekilis':>13}")
        for k in E.SPACE:
            m1 = statistics.mean(P[k] for P, _ in good)
            m0 = statistics.mean(P[k] for P in inputs)
            fmt = lambda v: f"{v:,.3g}" if abs(v) < 1e5 else f"{v / 1000:,.0f}b"
            print(f"{k:<13}{fmt(m1):>14}{fmt(m0):>13}")
        print(f"  Bu cekilislerde ortalama yerlesen daire {statistics.mean(o['N'] for _, o in good) / 1000:.0f} bin (tum cekilis {statistics.mean(n) / 1000:.0f} bin)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
