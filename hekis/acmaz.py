"""Ucluk acmaz: kanallar tek tek mi, birlikte mi cozulur, ve cozulunce enflasyon yolu.

    python -m hekis.acmaz

Acmaz iddiasi: kira (A), mahsup (B), ic borclanma (C) ayni stok-akis dongusunu paylasir.
Birini tek basina cozmek etkisinin bir kismini sizdirir, cunku cozulmeyen digerleri geri
besler. Sizinti VARSAYIMdir, veriden tanimlanamaz. Doviz bu kanallarin SONUCU olarak ayri
kurulur (borc_doviz.py); eski dissal doviz kanali kaldirildi (reddedildi, kappa ~12 gerektiriyordu).

Altkume S cozulurse kanal i katkisi: v_i * (1 - sizinti_i * (3 - |S|) / 2).
|S|=3 iken sizinti 0, |S|=1 iken sizinti_i kadar kayip.

Dinamik: e_t = atalet * e_{t-1} + y1 * g_t, g_t uygulama rampasi. Enflasyon yolu: baz - e_t.
Baz %31,5'te dondurulmustur (repo varsayimi), yani 'hicbir sey yapilmazsa' kosusu bir tahmin degildir.
"""

import itertools
import random
import statistics

from hekis.enflasyon import TUFE_YILLIK, cek, kanallar, yuzdelik, TOHUM, N

KANAL = ("A", "B", "C")
RAMPA = {
    "yavas (25/50/75/100)": [0.25, 0.5, 0.75, 1.0, 1.0],
    "hizli (50/100)": [0.5, 1.0, 1.0, 1.0, 1.0],
    "yarim (50 sabit)": [0.5] * 5,
}


def degerler(p):
    """Haircut uygulanmis tam cozum yil-1 degerleri."""
    k = kanallar(p)
    h = 1.0 - p["ortusme"]
    return {"A": k["A kira"] * h, "B": k["B mahsup"] * h, "C": k["C ic borc"] * h}


def altkume(v, sizinti, S):
    if not S:
        return 0.0
    pay = (3 - len(S)) / 2.0
    return sum(v[i] * (1 - sizinti[i] * pay) for i in S)


def yol(y1, atalet, rampa):
    e, out = 0.0, []
    for g in rampa:
        e = atalet * e + y1 * g
        out.append(e)
    return out


def kos(n=N, tohum=TOHUM):
    rng = random.Random(tohum)
    sonuc = []
    for _ in range(n):
        p = cek(rng)
        v = degerler(p)
        sz = {i: rng.uniform(0.0, 0.4) for i in KANAL}
        sonuc.append((p, v, sz))
    return sonuc


def med(x):
    return statistics.median(x)


def rapor() -> str:
    s = kos()
    L = []
    L.append("UCLU ACMAZ (A kira, B mahsup, C ic borc). Yil-1 puan, medyan [p10-p90]")
    L.append("")
    L.append("Altkume                   yil 1")
    for r in (1, 2, 3, 4):
        for S in itertools.combinations(KANAL, r):
            x = [altkume(v, sz, S) for _, v, sz in s]
            L.append("  {:<22}{:>6.2f}  [{:.2f} - {:.2f}]".format("+".join(S), med(x), yuzdelik(x, .1), yuzdelik(x, .9)))
    L.append("")
    tek = [sum(altkume(v, sz, (i,)) for i in "ABC") for _, v, sz in s]
    ort = [altkume(v, sz, ("A", "B", "C")) for _, v, sz in s]
    L.append("Ucluk: tek tek cozumlerin toplami {:.2f}, birlikte {:.2f}. Acmaz primi {:+.2f} puan.".format(
        med(tek), med(ort), med(ort) - med(tek)))
    L.append("(Prim varsayima bagli, veriden tanimlanamaz. Doviz borcu etkisi: python -m hekis.sonuc)")
    L.append("")

    L.append("DINAMIK: uc kanal cozulurse, YALNIZ dogrudan etki (doviz borcu haric, bkz sonuc.py), baz %{:.1f} dondurulmus".format(TUFE_YILLIK * 100))
    for ad, rampa in RAMPA.items():
        yollar = [[TUFE_YILLIK * 100 - e for e in yol(altkume(v, sz, KANAL), p["atalet"], rampa)] for p, v, sz in s]
        L.append("  {}".format(ad))
        L.append("    yil        " + "".join("{:>9}".format(t) for t in range(1, 6)))
        L.append("    medyan %   " + "".join("{:>9.1f}".format(med([y[t] for y in yollar])) for t in range(5)))
        L.append("    p10-p90    " + "".join("{:>9}".format("{:.0f}-{:.0f}".format(
            yuzdelik([y[t] for y in yollar], .1), yuzdelik([y[t] for y in yollar], .9))) for t in range(5)))
    L.append("")
    kota = [TUFE_YILLIK * 100 - yol(altkume(v, sz, KANAL), p["atalet"], RAMPA["yavas (25/50/75/100)"])[-1] for p, v, sz in s]
    L.append("Yavas rampada 5. yil: %20 altina inme olasiligi {:.0f}%, %15 altina {:.0f}%".format(
        100 * sum(k < 20 for k in kota) / len(kota), 100 * sum(k < 15 for k in kota) / len(kota)))
    return "\n".join(L)


def main() -> int:
    print(rapor())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
