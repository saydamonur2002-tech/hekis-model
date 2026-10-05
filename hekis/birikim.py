"""Doviz borcu birikimi 2014'ten: geriye kurma, kalibrasyon, tarihsel karsi-olgusal, ileri.

    python -m hekis.birikim

Net doviz acigi (NOP) 2014-2022 icin Drive'da bos. Baslangic stoku N0 bilinmeyen:
  NOP_t = NOP_{t-1} + c_up * max(carry_t, 0) - c_dn * max(-carry_t, 0),   carry = politika faizi - kur artisi
(N0, c_up, c_dn) 2023-25 gozlemlerine (70, 148, 188,6 mlr $, +-12) uydurulur: ABC, kabul-ret.
Kabul edilen uclu, ayni cekilen diger parametrelerle tarihsel karsi-olgusal ve ileri kosuya girer.

Kur 2014-2022: hafizadan, dogrulanmadi (hekis.kalibre). Faiz ve GSYH: Drive Secici_Kredi_Veri V22, V15.
2014-18 carry negatif iken borc artti diye hatirlaniyor (kuresel dolar likiditesi). Model bunu
aciklamaz, bu bilincli bir sinir. Test T-B2 bunu isaretler.
"""

import random
import statistics

from hekis.kalibre import KUR, TUFE
from hekis.enflasyon import TUFE_YILLIK, yuzdelik, TOHUM
from hekis.acmaz import degerler
from hekis.borc_doviz import (GSYH_USD_2025, NOP, RAMPA, cek_fx, simule, aralik, med)

FAIZ = {2015: 7.6, 2016: 7.6, 2017: 8.0, 2018: 15.6, 2019: 20.6, 2020: 10.2, 2021: 17.8,
        2022: 12.9, 2023: 18.6, 2024: 48.7, 2025: 43.2}  # Drive V22
GSYH_TL = {2015: 2354.1, 2016: 2630.0, 2017: 3151.5, 2018: 3806.5, 2019: 4402.1, 2020: 5141.7,
           2021: 7433.8, 2022: 15325.9, 2023: 27091.5, 2024: 44676.0, 2025: 63240.5}  # Drive V15
YILLAR = list(range(2015, 2026))
DEP = {t: (KUR[t] / KUR[t - 1] - 1) * 100 for t in YILLAR}
CARRY = {t: FAIZ[t] - DEP[t] for t in YILLAR}
GSYH_USD = {t: GSYH_TL[t] / ((KUR[t - 1] + KUR[t]) / 2) for t in YILLAR}
TOL = 12.0   # NOP gozlemleri yuvarlak aktarim, +-12 mlr $


def akis(c_up, c_dn, carry):
    return c_up * carry if carry > 0 else c_dn * carry   # carry<0 ise borc cozulur


def hindcast(c_up, c_dn, n0):
    nop, s = {}, n0
    for t in YILLAR:
        s += akis(c_up, c_dn, CARRY[t])
        nop[t] = s
    return nop


def kalibre(n=200000, tohum=TOHUM, atla=None):
    """ABC. atla: bir yili dislayip tahmin etmek icin."""
    rng = random.Random(tohum)
    kabul = []
    for _ in range(n):
        c_up, c_dn, n0 = rng.uniform(1.5, 3.0), rng.uniform(0.0, 0.8), rng.uniform(0.0, 300.0)
        h = hindcast(c_up, c_dn, n0)
        if all(abs(h[t] - NOP[t]) <= TOL for t in (2023, 2024, 2025) if t != atla):
            kabul.append((c_up, c_dn, n0, h))
    return kabul


