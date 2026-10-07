"""OVP 2027-2029 ve TCMB yollari ile modelin tahmin yolu.

    python -m hekis.ovp

Iki soru:
  1. Tahmin: modelin 2026-2029 Aralik/Aralik enflasyon yolu, belirsizlik bandiyla.
  2. OVP/TCMB simulasyonu: resmi yollar tutmak icin her yil ne kadar EK dezenflasyon (kalinti) gerekir, tarihte ne kadar gorulmus.

Tahmin cekirdegi: TUFE_t = a + b*kur_t + rho*TUFE_t-1 + delta_t (hekis/kalibre.py, 10 gozlem, bootstrap).
Bu yapinin ornek disi sicili zayiftir (gerceklik.py T2/T3). Sonuc 'model onerir' degil, 'bu yapi ne gosterir'.

Resmi rakamlar arama ozetlerinden (OVP 2027-2029, TCMB Enflasyon Raporu 2026-III, Agustos 2026).
Kur: 2026 gozlem tempo (%16-20); sonraki yillar kayma kurali kur_t = oran * TUFE_t-1 (2024-26 gozlem: 0,31, 0,49, 0,63).
"""

import random
import statistics

from hekis.enflasyon import TOHUM, yuzdelik
from hekis.kalibre import KUR, TUFE, ols
import hekis.borc_doviz as bd
from hekis.borc_doviz import RAMPA, cek_fx, simule

YILLAR = (2026, 2027, 2028, 2029)
OVP = {2026: 28.4, 2027: 21.0, 2028: 13.5, 2029: 9.0}        # yil sonu TUFE, OVP 2027-2029
TCMB = {2026: 28.0, 2027: 15.0, 2028: 9.0}                    # TCMB Ag 2026 tahmini (2026 tahmin, 2027 ara hedef/tahmin, 2028)
OVP_ARA = {"buyume": (3.3, 4.2, 4.6, 5.0), "acik_gsyh": (3.1, 3.5, 3.1, 2.8), "faiz_disi": (0.2, 0.1, 0.4, 0.6),
           "cari_mlr": (47.5, 38.5, 37.0, 35.5)}
OVP_ESKI_2026 = 16.0                                          # OVP 2026-2028 (Eylul 2025): 2026 tahmini 16, simdi 28,4
# gecmis OVP hatalari (HAFIZADAN, dogrulanmadi): 2025 icin 17,5 (gerceklesen 30,9); 2024 icin 33 (gerceklesen 44,4)
OVP_GECMIS = [(2024, 33.0, 44.4), (2025, 17.5, 30.9), (2026, OVP_ESKI_2026, 28.4)]
KALINTI_TARIH = {"2024": -5.7, "2025": -6.1}                  # kalibre.py kalintilari, sikî politika yillari
YIL2026_KALINTI = +2.0                                       # model 26,0 vs TCMB 28 (kirilma.py T-K3)


def boot_coef(n=3000, tohum=TOHUM):
    d = {t: (KUR[t] / KUR[t - 1] - 1) * 100 for t in range(2015, 2026)}
    ys = list(range(2016, 2026))
    rng = random.Random(tohum)
    out = []
    while len(out) < n:
        ornek = [rng.choice(ys) for _ in ys]
        if len(set(d[t] for t in ornek)) < 3:
            continue
        try:
            b, _, _, _ = ols([[1, d[t], TUFE[t - 1]] for t in ornek], [TUFE[t] for t in ornek])
        except ZeroDivisionError:
            continue
        if 0 <= b[2] <= 1.2:
            out.append(tuple(b))
    return out


def yol(coef, oran, d26, delta, J=0.0, pi0=30.9):
    """2026-2029 yil sonu TUFE. J: 2027'de kayma ustu kur sicramasi (puan)."""
    a, b, rho = coef
    pi = pi0
    out = {}
    for t in YILLAR:
        d = d26 if t == 2026 else oran * pi
        if t == 2027:
            d += J
        pi = max(3.0, a + b * d + rho * pi + delta)
        out[t] = pi
    return out


