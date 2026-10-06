"""blokaj.py icin olcum: gercek dosya sayimindan I, B0, delta kestirimi.

    python -m hekis.blokaj_veri data/dosya_sayim.csv     # gercek veri, data/kurumlar_olculen.json yazar
    python -m hekis.blokaj_veri --test                   # sentetik veride yontem kendini sinar

CSV sutunlari (sablon: data/dosya_sayim_sablon.csv), satir = kurum x yil:
  kurum   kurum sinifi adi (kurumlar.json ile ayni)
  yil     donem
  C       formal merkezilesme olcusu, 0-1 (nasil olculdugunu SEN tanimlarsin, bkz. data/OLCUM.md)
  n_D     D'nin kayitli dosya sayisi (rapor, tutanak, teftis dosyasi)
  n_X     D'den BAGIMSIZ ikinci kaynaktaki dosya sayisi (ihale ilani, bagis kaydi, sikayet, basin tarama)
  m       iki kaynakta da gorunen dosya sayisi
  y       n_D icinden pencere icinde yaptirima donenler (savcilik sevki, tahsil, idari ceza)

Kestirimler:
  I  = m / n_X                 yakalama-yeniden yakalama: n_X'in ne kadari D'de de var.
  B  = 1 - y / n_D             D'nin bildigi dosyalarin yaptirima donmeyen payi.
  delta  kurum sabit etkili egim: B_kt = B0_k + delta C_kt.
Belirsizlik: binom bootstrap (I, B), satir bootstrap (delta).

Sinirlar (olcumun kimlik sorunu):
- I icin iki kaynak bagimsiz olmali. Ikisi de ayni seyi gorunur kilar (ornegin ikisi de basindan beslenir ve
  D basini izler) ise N dusuk, I yuksek cikar. Pozitif bagimlilik I'yi sisirir.
- Sayistay raporu da D'nin parcasidir. Rapor ele gecirilmis organdan geliyorsa n_D kendisi secilmistir; bu
  yontem onu yakalamaz, yalniz n_X ile karsilastirma yakalar.
- y'nin penceresi (kac yil beklendi) B'yi etkiler; gec yaptirim erken yilda B'yi yukari iter.
- 'Rakip hat acti' ile 'devlet denetledi' y icinde ayrilmaz. B bu yuzden alt sinir olabilir.
- C bir olcu degil bir tanimdir. delta bu tanima baglidir.
"""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

from hekis.blokaj import VERI

CIKTI = VERI.parent / "kurumlar_olculen.json"
N_BOOT = 2000


def okuma(yol: Path) -> list[dict]:
    rows = []
    with open(yol, newline="") as f:
        for r in csv.DictReader(f):
            rows.append({"kurum": r["kurum"], "yil": int(r["yil"]), "C": float(r["C"]),
                         "n_D": int(r["n_D"]), "n_X": int(r["n_X"]), "m": int(r["m"]), "y": int(r["y"])})
    for r in rows:
        if not (0 <= r["m"] <= min(r["n_D"], r["n_X"]) and 0 <= r["y"] <= r["n_D"] and 0 <= r["C"] <= 1):
            raise ValueError(f"tutarsiz satir: {r}")
    return rows


def _binom(n: int, p: float, rng: random.Random) -> int:
    p = min(1.0, max(0.0, p))
    if hasattr(rng, "binomialvariate"):          # Python 3.12+
        return rng.binomialvariate(n, p)
    return sum(rng.random() < p for _ in range(n))


def _araliklar(xs: list[float]) -> tuple[float, float]:
    xs = sorted(xs)
    return xs[int(0.05 * len(xs))], xs[int(0.95 * len(xs)) - 1]


def tahmin_kurum(rows: list[dict], seed: int = 3) -> dict:
    rng = random.Random(seed)
    nD = sum(r["n_D"] for r in rows)
    nX = sum(r["n_X"] for r in rows)
    m = sum(r["m"] for r in rows)
    y = sum(r["y"] for r in rows)
    I = m / nX if nX else float("nan")
    B = 1 - y / nD if nD else float("nan")
    Is = [_binom(nX, I, rng) / nX for _ in range(N_BOOT)]
    Bs = [1 - _binom(nD, 1 - B, rng) / nD for _ in range(N_BOOT)]
    return {"I": I, "I_ara": _araliklar(Is), "B": B, "B_ara": _araliklar(Bs), "n_D": nD, "n_X": nX}


def _egim(rows: list[dict]) -> float | None:
    """Kurum sabit etkili OLS egimi: B_kt uzerine C_kt. Agirlik n_D."""
    by: dict[str, list[tuple[float, float, int]]] = {}
    for r in rows:
        if r["n_D"] > 0:
            by.setdefault(r["kurum"], []).append((r["C"], 1 - r["y"] / r["n_D"], r["n_D"]))
    num = den = 0.0
    for lst in by.values():
        w = sum(x[2] for x in lst)
        c0 = sum(x[0] * x[2] for x in lst) / w
        b0 = sum(x[1] * x[2] for x in lst) / w
        for c, b, wt in lst:
            num += wt * (c - c0) * (b - b0)
            den += wt * (c - c0) ** 2
    return num / den if den > 0 else None


