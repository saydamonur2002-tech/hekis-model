"""Elde tutma maliyeti ile havuz teklifi. Kanun degil, karar kurali.

Birincil konut muaf. Ikinci konut hafif. Ucuncu ve sonrasi artan bos tutma bedeli.
Satis ancak havuz teklifi ile piyasa arasindaki fark, bos tutmanin birikmis maliyetinden kucukse gelir.
Kira geliri bu blokta yok. Duran stok isler kilinacak stoktur.
Oranlar gozlem degil. Esenyurt fiyati gozlem.
"""

from __future__ import annotations


def years_to_sell(market: float, bid: float, annual_cost: float) -> float | None:
    gap = market - bid
    if gap <= 0:
        return 0.0
    if annual_cost <= 0:
        return None
    return gap / annual_cost


def schedule(market: float, rates: dict[str, float], bid_ratio: float) -> list[dict]:
    bid = market * bid_ratio
    rows = []
    for name, rate in rates.items():
        cost = market * rate
        years = years_to_sell(market, bid, cost)
        rows.append(
            {
                "sinif": name,
                "oran": rate,
                "yillik_maliyet": cost,
                "havuz": bid,
                "fark": market - bid,
                "yil": years,
                "gelir": years is not None and years <= 5,
            }
        )
    return rows


def format_rows(rows: list[dict]) -> str:
    lines = ["sinif | oran | yillik | fark | yil | 5 yilda gelir"]
    for row in rows:
        year = "gelmez" if row["yil"] is None else f"{row['yil']:.1f}"
        lines.append(
            f"{row['sinif']} | {row['oran']:.1%} | {row['yillik_maliyet']:.0f} | {row['fark']:.0f} | {year} | {row['gelir']}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    market = 3_619_875
    rates = {"birincil": 0.0, "ikinci": 0.002, "ucuncu_arti": 0.02}
    print("Esenyurt ortalama, havuz piyasanin yuzde 80'i")
    print(format_rows(schedule(market, rates, 0.80)))
    print()
    print("Ayni stok, havuz piyasanin yuzde 100'u")
    print(format_rows(schedule(market, rates, 1.0)))
