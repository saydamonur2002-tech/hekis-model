"""Doviz borcu birikimi 2014'ten, TCMB resmi serisiyle.

    python -m hekis.birikim

Gercek net doviz acigi (NOP) 2014-2025 ve 2026-07, TCMB FKDFDVY (hekis/nop_veri.py).
Onceki surum N0 ve katsayilari ABC ile uyduruyordu. Artik seri gercek: uyduracak bir sey yok,
model sinanir. Karsi-olgusal: A-C 2014'ten cozulseydi, gercek dNOP'tan kacinilan pay dusulur.
"""

import random

from hekis.kalibre import KUR, TUFE
from hekis.enflasyon import TUFE_YILLIK, yuzdelik, TOHUM
from hekis.acmaz import degerler
from hekis.nop_veri import (CARRY, DEP, DNOP, KV_NET, KV_NET_2026_07, NOP, NOP_2026_07,
                            S, YIL, boot_havuzu, fit)
import hekis.borc_doviz as bd
from hekis.borc_doviz import RAMPA, aralik, cek_fx, med, simule

GSYH_TL = {2015: 2354.1, 2016: 2630.0, 2017: 3151.5, 2018: 3806.5, 2019: 4402.1, 2020: 5141.7,
           2021: 7433.8, 2022: 15325.9, 2023: 27091.5, 2024: 44676.0, 2025: 63240.5}   # Drive V15
YILLAR = list(range(2015, 2026))
GSYH_USD = {t: GSYH_TL[t] / ((KUR[t - 1] + KUR[t]) / 2) for t in YILLAR}


def i(t):
    return YIL[t]


def veri_blogu():
    L = ["GERCEK SERI (TCMB FKDFDVY), mlr $, pozitif = net doviz acigi"]
    L.append("  yil    NOP  NOP/GSYH$   dNOP  carry   KV net   dVarlik dYukuml")
    for t in YILLAR:
        dv = S["VARLIK"][i(t)] - S["VARLIK"][i(t - 1)]
        dy = S["YUKUMLULUK"][i(t)] - S["YUKUMLULUK"][i(t - 1)]
        L.append("  {}  {:>5.0f}  {:>7.1f}%  {:>+6.1f} {:>+6.1f}  {:>6.1f}  {:>+7.1f} {:>+7.1f}".format(
            t, NOP[t], NOP[t] / GSYH_USD[t] * 100, DNOP[t], CARRY[t], KV_NET[t], dv, dy))
    L.append("  2026-07  {:>4.0f}   (Aralik 2025'ten +{:.1f}; KV net {:.1f})".format(NOP_2026_07, NOP_2026_07 - NOP[2025], KV_NET_2026_07))
    mx = max(NOP.items(), key=lambda x: x[1])
    L.append("  Yillik tepe: {} {:.1f}. 2026-07 {:.1f}: dolar bazinda seri tepesini asti mi: {}".format(mx[0], mx[1], NOP_2026_07, NOP_2026_07 > mx[1]))
    return L


def karsi_olgusal(p, q, c, rampa_g=1.0):
    """Gercek dNOP'tan kacinilan pay: pay*max(f,0) + dongu. Enflasyon: dogrudan A-C + doviz borcu yolu."""
    pay = q["sA"] + q["sB"] + q["sC"]
    v = degerler(p)
    dir_y = (v["A"] + v["B"] + v["C"]) * rampa_g
    e_dir = e_fx = 0.0
    kum = 0.0
    e_onc = dd_onc = 0.0
    ya = {}
    for t in YILLAR:
        di = q["taylor"] * e_onc
        loop = c * max(0.0, di - dd_onc)                      # carry daralmasindan ek kacinilan
        kac = pay * rampa_g * max(DNOP[t], 0.0) + loop
        kum += kac
        oran = kum / GSYH_USD[t] * 100
        dd = q["kappa"] * oran
        a_risk = p["phi1"] * dd
        a_bs = q["rho_bs"] * (oran / 100) * DEP[t] / 100 / p["maliyet_tabani"] * 100
        a_gecis = -p["phi1"] * q["kappa_f"] * (kac / GSYH_USD[t] * 100) * (1 - q["ca_uyum"])
        e_fx = p["atalet"] * e_fx + a_risk + a_bs + a_gecis
        e_dir = p["atalet"] * e_dir + dir_y
        ya[t] = (e_dir + e_fx, e_fx, kum)
        e_onc, dd_onc = e_dir + e_fx, dd
    return ya


