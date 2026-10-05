"""Doviz, ucluk acmazin dorduncu etkisi: kademeli doviz borclulugu.

    python -m hekis.borc_doviz

Onceki D kanali (cozumde kur artisi dusuyor) dissaldi. Burada doviz ic olusur:
kira/konut (A), mahsup (B), ic borclanma (C) TL finansmani pahali ve kilitli kilar,
firma doviz borcuna kayar, net doviz acigi kademeli birikir. Enflasyona uc yoldan gecer:

  1. risk primi: birikmis stok kur baskisi yaratir        kappa
  2. bilanco: kur artisi doviz borcunun TL maliyetini sisirir, fiyata gecer
  3. gecis maliyeti: doviz borclanmasi kesilirse kisa vadeli lira destegi kaybolur

Gozlem: Drive Secici_Kredi_Veri V15, V16, V21, V22. Atif payi ve kappa VARSAYIM.
kappa veriden tanimlanamaz: elde 3 stok gozlemi var. Sonuc kappa'ya duyarlilik olarak okunmali.
"""

import random
import statistics

from hekis.enflasyon import TUFE_YILLIK, cek, yuzdelik, TOHUM, N
from hekis.acmaz import degerler, yol

# ---- GOZLEM (Drive Secici_Kredi_Veri_MOBIL.pdf) ---------------------------------
NOP = {2023: 70.0, 2024: 148.0, 2025: 188.551}   # reel kesim net doviz acik pozisyonu, mlr $ (V21)
GSYH_TL = {2023: 27091.5, 2024: 44676.0, 2025: 63240.5}  # V15
CARI_TL = {2023: 982.2, 2024: 426.7, 2025: 1192.2}       # V16 (pozitif acik)
FAIZ = {2023: 18.6, 2024: 48.7, 2025: 43.2}              # V22 politika faizi yil ort.
KUR_SON = {2022: 18.70, 2023: 29.40, 2024: 35.22, 2025: 42.88}
DEP = {2023: 57.2, 2024: 19.8, 2025: 21.7}
KUR_ORT = {t: (KUR_SON[t - 1] + KUR_SON[t]) / 2 for t in (2023, 2024, 2025)}  # yaklasik
GSYH_USD_2025 = GSYH_TL[2025] / KUR_ORT[2025]            # ~1619 mlr $

RAMPA = {"yavas": [0.25, 0.5, 0.75, 1.0, 1.0], "hizli": [0.5, 1, 1, 1, 1], "yarim": [0.5] * 5}


def cek_fx(rng):
    p = cek(rng)
    q = {
        "c": rng.uniform(1.5, 3.0),          # mlr $ / puan carry. Veri: 2024 2,70, 2025 1,89 (iki nokta)
        "faiz26": rng.uniform(30, 42),       # 2026 politika faizi, V22 2026 bos: VARSAYIM
        "decay": rng.uniform(0.60, 0.95),    # carry ve borc akisinin yillik sonmesi
        "gusd": rng.uniform(0.05, 0.09),     # GSYH dolar buyumesi
        "sA": rng.uniform(0.03, 0.15),       # doviz borc akisinin kira/konut kaynakli payi
        "sB": rng.uniform(0.10, 0.35),       # mahsup/kilit kaynakli
        "sC": rng.uniform(0.10, 0.35),       # ic borclanma/faiz kaynakli
        "kappa": rng.uniform(0.0, 1.5),      # puan kur artisi / GSYH puani kacinilan borc stoku. TANIMLANAMAZ
        "kappa_f": rng.uniform(0.2, 1.0),    # gecis: kesilen doviz akisinin kur destegi kaybi
        "ca_uyum": rng.uniform(0.3, 0.9),    # kesilen doviz finansmaninin TL ile ikamesi
        "rho_bs": rng.uniform(0.2, 0.5),     # bilanco maliyetinin fiyata gecisi
    }
    s = q["sA"] + q["sB"] + q["sC"]
    if s > 0.7:
        for k in ("sA", "sB", "sC"):
            q[k] *= 0.7 / s
    return p, q


def baz_akis(p, q):
    """Cozum yokken yillik net doviz borc akisi (mlr $), 5 yil. 2026 carry'den."""
    carry = max(0.0, q["faiz26"] - p["d_yil"] * 100)
    f = q["c"] * carry
    return [f * q["decay"] ** t for t in range(5)]


