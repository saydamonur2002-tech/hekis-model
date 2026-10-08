"""Kendi kendini finanse etme kosulu. Modelden bagimsiz cebir, parametre araliklari ile.

Yerlesen daire basina yillik subvansiyon  s  (kira farki + abonelik) TL.
Bos kalan daire basina bedel  fee x deger V x tahsilat c.
Yerlesen oran p. Kendini finanse eder ancak:

    p * s  <=  (1 - p) * V * fee * c      ->      fee * c  >=  (s / V) * p / (1 - p)

Sol taraf etkin bedel orani. Katilim arttikca bedel odeyen taban erir.

    python -m hekis.selffinance
"""

from __future__ import annotations


def required_rate(s_month: float, value: float, p: float) -> float:
    """Gerekli etkin bedel orani (bedel x tahsilat), yillik, degere oranla."""
    return (s_month * 12 / value) * p / (1 - p)


def main() -> int:
    pct = lambda v: f"{v:.1%}"
    print("Gerekli etkin bedel = bedel x tahsilat, degerin yilda yuzdesi")
    print("Denklem: bedel x tahsilat >= (12 s / V) x p / (1 - p)")
    print()
    V = 3_550_000
    ss = (4_000, 6_000, 8_000, 10_000, 14_000)
    print(f"A) Deger V = {V:,} TL (orta ve ucuz semt karisimi). Satir: yerlesen oran p. Sutun: aylik subvansiyon s (kira farki + abonelik)".replace(",", "."))
    print(f"{'p':>6}" + "".join(f"{f's={s:,}'.replace(',', '.'):>12}" for s in ss))
    for p in (0.05, 0.10, 0.20, 0.36, 0.50, 0.60):
        print(f"{p:>6.0%}" + "".join(f"{pct(required_rate(s, V, p)):>12}" for s in ss))
    print()
    s = 8_400
    p = 0.36
    print(f"B) Deger duyarliligi, p = %36, s = {s:,} TL/ay".replace(",", "."))
    print(f"{'V (TL)':>12}{'gerekli etkin':>15}")
    for V2 in (1_500_000, 2_400_000, 3_550_000, 4_700_000, 6_000_000):
        print(f"{V2:>12,}{pct(required_rate(s, V2, p)):>15}".replace(",", "."))
    print()
    print(f"C) Gerekli etkin orani saglamak icin en dusuk tahsilat, V = 3.550.000, s = 8.400")
    print(f"{'p':>6}{'gerekli':>9}" + "".join(f"{f'bedel %{int(f * 100)}':>12}" for f in (0.01, 0.02, 0.03, 0.05)))
    for p in (0.05, 0.10, 0.20, 0.36, 0.50, 0.60):
        r = required_rate(8_400, 3_550_000, p)
        cells = []
        for fee in (0.01, 0.02, 0.03, 0.05):
            c = r / fee
            cells.append(f"{c:.0%}" if c <= 1 else "imkansiz")
        print(f"{p:>6.0%}{pct(r):>9}" + "".join(f"{x:>12}" for x in cells))
    print()
    print("D) Tavan: bedel %5 (Vancouver en yuksek), tahsilat %90 -> etkin %4,5. Bu etkin oranin izin verdigi en yuksek yerlesen oran p:")
    print(f"{'s (TL/ay)':>10}{'V=2,4 mn':>11}{'V=3,55 mn':>11}{'V=4,7 mn':>11}")
    for s in (4_000, 8_400, 14_000):
        cells = []
        for V in (2_400_000, 3_550_000, 4_700_000):
            k = 0.045 * V / (s * 12)
            cells.append(f"{k / (1 + k):.0%}")
        print(f"{s:>10,}".replace(",", ".") + "".join(f"{x:>11}" for x in cells))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