def kos(n=3000, tohum=TOHUM, mod="cipa"):
    """mod 'tarih': delta ~ U(-4,2) (2024-25 sikî politika kalintisini da kapsar).
    mod 'cipa': delta, 2026 yil sonunu TCMB tahminine (28) cipalar: delta0 = 28 - model2026 + N(0,1), tum yillara tasinir."""
    rng = random.Random(tohum)
    pool = boot_coef(n)
    bd.REJIM = "tam"
    baz, coz, kir, ek = [], [], [], []
    for coef in pool:
        oran = rng.uniform(0.5, 0.9)
        d26 = rng.uniform(16, 20)
        if mod == "tarih":
            delta = rng.uniform(-4.0, 2.0)
        else:
            a_, b_, r_ = coef
            delta = TCMB[2026] - (a_ + b_ * d26 + r_ * 30.9) + rng.gauss(0.0, 1.0)
        y = yol(coef, oran, d26, delta)
        baz.append(y)
        # cozum: A-C + doviz borcu + dongu, 2027'den baslayan yavas rampa. Seviye farki (atalet simule icinde)
        p, q = cek_fx(rng)
        pay = {"A": q["sA"], "B": q["sB"], "C": q["sC"]}
        e = simule(p, q, pay, RAMPA["yavas"], dongu=True)["toplam"]
        coz.append({t: y[t] - (e[t - 2027] if t >= 2027 else 0.0) for t in YILLAR})
        kir.append(yol(coef, oran, d26, delta, J=rng.uniform(15, 50)))
        ek.append((coef, oran, d26))
    return baz, coz, kir, ek


def gerekli_kalinti(coef, oran, d26, hedef):
    """Resmi yol tutsun diye her yil gereken ek dezenflasyon (kalinti), onceki yil hedefte varsayilarak."""
    a, b, rho = coef
    out = {}
    onc = 30.9
    for t in sorted(hedef):
        d = d26 if t == 2026 else oran * onc
        out[t] = hedef[t] - (a + b * d + rho * onc)
        onc = hedef[t]
    return out


def f(v):
    return "{:.1f} [{:.1f}-{:.1f}]".format(statistics.median(v), yuzdelik(v, .1), yuzdelik(v, .9))


def rapor() -> str:
    baz, coz, kir, ek = kos(mod="cipa")
    baz_t, _, _, _ = kos(mod="tarih")
    L = ["OVP 2027-2029 ve TAHMIN", ""]
    L.append("RESMI YOLLAR (yil sonu TUFE %, kaynak: arama ozetleri)")
    L.append("  yil     OVP    TCMB (Ag 2026)")
    for t in YILLAR:
        L.append("  {}   {:>5.1f}   {}".format(t, OVP[t], "{:>5.1f}".format(TCMB[t]) if t in TCMB else "    -"))
    L.append("  OVP bir onceki surumde 2026 icin %{:.0f} demisti, simdi %{:.1f}: {:.1f} puan revizyon".format(OVP_ESKI_2026, OVP[2026], OVP[2026] - OVP_ESKI_2026))
    L.append("  OVP: buyume {}, merkezi yonetim acigi/GSYH {}, faiz disi denge {}, cari acik mlr$ {}".format(*[OVP_ARA[k] for k in ("buyume", "acik_gsyh", "faiz_disi", "cari_mlr")]))
    L.append("")

    L.append("MODEL TAHMINI (yil sonu TUFE %, medyan [p10-p90]). CIPA: 2026 sonunu TCMB tahminine (28) baglar, kalinti sonraki yillara tasinir")
    L.append("  yil    BAZ-CIPA                      COZUM-CIPA (A-C+doviz borcu, 2027'den)   KIRILMA-CIPA (2027 kur sicramasi)   BAZ-TARIH (kalinti U(-4,2))")
    for t in YILLAR:
        L.append("  {}   {:<28}  {:<40} {:<32} {}".format(t, f([x[t] for x in baz]), f([x[t] for x in coz]), f([x[t] for x in kir]), f([x[t] for x in baz_t])))
    L.append("")

    L.append("RESMI YOL ILE KIYAS: modelin yolu hedefi tutturur mu? P(model <= hedef)")
    L.append("  yil    OVP hedef  P(baz<=OVP)  P(cozum<=OVP)   TCMB hedef  P(baz<=TCMB)  P(cozum<=TCMB)")
    for t in YILLAR:
        pb = sum(1 for x in baz if x[t] <= OVP[t]) / len(baz)
        pc = sum(1 for x in coz if x[t] <= OVP[t]) / len(coz)
        if t in TCMB:
            tb = sum(1 for x in baz if x[t] <= TCMB[t]) / len(baz)
            tc = sum(1 for x in coz if x[t] <= TCMB[t]) / len(coz)
            tcs = "{:>5.1f}      %{:>3.0f}         %{:>3.0f}".format(TCMB[t], 100 * tb, 100 * tc)
        else:
            tcs = "    -         -            -"
        L.append("  {}   {:>5.1f}     %{:>3.0f}         %{:>3.0f}          {}".format(t, OVP[t], 100 * pb, 100 * pc, tcs))
    L.append("")

    L.append("OVP SIMULASYONU: yolun tutmasi icin her yil gereken EK dezenflasyon (kalinti, puan)")
    L.append("  tarihte gorulen kalinti: 2024 {:+.1f}, 2025 {:+.1f} (sikî politika); 2026 {:+.1f} (model-TCMB)".format(
        KALINTI_TARIH["2024"], KALINTI_TARIH["2025"], YIL2026_KALINTI))
    for ad, hedef in (("OVP", OVP), ("TCMB", TCMB)):
        gk = [gerekli_kalinti(c, o, d, hedef) for c, o, d in ek]
        L.append("  {}: ".format(ad) + "   ".join("{} {}".format(t, f([g[t] for g in gk])) for t in sorted(hedef)))
    L.append("  (negatif = hedefi tutturmak icin kur ve ataletin otesinde enflasyonu asagi ceken ek guc gerekir)")
    L.append("")

    # mali durus
    ac = OVP_ARA["acik_gsyh"]
    imp = [ac[i] - ac[i - 1] for i in range(1, 4)]
    beta_med = 0.3
    L.append("MALI DURUS (OVP): acik/GSYH {} -> yillik degisim {} puan GSYH".format(ac, ["{:+.1f}".format(x) for x in imp]))
    L.append("  C kanali beta ~{:.2f} puan/puan: 2027 mali itis {:+.2f}, 2028 {:+.2f}, 2029 {:+.2f} puan TUFE (kucuk, 2027'de dezenflasyona ters yon)".format(
        beta_med, beta_med * imp[0], beta_med * imp[1], beta_med * imp[2]))
    return "\n".join(L)