def fx_etki(p, q, pay, rampa, kappa=None):
    """pay: kanal -> atif payi. Doviz borcu uzerinden enflasyon etkisi, yil bazinda e_t (puan, pozitif=dusus)."""
    kappa = q["kappa"] if kappa is None else kappa
    f0 = baz_akis(p, q)
    toplam_pay = sum(pay.values())
    e, kum, out, mek = 0.0, 0.0, [], []
    for t in range(5):
        g = rampa[t]
        kac = f0[t] * toplam_pay * g                       # kacinilan akis, mlr $
        kum += kac
        gusd = GSYH_USD_2025 * (1 + q["gusd"]) ** (t + 1)
        oran = kum / gusd * 100                             # kacinilan stok / GSYH, puan
        a_risk = p["phi1"] * kappa * oran                  # risk primi
        d = p["d_yil"]
        a_bs = q["rho_bs"] * (oran / 100) * d / p["maliyet_tabani"] * 100   # bilanco
        a_gecis = -p["phi1"] * q["kappa_f"] * (kac / gusd * 100) * (1 - q["ca_uyum"])   # destek kaybi
        y = a_risk + a_bs + a_gecis
        e = p["atalet"] * e + y
        out.append(e)
        mek.append((a_risk, a_bs, a_gecis))
    return out, mek


def kos(n=N, tohum=TOHUM):
    rng = random.Random(tohum)
    return [cek_fx(rng) for _ in range(n)]


def med(x):
    return statistics.median(x)


def aralik(x):
    return "{:.1f}-{:.1f}".format(yuzdelik(x, .1), yuzdelik(x, .9))


def veri_blogu():
    L = ["VERI: reel kesim doviz borcu (Drive)"]
    L.append("  yil  NOP mlr$  NOP/GSYH$  cari$   dNOP   carry(faiz-kur)")
    for t in (2023, 2024, 2025):
        g = GSYH_TL[t] / KUR_ORT[t]
        dn = NOP[t] - NOP[t - 1] if t - 1 in NOP else None
        L.append("  {}  {:>8.0f}  {:>8.1f}%  {:>6.1f}  {:>6}  {:>+7.1f}".format(
            t, NOP[t], NOP[t] / g * 100, CARI_TL[t] / KUR_ORT[t], "-" if dn is None else "%.1f" % dn, FAIZ[t] - DEP[t]))
    return L


def rapor() -> str:
    s = kos()
    L = veri_blogu()
    L.append("")
    # baz: doviz borcu birikimi
    nop_baz = [[NOP[2025] + sum(baz_akis(p, q)[: t + 1]) for t in range(5)] for p, q in s]
    gusd = [GSYH_USD_2025 * (1 + 0.07) ** (t + 1) for t in range(5)]
    L.append("BAZ: cozum yoksa doviz borcu (medyan, mlr $ ve GSYH payi, GSYH buyumesi %7 yaklasik)")
    L.append("  yil        " + "".join("{:>9}".format(2026 + t) for t in range(5)))
    L.append("  NOP        " + "".join("{:>9.0f}".format(med([n[t] for n in nop_baz])) for t in range(5)))
    L.append("  NOP/GSYH%  " + "".join("{:>9.1f}".format(med([n[t] for n in nop_baz]) / gusd[t] * 100) for t in range(5)))
    L.append("")

    r = RAMPA["yavas"]
    tum = {"A": None, "B": None, "C": None}
    tam, fxk, dire = [], [], []
    for p, q in s:
        v = degerler(p)
        direct = yol(v["A"] + v["B"] + v["C"], p["atalet"], r)
        pay = {"A": q["sA"], "B": q["sB"], "C": q["sC"]}
        fx, _ = fx_etki(p, q, pay, r)
        dire.append(direct)
        fxk.append(fx)
        tam.append([a + b for a, b in zip(direct, fx)])
    L.append("COZUM, yavas rampa: enflasyon yolu %, baz %{:.1f}".format(TUFE_YILLIK * 100))
    L.append("  yil        " + "".join("{:>9}".format(2026 + t) for t in range(5)))
    L.append("  medyan     " + "".join("{:>9.1f}".format(TUFE_YILLIK * 100 - med([x[t] for x in tam])) for t in range(5)))
    L.append("  p10-p90    " + "".join("{:>9}".format("{:.0f}-{:.0f}".format(
        TUFE_YILLIK * 100 - yuzdelik([x[t] for x in tam], .9), TUFE_YILLIK * 100 - yuzdelik([x[t] for x in tam], .1))) for t in range(5)))
    L.append("")
    L.append("5. YIL AYRISTIRMA (puan dusus, medyan [p10-p90]):")
    L.append("  dogrudan (A+B+C)             {:>5.2f}  [{}]".format(med([x[4] for x in dire]), aralik([x[4] for x in dire])))
    L.append("  doviz borcu uzerinden        {:>5.2f}  [{}]".format(med([x[4] for x in fxk]), aralik([x[4] for x in fxk])))
    for ad in ("A", "B", "C"):
        sol = []
        for p, q in s:
            fx, _ = fx_etki(p, q, {ad: q["s" + ad]}, r)
            sol.append(fx[4])
        L.append("     yalniz {} kaynakli         {:>5.2f}  [{}]".format(ad, med(sol), aralik(sol)))
    L.append("")
    L.append("Doviz borcu etkisi, mekanizma (5. yil, tek yil katki, atalet oncesi, medyan):")
    for i, ad in enumerate(("risk primi", "bilanco", "gecis maliyeti")):
        v = [fx_etki(p, q, {"A": q["sA"], "B": q["sB"], "C": q["sC"]}, r)[1][4][i] for p, q in s]
        L.append("  {:<16}{:>7.2f}".format(ad, med(v)))
    gec = [fx_etki(p, q, {"A": q["sA"], "B": q["sB"], "C": q["sC"]}, r)[0][0] for p, q in s]
    L.append("  Yil 1 doviz katkisi medyan {:.2f}, negatif olma olasiligi %{:.0f} (gecis maliyeti)".format(
        med(gec), 100 * sum(x < 0 for x in gec) / len(gec)))
    L.append("")
    L.append("kappa DUYARLILIGI (5. yil, doviz borcu etkisi, medyan puan). Veri kappa'yi tanimlamaz:")
    for k in (0.0, 0.25, 0.5, 1.0, 1.5):
        v = [fx_etki(p, q, {"A": q["sA"], "B": q["sB"], "C": q["sC"]}, r, kappa=k)[0][4] for p, q in s]
        L.append("  kappa={:<5}{:>7.2f}".format(k, med(v)))
    return "\n".join(L)