def karsi_olgusal(p, q, c_up, c_dn, n0, rampa_g=1.0):
    """A-C 2014'ten itibaren tam cozulseydi (g=1): doviz borcu ve enflasyon. Dongu dahil."""
    toplam_pay = q["sA"] + q["sB"] + q["sC"]
    v = degerler(p)
    dir_y = (v["A"] + v["B"] + v["C"]) * rampa_g
    e = e_fx = e_dir = 0.0
    kum = 0.0
    e_onc = dd_onc = 0.0
    ya = {}
    for t in YILLAR:
        di = q["taylor"] * e_onc
        carry_cf = CARRY[t] - di + dd_onc
        f_act = akis(c_up, c_dn, CARRY[t])
        f_cf = (1 - toplam_pay * rampa_g) * akis(c_up, c_dn, carry_cf) if carry_cf > 0 else akis(c_up, c_dn, carry_cf)
        kac = f_act - f_cf
        kum += kac
        oran = kum / GSYH_USD[t] * 100
        dd = q["kappa"] * oran
        a_risk = p["phi1"] * dd
        a_bs = q["rho_bs"] * (oran / 100) * DEP[t] / 100 / p["maliyet_tabani"] * 100
        a_gecis = -p["phi1"] * q["kappa_f"] * (max(kac, 0) / GSYH_USD[t] * 100) * (1 - q["ca_uyum"])
        y_fx = a_risk + a_bs + a_gecis
        e_fx = p["atalet"] * e_fx + y_fx
        e_dir = p["atalet"] * e_dir + dir_y
        e = e_fx + e_dir
        ya[t] = (e, e_fx, kum, oran)
        e_onc, dd_onc = e, dd
    return ya


def rapor() -> str:
    L = ["BIRIKIM 2014'TEN: net doviz acigi (NOP) geriye kurma ve karsi-olgusal"]
    L.append("")
    L.append("Girdi (Drive V22/V15, kur 2014-22 hafizadan):")
    L.append("  yil    kur%   faiz   carry   NOP gozlem")
    for t in YILLAR:
        L.append("  {}  {:>6.1f}  {:>5.1f}  {:>+6.1f}   {}".format(t, DEP[t], FAIZ[t], CARRY[t], "%.0f" % NOP[t] if t in NOP else "-"))
    kab = kalibre()
    L.append("")
    L.append("KALIBRASYON (ABC, 200 bin cekim, tolerans +-{:.0f} mlr $): kabul {} ({:.2f}%)".format(TOL, len(kab), len(kab) / 2000))
    if not kab:
        return "\n".join(L + ["Hicbir cekim 2023-25 gozlemlerine uymadi, model reddedildi."])
    cu = [k[0] for k in kab]; cd = [k[1] for k in kab]; n0 = [k[2] for k in kab]
    L.append("  c_up (mlr $ / carry puan)  medyan {:.2f} [{}]".format(med(cu), aralik(cu)))
    L.append("  c_dn (borc cozulme)         medyan {:.2f} [{}]".format(med(cd), aralik(cd)))
    L.append("  N0 (2014 sonu NOP, mlr $)   medyan {:.0f} [{}]".format(med(n0), aralik(n0)))
    L.append("")
    L.append("  Ima edilen NOP yolu (medyan, mlr $) ve NOP/GSYH$:")
    L.append("    yil   " + "".join("{:>7}".format(t) for t in YILLAR))
    L.append("    NOP   " + "".join("{:>7.0f}".format(med([k[3][t] for k in kab])) for t in YILLAR))
    L.append("    %GSYH " + "".join("{:>7.1f}".format(med([k[3][t] / GSYH_USD[t] * 100 for k in kab])) for t in YILLAR))
    L.append("")

    # karsi-olgusal
    rng = random.Random(TOHUM + 1)
    sm = kab[:3000]
    sonuc = []
    for c_up, c_dn, n0_, h in sm:
        p, q = cek_fx(rng)
        q["c"] = c_up
        sonuc.append((p, q, karsi_olgusal(p, q, c_up, c_dn, n0_), h))
    L.append("TARIHSEL KARSI-OLGUSAL: A-C 2014'ten itibaren tam cozulseydi (dongu dahil, medyan)")
    L.append("    yil          " + "".join("{:>7}".format(t) for t in YILLAR[4:]))
    L.append("    gercek TUFE  " + "".join("{:>7.1f}".format(TUFE[t]) for t in YILLAR[4:]))
    L.append("    karsi-olg.   " + "".join("{:>7.1f}".format(med([TUFE[t] - x[2][t][0] for x in sonuc])) for t in YILLAR[4:]))
    L.append("    NOP/GSYH% gercek " + "".join("{:>7.1f}".format(med([x[3][t] / GSYH_USD[t] * 100 for x in sonuc])) for t in YILLAR[4:]))
    L.append("    NOP/GSYH% karsi  " + "".join("{:>7.1f}".format(med([(x[3][t] - x[2][t][2]) / GSYH_USD[t] * 100 for x in sonuc])) for t in YILLAR[4:]))
    d25 = [x[2][2025][0] for x in sonuc]
    f25 = [x[2][2025][1] for x in sonuc]
    k25 = [x[2][2025][2] for x in sonuc]
    L.append("")
    L.append("  2025: enflasyon dususu medyan {:.1f} puan [{}]; bunun doviz borcu uzerinden kismi {:.2f} [{}]".format(
        med(d25), aralik(d25), med(f25), aralik(f25)))
    L.append("  2025: kacinilan birikmis doviz borcu {:.0f} mlr $ [{}] (gercek NOP 189)".format(med(k25), aralik(k25)))

    # ileri, kalibre c ile
    r = RAMPA["yavas"]
    rng = random.Random(TOHUM + 2)
    ileri = []
    for c_up, c_dn, n0_, h in sm:
        p, q = cek_fx(rng)
        q["c"] = c_up
        pay = {"A": q["sA"], "B": q["sB"], "C": q["sC"]}
        ileri.append(simule(p, q, pay, r, dongu=True)["toplam"])
    L.append("")
    L.append("ILERI 2026-30, c kalibre (yavas rampa, dongulu): enflasyon %, baz %{:.1f}".format(TUFE_YILLIK * 100))
    L.append("    yil      " + "".join("{:>8}".format(2026 + t) for t in range(5)))
    L.append("    medyan   " + "".join("{:>8.1f}".format(TUFE_YILLIK * 100 - med([x[t] for x in ileri])) for t in range(5)))
    L.append("    p10-p90  " + "".join("{:>8}".format("{:.0f}-{:.0f}".format(
        TUFE_YILLIK * 100 - yuzdelik([x[t] for x in ileri], .9), TUFE_YILLIK * 100 - yuzdelik([x[t] for x in ileri], .1))) for t in range(5)))
    return "\n".join(L)