def testler():
    out = []
    # T-O1: OVP gecmis hatalari
    h = [(y, hz, g, g - hz) for y, hz, g in OVP_GECMIS]
    ort = statistics.fmean(x[3] for x in h)
    out.append(("T-O1 OVP gecmis hatasi (OVP ilk tahmin vs gerceklesen, yil sonu): " + ", ".join("{} {:.1f}->{:.1f} ({:+.1f})".format(*x) for x in h)
                + "; ortalama {:+.1f}. 2024-25 hafizadan, dogrulanmadi".format(ort), None, "BILGI: OVP gecmiste ~12 puan dusuk tahmin etti; resmi yol guvenilirlik sinirina bakilmali"))
    # T-O2: model tahmin yapisinin ornek disi sicili (gerceklik T2 ozet)
    out.append(("T-O2 tahmin cekirdeginin (TUFE~kur+onceki TUFE) ornek disi RMSE'si 28 puan, naif 19 (gerceklik.py T2). Tahmin guvenilir degil, yol yapisal gosterge", False,
                "10 gozlem, rejim kirilmalari"))
    # T-O3: 2026 anchor
    bt, _, _, _ = kos(1500, mod="tarih")
    bc, _, _, _ = kos(1500, mod="cipa")
    mt = statistics.median(x[2026] for x in bt)
    mc = statistics.median(x[2026] for x in bc)
    out.append(("T-O3 2026 yil sonu: tarihsel kalinti {:.1f}, cipali {:.1f}; TCMB 28,0, OVP 28,4, Agustos yillik gozlem 31,5. Tarihsel kalinti 2026'yi ~{:.0f} puan dusuk veriyor".format(mt, mc, 28.0 - mt),
                abs(mt - 28.0) < 3, "kalinti 2024-25'te -6, 2026'da +2: rejim degisti, tarihsel kalinti 2026 icin yanlis"))
    out.append(("T-O4 OVP kur varsayimi ve aylik kur yolu bu turda bulunamadi; kayma kurali (oran*TUFE) VARSAYIM", None, "BILGI: OVP belgesi yuklenirse kur yolu girer"))
    out.append(("T-O5 kirilma olasiligi yok: KIRILMA sutunu kosullu senaryo, tahmin degil", None, "BILGI"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (ovp)"]
    gec = say = 0
    for msg, ok, n in testler():
        if ok is None:
            L.append("  [BILGI] {}  ({})".format(msg, n))
            continue
        say += 1
        gec += bool(ok)
        L.append("  [{}] {}  ({})".format("GECTI" if ok else "KALDI", msg, n))
    L.append("  {}/{} gecti (bilgi satirlari sayilmadi)".format(gec, say))
    return "\n".join(L)


def main() -> int:
    print(rapor())
    print()
    print(test_blogu())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