def delta(rows: list[dict], seed: int = 5) -> dict:
    rng = random.Random(seed)
    d = _egim(rows)
    if d is None:
        return {"delta": None, "delta_ara": None, "not": "C kurum icinde degismiyor, delta tanimlanamaz"}
    bs = []
    for _ in range(N_BOOT):
        b = _egim([rng.choice(rows) for _ in rows])
        if b is not None:
            bs.append(b)
    lo, hi = _araliklar(bs) if bs else (None, None)
    return {"delta": d, "delta_ara": (lo, hi), "not": "aralik 0'i iceriyorsa isaret bilinmiyor"}


def _sentetik(seed: int = 1) -> tuple[list[dict], dict]:
    """YONTEM SINAMASI icin sentetik veri. Gercek degil. Bilinen gercek parametre ile uretilir."""
    rng = random.Random(seed)
    gercek = {"I": 0.55, "B0": 0.30, "delta": 0.35}
    rows = []
    for yil in range(2015, 2025):
        C = 0.2 + 0.07 * (yil - 2015)
        N = 4000
        nX = _binom(N, 0.5, rng)
        # D'nin dosyalari: her dosya D'de I olasilikla, X'ten bagimsiz
        nD_total = _binom(N, gercek["I"], rng)
        m = _binom(nX, gercek["I"], rng)
        B = min(1.0, gercek["B0"] + gercek["delta"] * C)
        y = _binom(nD_total, 1 - B, rng)
        rows.append({"kurum": "ornek", "yil": yil, "C": C, "n_D": nD_total, "n_X": nX, "m": m, "y": y})
    return rows, gercek


def test(tekrar: int = 200) -> str:
    """Kapsama sinamasi: %90 aralik gercek degeri ~%90 yakaliyor mu? Tek kosu karar vermez."""
    kapI = kapD = 0
    for sd in range(tekrar):
        rows, g = _sentetik(seed=100 + sd)
        t = tahmin_kurum(rows, seed=sd)
        d = delta(rows, seed=sd)
        kapI += t["I_ara"][0] <= g["I"] <= t["I_ara"][1]
        kapD += d["delta_ara"][0] <= g["delta"] <= d["delta_ara"][1]
    rows, g = _sentetik()
    t, d = tahmin_kurum(rows), delta(rows)
    return (f"SENTETIK sinama ({tekrar} veri seti; gercek I={g['I']}, B0={g['B0']}, delta={g['delta']})\n"
            f"tek kosu: I {t['I']:.3f} [{t['I_ara'][0]:.3f}, {t['I_ara'][1]:.3f}], "
            f"delta {d['delta']:.3f} [{d['delta_ara'][0]:.3f}, {d['delta_ara'][1]:.3f}]\n"
            f"%90 araligin gercek degeri yakalama orani: I {kapI / tekrar:.0%}, delta {kapD / tekrar:.0%} (hedef ~90%)")


def calistir(yol: Path) -> str:
    rows = okuma(yol)
    if not rows:
        return "CSV bos. Sablonu doldur: data/dosya_sayim_sablon.csv, aciklama data/OLCUM.md."
    d = json.loads(VERI.read_text())
    out = []
    for k in d["kurumlar"]:
        kr = [r for r in rows if r["kurum"] == k["ad"]]
        if not kr:
            out.append(f"{k['ad']}: veri yok, parametre ornek olarak kaldi")
            continue
        t = tahmin_kurum(kr)
        dd = delta(kr)
        meanC = sum(r["C"] for r in kr) / len(kr)
        k["I"] = round(t["I"], 3)
        if dd["delta"] is not None:
            k["delta"] = round(dd["delta"], 3)
            k["B0"] = round(min(1.0, max(0.0, t["B"] - dd["delta"] * meanC)), 3)
        else:
            k["B0"] = round(t["B"], 3)
        k["_olculdu"] = True
        out.append(f"{k['ad']}: I {t['I']:.2f} {tuple(round(x, 2) for x in t['I_ara'])}, B {t['B']:.2f} "
                   f"{tuple(round(x, 2) for x in t['B_ara'])}, delta {dd['delta']} {dd['delta_ara']}")
    CIKTI.write_text(json.dumps(d, indent=2, ensure_ascii=False))
    out.append(f"yazildi: {CIKTI.name}. Calistir: python -m hekis.blokaj {CIKTI}")
    out.append("Not: yalniz I, B0, delta olculdu; tau, a, r, p_pat, q_rival, phi hala ornek.")
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print(test())
    elif len(sys.argv) > 1:
        print(calistir(Path(sys.argv[1])))
    else:
        print(__doc__)