def testler():
    out = []
    kab = kalibre()
    cu = [k[0] for k in kab]
    ok1 = bool(kab) and yuzdelik(cu, .1) <= 2.70 and yuzdelik(cu, .9) >= 1.89
    out.append(("T-B1 uyum: {} cekim kabul (%{:.2f}, N0 genis oldugu icin dusuk beklenir). c_up {} ile dogrudan 2024-25 kestirimi 1,89-2,70 ortusuyor mu".format(
        len(kab), len(kab) / 2000, aralik(cu) if kab else "-"), ok1, "oran degil ortusme olculur"))
    # T-B2: carry modeli 2015-18 birikimini aciklar mi. Model: carry<0 iken borc cozulur.
    h = [k[3] for k in kab]
    dus = med([x[2018] - x[2015] for x in h]) if h else float("nan")
    out.append(("T-B2 2015-18 model NOP degisimi {:+.0f} mlr $ (carry negatif). Hafiza: o yillarda borc ARTTI (kuresel likidite). Model yanlis isaret".format(dus),
                dus > 0, "carry kanali yalniz 2019 sonrasi rejim icin gecerli"))
    # T-B3: bir yili disarida birak, 2025 tahmini
    kab2 = kalibre(atla=2025)
    if kab2:
        tah = [k[3][2025] for k in kab2]
        hata = med(tah) - NOP[2025]
        out.append(("T-B3 2025 gozlemi disarida, tahmin {:.0f} [{}] vs gercek {:.0f}".format(med(tah), aralik(tah), NOP[2025]),
                    abs(hata) < TOL * 1.5, "hata {:+.0f}".format(hata)))
    else:
        out.append(("T-B3 2025 disarida kabul 0", False, ""))
    # T-B4: ima edilen stok negatif olmamali
    neg = sum(1 for k in kab if min(k[3].values()) < 0) / max(len(kab), 1)
    out.append(("T-B4 ima edilen NOP yolunda negatif deger orani %{:.0f}".format(100 * neg), neg < 0.2, "negatif stok anlamsiz"))
    # T-B5: N0 makul mu (mutlak kistas yok, yalniz yorum)
    out.append(("T-B5 N0 kalibrasyonun kistasi disarida: Drive'da 2014-22 NOP bos. Gercek seriyle (TCMB) karsilastir", False,
                "bu test acik, veri bekliyor"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (birikim)"]
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