def rapor() -> str:
    L = ["BIRIKIM 2014'TEN, GERCEK TCMB SERISI", ""]
    L += veri_blogu()
    b, se, r2, _ = fit()
    cs = [x[1] for x in boot_havuzu()]
    L.append("")
    L.append("CARRY ILISKISI (resmi seri 2015-25): dNOP = a + c*carry: a={:.1f} (se {:.1f}), c={:.2f} (se {:.2f}), R2={:.2f}".format(b[0], se[0], b[1], se[1], r2))
    L.append("  bootstrap c p10-p90: {:.2f}-{:.2f}; c<0 olasiligi %{:.0f}".format(yuzdelik(cs, .1), yuzdelik(cs, .9), 100 * sum(c < 0 for c in cs) / len(cs)))
    b23, _, r23, _ = fit(list(range(2015, 2024)))
    L.append("  2023'e kadar fit: a={:.1f}, c={:.2f}, R2={:.2f}. Yani 2024 oncesi carry hicbir sey acikla(ma)miyor.".format(b23[0], b23[1], r23))
    L.append("  2024-25 rejimi: dNOP/carry = {:.2f} ve {:.2f}".format(DNOP[2024] / CARRY[2024], DNOP[2025] / CARRY[2025]))

    bd.REJIM = "tam"
    rng = random.Random(TOHUM + 1)
    sonuc = []
    for _ in range(3000):
        p, q = cek_fx(rng)
        sonuc.append((p, q, karsi_olgusal(p, q, q["c"])))
    L.append("")
    L.append("TARIHSEL KARSI-OLGUSAL: A-C 2014'ten cozulseydi (dongu dahil, medyan)")
    L.append("    yil          " + "".join("{:>7}".format(t) for t in YILLAR[4:]))
    L.append("    gercek TUFE  " + "".join("{:>7.1f}".format(TUFE[t]) for t in YILLAR[4:]))
    L.append("    karsi-olg.   " + "".join("{:>7.1f}".format(med([TUFE[t] - x[2][t][0] for x in sonuc])) for t in YILLAR[4:]))
    L.append("    NOP gercek   " + "".join("{:>7.0f}".format(NOP[t]) for t in YILLAR[4:]))
    L.append("    NOP karsi    " + "".join("{:>7.0f}".format(med([NOP[t] - x[2][t][2] for x in sonuc])) for t in YILLAR[4:]))
    d25 = [x[2][2025][0] for x in sonuc]
    f25 = [x[2][2025][1] for x in sonuc]
    k25 = [x[2][2025][2] for x in sonuc]
    L.append("  2025 enflasyon dususu {:.1f} puan [{}], doviz borcu kismi {:.2f} [{}]; kacinilan NOP {:.0f} mlr $ [{}]".format(
        med(d25), aralik(d25), med(f25), aralik(f25), med(k25), aralik(k25)))

    L.append("")
    L.append("ILERI 2026-30 (yavas rampa, dongulu): enflasyon %, baz %{:.1f}".format(TUFE_YILLIK * 100))
    for rj in ("tam", "son2yil"):
        bd.REJIM = rj
        rng = random.Random(TOHUM + 2)
        ileri, nop30 = [], []
        for _ in range(3000):
            p, q = cek_fx(rng)
            pay = {"A": q["sA"], "B": q["sB"], "C": q["sC"]}
            ileri.append(simule(p, q, pay, RAMPA["yavas"], dongu=True)["toplam"])
            nop30.append(NOP[2025] + sum(bd.baz_akis(p, q)))
        L.append("  rejim={:<8} ".format(rj) + "".join("{:>7.1f}".format(TUFE_YILLIK * 100 - med([x[t] for x in ileri])) for t in range(5))
                 + "   (p10-p90 2030: {:.0f}-{:.0f}); baz NOP 2030 {:.0f} mlr $".format(
                     TUFE_YILLIK * 100 - yuzdelik([x[4] for x in ileri], .9), TUFE_YILLIK * 100 - yuzdelik([x[4] for x in ileri], .1), med(nop30)))
    bd.REJIM = "tam"
    return "\n".join(L)


def testler():
    out = []
    cs = [x[1] for x in boot_havuzu()]
    out.append(("T-B1 carry katsayisi resmi seride: c {:.2f}-{:.2f} (p10-p90)".format(yuzdelik(cs, .1), yuzdelik(cs, .9)),
                yuzdelik(cs, .1) > 0, "p10 > 0 ise carry anlamli"))
    ayni = sum(1 for t in (2015, 2016, 2017) if (DNOP[t] > 0) == (CARRY[t] > 0))
    out.append(("T-B2 2015-17: dNOP isareti (+,+,+), carry isareti (-,-,+): {}/3 uyumlu. Borc carry negatifken artti".format(ayni),
                ayni >= 2, "carry 2015-16'yi aciklamaz, kuresel likidite hafizasi dogru cikti"))
    b23, _, _, _ = fit(list(range(2015, 2024)))
    h = [(b23[0] + b23[1] * CARRY[t]) - DNOP[t] for t in (2024, 2025)]
    out.append(("T-B3 ornek disi: 2023'e kadar fit 2024-25 dNOP'u {:+.0f}/{:+.0f} mlr $ yanlis tahmin ediyor (gercek {:+.0f}/{:+.0f})".format(
        h[0], h[1], DNOP[2024], DNOP[2025]), max(abs(x) for x in h) < 25, "rejim degisimi"))
    rng = random.Random(9)
    bd.REJIM = "tam"
    tah = []
    for _ in range(3000):
        p, q = cek_fx(rng)
        tah.append(NOP[2025] + bd.baz_akis(p, q)[0] * 7 / 12)
    out.append(("T-B4 2026-07 kor tahmin (model baz, 7 ay): {:.0f} [{}] vs gercek {:.1f}".format(med(tah), aralik(tah), NOP_2026_07),
                abs(med(tah) - NOP_2026_07) < 15, "2026 verisi kalibrasyona girmedi"))
    out.append(("T-B5 kisa vadeli net pozisyon (likidite tamponu): 2022 {:.0f} -> 2026-07 {:.1f} mlr $. Model bunu icermiyor".format(KV_NET[2022], KV_NET_2026_07),
                False, "acik bulgu, modelde olmayan kirilganlik"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (birikim, resmi seri)"]
    gec = 0
    tl = testler()
    for msg, ok, n in tl:
        gec += bool(ok)
        L.append("  [{}] {}  ({})".format("GECTI" if ok else "KALDI", msg, n))
    L.append("  {}/{} gecti".format(gec, len(tl)))
    return "\n".join(L)


def main() -> int:
    print(rapor())
    print()
    print(test_blogu())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
