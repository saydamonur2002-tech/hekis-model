"""Kalibrasyon ve duyarlilik.

Kalibre edilebilen: sahibin reel fiyat beklentisi kuralinin pencere uzunlugu. Gercek KFE serisiyle
bir yil ilerisini tahmin etme testi. Kalibre edilemeyen: katilim tavani ve egimi. Gozlem yok.
Onlar icin bant verilir, tek sayi verilmez.

    python -m hekis.calibrate
"""

from __future__ import annotations

import math

from hekis import activation
from hekis.bind import load_obs


def series(obs: dict) -> dict[int, float]:
    k = obs["kfe_reel_yillik"]
    return {int(y): v for y, v in k.items() if y.isdigit()}


def window_errors(obs: dict, max_window: int = 4) -> list[tuple[str, float, float, int]]:
    """Bir yil ilerisi tahmini: her pencere icin RMSE, MAE, ornek sayisi. Ayni ornekler uzerinde."""
    r = series(obs)
    years = [y for y in sorted(r) if y - max_window >= min(r)]
    out = []
    methods = {"sifir": lambda y: 0.0}
    for w in range(1, max_window + 1):
        methods[f"son {w} yil"] = (lambda w: lambda y: sum(r[y - i] for i in range(1, w + 1)) / w)(w)
    methods["uzun ort. (gecmis hepsi)"] = lambda y: sum(r[x] for x in r if x < y) / len([x for x in r if x < y])
    for name, f in methods.items():
        errs = [f(y) - r[y] for y in years]
        out.append((name, math.sqrt(sum(e * e for e in errs) / len(errs)), sum(abs(e) for e in errs) / len(errs), len(errs)))
    return out


def best_window(obs: dict, max_window: int = 4) -> int:
    best = min(((e[1], i + 1) for i, e in enumerate(window_errors(obs, max_window)[1:max_window + 1])), key=lambda t: t[0])
    return best[1]


def band(obs: dict, window: int) -> None:
    tl = lambda v: f"{v:,.0f}".replace(",", ".")
    bn = lambda v: f"{v / 1e9:,.0f}".replace(",", ".")
    stok = obs["bos_stok"]["ibb_elektrik_su_tabanli"]
    c = activation.hold_cost_ratio(obs)
    g = activation.expected_real_growth(obs, window=window)
    print(f"Bugun beklenen reel artis (pencere {window}): {g:.1%}. 450 bin bos stok, bedel %1.")
    print("Katilim tavani x egim: giren daire (bin) / 20 yil yuk (mr TL, bugunku)")
    caps = (0.10, 0.20, 0.40, 0.60)
    print(f"{'egim':>6}" + "".join(f"{f'tavan %{int(c_ * 100)}':>22}" for c_ in caps))
    lo, hi = None, None
    for slope in (10.0, 25.0, 50.0):
        cells = []
        for cap in caps:
            p = activation.participation(g, c, 0.01, slope, cap)
            n = stok * p
            r = activation.run(obs, {"orta": 0.5, "ucuz": 0.5}, n)
            cells.append(f"{n / 1000:7.0f} / {bn(r.total_fiscal_real):>5}")
            lo = n if lo is None else min(lo, n)
            hi = n if hi is None else max(hi, n)
        print(f"{slope:>6.0f}" + "".join(f"{x:>22}" for x in cells))
    print(f"Bant: {tl(lo)} - {tl(hi)} daire")


def analog_scenarios(obs: dict, window: int) -> None:
    """Yurt disi benzerleriyle sinirlanan uc senaryo. Tavan secimi analoga dayanir, kalibrasyon degildir."""
    bn = lambda v: f"{v / 1e9:,.0f}".replace(",", ".")
    stok = obs["bos_stok"]["ibb_elektrik_su_tabanli"]
    c = activation.hold_cost_ratio(obs)
    g = activation.expected_real_growth(obs, window=window)
    scen = (
        ("gonullu tek basina (PAA, Irlanda RLS)", 0.05, 0.0),
        ("karma: bedel %1, tavan %40 (mevcut)", 0.40, 0.01),
        ("Vancouver benzeri: bedel %3, tavan %55", 0.55, 0.03),
    )
    print(f"{'senaryo':<42}{'katilim':>9}{'daire (bin)':>13}{'giris mr':>10}{'yuk mr (20y)':>14}")
    for name, cap, fee in scen:
        p = activation.participation(g, c, fee, 25.0, cap)
        n = stok * p
        r = activation.run(obs, {"orta": 0.5, "ucuz": 0.5}, n)
        print(f"{name:<42}{p:>9.1%}{n / 1000:>13.0f}{bn(r.entry_value):>10}{bn(r.total_fiscal_real):>14}")


def main() -> int:
    obs = load_obs()
    print("1) Beklenti kurali: bir yil ilerisi reel KFE artisini tahmin hatasi (pp)")
    print(f"{'yontem':<28}{'RMSE':>8}{'MAE':>8}{'n':>5}")
    for name, rmse, mae, n in window_errors(obs):
        print(f"{name:<28}{rmse * 100:>8.1f}{mae * 100:>8.1f}{n:>5}")
    w = best_window(obs)
    print(f"Secilen pencere: {w} (en dusuk RMSE, 1-4 arasi)")
    print()
    print("2) Katilim bandi")
    band(obs, w)
    print()
    print("3) Yurt disi benzerleriyle sinirlanan senaryolar (450 bin bos stok)")
    analog_scenarios(obs, w)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
