"""Ilk defter: mulkiyet.

Birim stoku. Kira ve senet bu dosyada yazilmaz.
Satistan cikan deger senet defterine alacak diye not dusulur, burada anapara olmaz.
Sinif payi ve ilce stok adedi gozlem degil. Fiyat Endeksa-Emlakjet ilan endeksi.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from hekis.owner import years_to_sell

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "istanbul_2026.json"

OLCEK = 1000
SINIF_PAYLARI = (0.10, 0.30, 0.50)
ORANLAR = (0.02, 0.04)
TEKLIF = (0.80, 1.00)
UFUK = 5


@dataclass(frozen=True)
class Acilis:
    ilce: str
    m2: float
    fiyat: float
    m2_fiyat: float
    varlik_artis: float
    artis_dondurma: bool
    stok_adet: None
    kaynak: str


def acilis_oku() -> Acilis:
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    sale = raw["sale"]
    return Acilis(
        ilce="Esenyurt",
        m2=float(sale["esenyurt_ortalama_m2"]),
        fiyat=float(sale["esenyurt_ortalama_tl"]),
        m2_fiyat=float(sale["esenyurt_m2_tl"]),
        varlik_artis=float(sale["esenyurt_nominal_yillik"]),
        artis_dondurma=True,
        stok_adet=None,
        kaynak=sale["kaynak"],
    )


def fiyat_yolu(p0: float, g: float, yil: int) -> float:
    return p0 * (1 + g) ** yil


def satis_yili(fiyat: float, teklif: float, oran: float) -> float | None:
    return years_to_sell(fiyat, teklif, fiyat * oran)


def akis(
    p0: float,
    g: float,
    bid_ratio: float,
    oran: float,
    teklif_kurali: str,
    ufuk: int = UFUK,
) -> dict:
    """Bos ucuncu birim. Iskansiz bu akisa girmez.

    teklif_oransal: teklif fiyatin yuzdesi, her yil yeniden.
    teklif_sabit: teklif acilis fiyatina kilitli.
    """
    if teklif_kurali not in ("oransal", "sabit"):
        raise ValueError("teklif oransal veya sabit")
    biriken = 0.0
    satildi = False
    satis_yil = None
    for yil in range(ufuk + 1):
        fiyat = fiyat_yolu(p0, g, yil)
        teklif = fiyat * bid_ratio if teklif_kurali == "oransal" else p0 * bid_ratio
        fark = fiyat - teklif
        bedel = fiyat * oran
        if yil == 0:
            continue
        biriken += bedel
        if not satildi and biriken >= fark and fark > 0:
            satildi = True
            satis_yil = yil
            break
        if fark <= 0:
            satildi = True
            satis_yil = yil
            break
    son_fiyat = fiyat_yolu(p0, g, satis_yil or ufuk)
    son_teklif = son_fiyat * bid_ratio if teklif_kurali == "oransal" else p0 * bid_ratio
    statik = satis_yili(p0, p0 * bid_ratio, oran)
    return {
        "kural": teklif_kurali,
        "oran": oran,
        "teklif_oran": bid_ratio,
        "statik_yil": statik,
        "satis": satildi,
        "satis_yil": satis_yil,
        "cikan_deger": son_teklif if satildi else 0.0,
        "kalan": 0 if satildi else 1,
    }


def olcek_kapanis(satir: dict, pay: float, bosluk: float, olcek: int = OLCEK) -> dict:
    """Ilce stoku bilinmiyor. Olcek sayim degil.

    Yalniz ucuncu ve sonrasi bos birim bedel odet. Satis adedi mulkiyetten duser.
    Cikan deger senet defterine yazilmaz.
    """
    aday = olcek * pay * bosluk
    satilan = aday if satir["satis"] else 0.0
    return {
        "pay": pay,
        "bosluk": bosluk,
        "aday": aday,
        "satilan": satilan,
        "kalan_bos": aday - satilan,
        "cikan_deger_not": satilan * satir["cikan_deger"],
        "kimlik": olcek - satilan,
    }


def rapor() -> str:
    a = acilis_oku()
    if abs(a.m2 * a.m2_fiyat - a.fiyat) > 1:
        raise SystemExit("m2 carpi birim fiyat ortalamayi tutmuyor")
    lines = [
        "ilk defter: mulkiyet",
        f"ilce: {a.ilce}",
        f"fiyat: {a.fiyat:,.0f} TL  ({a.m2:.0f} m2 x {a.m2_fiyat:,.0f})".replace(",", "."),
        f"varlik artisi: {a.varlik_artis:.2%}  dondurma: {a.artis_dondurma}  veri degil",
        f"stok adedi: bilinmiyor  olcek {OLCEK} sayim degil",
        f"kaynak: {a.kaynak}",
        "iskansiz satis adedine girmez",
        "cikan deger senet defterine alacak notu, bu defterde anapara degil",
        "",
        "kural | oran | teklif | statik yil | 5 yilda satis | yil",
    ]
    kosular = []
    for kural in ("oransal", "sabit"):
        for oran in ORANLAR:
            for bid in TEKLIF:
                row = akis(a.fiyat, a.varlik_artis, bid, oran, kural)
                kosular.append(row)
                statik = "gelmez" if row["statik_yil"] is None else f"{row['statik_yil']:.1f}"
                yil = "-" if row["satis_yil"] is None else str(row["satis_yil"])
                lines.append(
                    f"{kural} | {oran:.0%} | {bid:.0%} | {statik} | {row['satis']} | {yil}"
                )
    lines.append("")
    lines.append("pay | bosluk | kural | oran | teklif | satilan / 1000 | kalan bos | cikan deger notu")
    bosluklar = {
        "elektrik_0.037": 0.037,
        "kalinti_0.27": 0.27,
    }
    for row in kosular:
        if row["teklif_oran"] != 0.80:
            continue
        for ad, bosluk in bosluklar.items():
            for pay in SINIF_PAYLARI:
                k = olcek_kapanis(row, pay, bosluk)
                lines.append(
                    f"{pay:.0%} | {ad} | {row['kural']} | {row['oran']:.0%} | {row['teklif_oran']:.0%} | "
                    f"{k['satilan']:.1f} | {k['kalan_bos']:.1f} | {k['cikan_deger_not']:.0f}"
                )
    lines.append("")
    lines.append(
        "statik yil sabit fiyat varsayar. Akis guncel fiyata bakar: "
        "bedel gecmis yillarin fiyatindan birikir, fark bugunku fiyattir. "
        "Yuzde 4 oransal kuralda statik 5 yil, akis 5 yilda satmaz."
    )
    return "\n".join(lines)


def main() -> None:
    print(rapor())


if __name__ == "__main__":
    main()