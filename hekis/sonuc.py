"""Kanonik sonuc: uclu acmaz cozulurse enflasyon kac puan duser.

    python -m hekis.sonuc

Tek sayi kaynagi. Dogrudan etki (kira A, mahsup B, ic borclanma C) + doviz borcu uzerinden etki
(borc_doviz.py, doviz bu kanallarin sonucu) + faiz-carry dongusu. Yil 1-5, yavas uygulama rampasi.

Sonuc bir TAHMIN degil, katki ayristirmasidir: baz TUFE %31,5'te dondurulur ('cozum yoksa'),
sonra cozumun puan katkisi dusulur. Tahmin icin: hekis/ovp.py.
"""

import random
import statistics

import hekis.borc_doviz as bd
from hekis.borc_doviz import RAMPA, cek_fx, simule, aralik, med
from hekis.acmaz import degerler
from hekis.enflasyon import TOHUM, TUFE_YILLIK, yuzdelik

R = RAMPA["yavas"]
BAZ = TUFE_YILLIK * 100


def kos(rejim, n=4000, tohum=TOHUM):
    bd.REJIM = rejim
    rng = random.Random(tohum)
    out = []
    for _ in range(n):
        p, q = cek_fx(rng)
        pay = {"A": q["sA"], "B": q["sB"], "C": q["sC"]}
        s = simule(p, q, pay, R, dongu=True)
        v = degerler(p)
        out.append({"toplam": s["toplam"], "dir": s["e_dir"], "fx": s["e_fx"], "A1": v["A"], "B1": v["B"], "C1": v["C"]})
    bd.REJIM = "tam"
    return out


def rapor() -> str:
    L = ["KANONIK SONUC: UCLU ACMAZ COZULURSE ENFLASYON KAC PUAN DUSER", ""]
    L.append("Yavas uygulama (25/50/75/100%), baz TUFE %{:.1f} dondurulmus. Puan dusus, medyan [p10-p90]".format(BAZ))
    L.append("")
    for rj, ad in (("tam", "carry rejimi 'tam ornek' (c ~0,75)"), ("son2yil", "carry rejimi '2024-25' (c ~2,3)")):
        o = kos(rj)
        L.append("REJIM: {}".format(ad))
        L.append("  yil              2026      2027      2028      2029      2030")
        L.append("  toplam dusus   " + "".join("{:>9.2f}".format(med([x["toplam"][t] for x in o])) for t in range(5)))
        L.append("  enflasyon %    " + "".join("{:>9.1f}".format(BAZ - med([x["toplam"][t] for x in o])) for t in range(5)))
        L.append("  p10-p90 %      " + "".join("{:>9}".format("{:.0f}-{:.0f}".format(
            BAZ - yuzdelik([x["toplam"][t] for x in o], .9), BAZ - yuzdelik([x["toplam"][t] for x in o], .1))) for t in range(5)))
        L.append("  5. yil: dogrudan (A+B+C) {} + doviz borcu {} = toplam {}".format(
            aralik([x["dir"][4] for x in o]), aralik([x["fx"][4] for x in o]), aralik([x["toplam"][4] for x in o])))
        L.append("")
    o = kos("tam")
    o2 = kos("son2yil")
    L.append("KANAL BAZINDA YIL-1 (dogrudan, haircut oncesi): A kira {:.2f}, B mahsup {:.2f}, C ic borc {:.2f} puan".format(
        med([x["A1"] for x in o]), med([x["B1"] for x in o]), med([x["C1"] for x in o])))
    L.append("")
    L.append("OKUMA")
    L.append("  5 yilda toplam dusus {:.1f} puan (tam ornek) / {:.1f} puan (2024-25 rejimi). Dogrudan ~{:.1f}, doviz borcu uzerinden ~{:.1f} (kappa'ya bagli).".format(
        med([x["toplam"][4] for x in o]), med([x["toplam"][4] for x in o2]), med([x["dir"][4] for x in o]), med([x["fx"][4] for x in o])))
    L.append("  Cozumun asil degeri enflasyonu mekanik dusurmesi degil, doviz borcu ve kirilma riskini azaltmasi olabilir (kirilma.py).")
    L.append("  Eski %19 ve 'hepsi %4,7' sonuclari dissal doviz kanalina dayaniyordu, reddedildi, KALDIRILDI.")
    return "\n".join(L)


def main() -> int:
    print(rapor())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