def testler():
    out = []
    # R1: doviz borcu artisi cari acigi asiyor mu? Asiyorsa 'acik finansmani' tek aciklama olamaz.
    for t in (2024, 2025):
        dn = NOP[t] - NOP[t - 1]
        ca = CARI_TL[t] / KUR_ORT[t]
        out.append(("R1 {}: dNOP {:.1f} mlr$ / cari acik {:.1f} mlr$ = {:.1f}x".format(t, dn, ca, dn / ca),
                    dn / ca > 1.0, "carry/arbitraj aciklamasi cari acik aciklamasindan guclu"))
    # R2: carry ile dNOP sirasi. Iki nokta, test degil.
    c24 = (NOP[2024] - NOP[2023]) / (FAIZ[2024] - DEP[2024])
    c25 = (NOP[2025] - NOP[2024]) / (FAIZ[2025] - DEP[2025])
    out.append(("R2 carry katsayisi: 2024 {:.2f}, 2025 {:.2f} mlr$/puan (fark %{:.0f})".format(c24, c25, 100 * (c24 - c25) / c24),
                abs(c24 - c25) / c24 < 0.5, "iki nokta, tanimlayici ama test degil"))
    # R3: 2024 katsayisiyla 2025'i tahmin et
    tah = c24 * (FAIZ[2025] - DEP[2025])
    err = tah - (NOP[2025] - NOP[2024])
    out.append(("R3 ornek disi: 2024 katsayisiyla 2025 dNOP tahmini {:.1f}, gercek {:.1f}, hata {:+.1f}".format(tah, NOP[2025] - NOP[2024], err),
                abs(err) / (NOP[2025] - NOP[2024]) < 0.25, "hata %{:.0f}".format(100 * abs(err) / (NOP[2025] - NOP[2024]))))
    # R4: baz yorungeyi makul mu
    s = kos()
    asiri = sum(1 for p, q in s if NOP[2025] + sum(baz_akis(p, q)) > 0.15 * GSYH_USD_2025 * (1 + q["gusd"]) ** 5) / len(s)
    out.append(("R4 baz: 2030'da NOP/GSYH > %15 olma olasiligi %{:.0f}".format(100 * asiri), asiri < 0.5, "kademeli artis varsayimi decay'e bagli"))
    # R5: kappa tanimlanabilir mi
    out.append(("R5 kappa: 3 stok gozlemi (2 degisim), kur artisi ayni anda dustu (57->20). Tanimlanamaz", False, "veri kappa'yi disarida birakir"))
    # R6: onceki dissal D ile tutarlilik, gerekli kappa
    r = RAMPA["yavas"]
    sl = []
    for p, q in s[:3000]:
        v = fx_etki(p, q, {"A": q["sA"], "B": q["sB"], "C": q["sC"]}, r, kappa=1.0)[0][4]
        sl.append(v)
    egim = med(sl)   # kappa=1 icin medyan etki (yaklasik dogrusal, kucuk bilanco terimi var)
    out.append(("R6 dissal D (yil 5 ~10 puan) tutarli olsaydi kappa ~{:.0f}: 1 puan GSYH kacinilan doviz borcu {:.0f} puan kur artisini kaldirmali".format(10 / egim, 10 / egim * 1.0),
                10 / egim <= 2.0, "makul aralik disinda, dissal D'yi reddeder"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (doviz borcu)"]
    gec = 0
    for msg, ok, not_ in testler():
        gec += bool(ok)
        L.append("  [{}] {}  ({})".format("GECTI" if ok else "KALDI", msg, not_))
    L.append("  {}/{} gecti".format(gec, len(testler())))
    return "\n".join(L)


def main() -> int:
    print(rapor())
    print()
    print(test_blogu())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
