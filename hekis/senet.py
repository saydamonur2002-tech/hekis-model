"""HEKIS senedi. Para piyasasi fonu degil.

Anapara TUFE ile yurur. Reel kupon sifir. Hedef primi yalniz fiziki endeks
esigi gecince dogar ve tavanlidir. Prim havuzunun 1/7'si senet sahibine,
6/7'si uretim devresinde kalir. Dis aliciya kapali. Doviz, altin, fon,
arsa ve yeni konut itfasi yok.

1/7 gozlem degil. Tasarim payi.
"""

from __future__ import annotations


HOLDER_SHARE = 1 / 7
CIRCUIT_SHARE = 6 / 7


def issue(principal: float, foreign: bool = False) -> dict:
    if foreign:
        raise ValueError("dis aliciya kapali")
    if principal <= 0:
        raise ValueError("anapara pozitif olmali")
    return {
        "anapara": principal,
        "dis_alici": False,
        "itfai": ("hekis",),
        "reel_kupon": 0.0,
        "sahip_payi": HOLDER_SHARE,
    }


def year(principal: float, inflation: float, physical: float, alpha: float = 0.04, cap: float = 0.10) -> dict:
    indexed = principal * (1 + inflation)
    gap = max(0.0, physical - 1.0)
    rate = min(cap, alpha * gap)
    premium = indexed * rate
    return {
        "anapara_nominal": indexed,
        "anapara_reel": principal,
        "prim_havuzu": premium,
        "sahip": premium * HOLDER_SHARE,
        "devre": premium * CIRCUIT_SHARE,
        "reel_kupon": 0.0,
        "oran": rate,
    }


def path(principal: float, inflation: list[float], physical: list[float]) -> list[dict]:
    rows = []
    nominal = principal
    for i, (inf, phy) in enumerate(zip(inflation, physical), start=1):
        row = year(nominal, inf, phy)
        row["yil"] = i
        nominal = row["anapara_nominal"]
        rows.append(row)
    return rows


def format_rows(rows: list[dict]) -> str:
    lines = ["yil | anapara | prim havuzu | sahip 1/7 | devre 6/7"]
    for row in rows:
        lines.append(
            f"{row['yil']} | {row['anapara_nominal']:.0f} | {row['prim_havuzu']:.0f} | {row['sahip']:.0f} | {row['devre']:.0f}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    note = issue(6_033_125_000)
    print("ihrac", note["anapara"], "dis", note["dis_alici"])
    inf = [0.3151] * 3
    print("hedef tutmadi")
    print(format_rows(path(note["anapara"], inf, [0.9, 0.9, 0.9])))
    print("hedef tuttu, endeks 1.25")
    print(format_rows(path(note["anapara"], inf, [1.25, 1.25, 1.25])))
