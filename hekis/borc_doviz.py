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

from hekis.enflasyon import BUTCE_FAIZI, GSYH, TICARI_STOK, TUFE_YILLIK, cek, yuzdelik, TOHUM, N
from hekis.acmaz import degerler, yol

# ---- GOZLEM (Drive Secici_Kredi_Veri_MOBIL.pdf) ---------------------------------
from hekis.nop_veri import NOP, boot_havuzu   # TCMB resmi seri (FKDFDVY), tum yillar, mlr $, pozitif = acik
REJIM = "tam"   # "tam": 2015-25 bootstrap; "son2yil": 2024-25 rejimi (c ~ 1,9-2,7)
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
    if REJIM == "tam":
        a_, c_ = rng.choice(boot_havuzu())     # DNOP = a + c*carry, resmi seri 2015-25, bootstrap
    else:
        a_, c_ = rng.uniform(-5, 5), rng.uniform(1.9, 2.7)   # 2024-25: dNOP/carry 2,70 ve 1,89
    q = {
        "a": a_,                             # carry'den bagimsiz yillik doviz borc artisi, mlr $
        "c": c_,                             # mlr $ / puan carry
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
        "taylor": rng.uniform(0.3, 1.0),     # TCMB'nin dusen enflasyona faiz indirimi tepkisi (2025: 0,41; ortodoks donem duzey 1,04)
        "tl_pay": rng.uniform(0.55, 0.75),   # ticari kredi stokunda TL payi (faiz maliyeti ayagi icin)
        "reprice": rng.uniform(0.4, 0.7),    # kamu borcunun yilda yeniden fiyatlanan payi
    }
    s = q["sA"] + q["sB"] + q["sC"]
    if s > 0.7:
        for k in ("sA", "sB", "sC"):
            q[k] *= 0.7 / s
    return p, q


def baz_akis(p, q):
    """Cozum yokken yillik net doviz borc akisi (mlr $), 5 yil. 2026 carry'den."""
    carry = max(0.0, q["faiz26"] - p["d_yil"] * 100)
    return [max(0.0, q["a"] + q["c"] * carry * q["decay"] ** t) for t in range(5)]


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


def simule(p, q, pay, rampa, dongu=True, kappa=None, taylor=None):
    """Yil yil, bir yil gecikmeli faiz-carry-doviz borcu dongusu.

    dongu=False: onceki fx_etki ile ayni sonuc (A-C dogrudan + borc yolu).
    dongu=True : enflasyon dususu e_t-1 -> politika faizi duser (taylor*e) ->
      carry azalir; kur artisi yavaslarsa carry geri artar (kappa*oran) ->
      net carry degisimi doviz borc akisini c*dcarry kadar degistirir ->
      ayrica faiz dusuk oldugu icin firma finansman maliyeti ve butce faizi azalir.
    """
    kappa = q["kappa"] if kappa is None else kappa
    taylor = q["taylor"] if taylor is None else taylor
    v = degerler(p)
    toplam_pay = sum(pay.values())
    carry26 = max(0.0, q["faiz26"] - p["d_yil"] * 100)
    e_dir = e_fx = 0.0
    kum = 0.0
    e_onceki = 0.0
    dd_onceki = 0.0   # onceki yil kur artisinda kacinilan puan
    out = {"toplam": [], "e_fx": [], "e_dir": [], "carry_fark": [], "ek_akis": [], "faiz_maliyet": [], "mali": []}
    for t in range(5):
        g = rampa[t]
        carry0 = carry26 * q["decay"] ** t
        f0 = max(0.0, q["a"] + q["c"] * carry0)
        di = taylor * e_onceki if dongu else 0.0                      # faiz indirimi, puan
        carry = max(0.0, carry0 - di + dd_onceki) if dongu else carry0
        dcarry = carry0 - carry                                       # + ise carry daraldi
        ek = q["c"] * dcarry if dongu else 0.0                        # dongu kaynakli ek kacinilan akis
        kac = f0 * toplam_pay * g + ek
        kum += kac
        gusd = GSYH_USD_2025 * (1 + q["gusd"]) ** (t + 1)
        oran = kum / gusd * 100
        dd = kappa * oran                                              # kur artisinda kacinilan puan
        a_risk = p["phi1"] * dd
        a_bs = q["rho_bs"] * (oran / 100) * p["d_yil"] / p["maliyet_tabani"] * 100
        a_gecis = -p["phi1"] * q["kappa_f"] * (kac / gusd * 100) * (1 - q["ca_uyum"])
        # dongu: faiz maliyeti ve butce ayagi
        maliyet = q["rho_bs"] * (di / 100) * TICARI_STOK * q["tl_pay"] / (GSYH * p["maliyet_tabani"]) * 100
        mali = (BUTCE_FAIZI * q["reprice"] * di / max(q["faiz26"], 1.0)) / GSYH * 100 * p["beta"]
        y_fx = a_risk + a_bs + a_gecis + maliyet + mali
        e_fx = p["atalet"] * e_fx + y_fx
        e_dir = p["atalet"] * e_dir + (v["A"] + v["B"] + v["C"]) * g
        e = e_dir + e_fx
        out["toplam"].append(e); out["e_fx"].append(e_fx); out["e_dir"].append(e_dir)
        out["carry_fark"].append(dcarry); out["ek_akis"].append(ek)
        out["faiz_maliyet"].append(maliyet); out["mali"].append(mali)
        e_onceki = e
        dd_onceki = dd
    return out


def dongu_blogu(n=None):
    s = kos()
    r = RAMPA["yavas"]
    pay = lambda q: {"A": q["sA"], "B": q["sB"], "C": q["sC"]}
    kapali = [simule(p, q, pay(q), r, dongu=False) for p, q in s]
    acik = [simule(p, q, pay(q), r, dongu=True) for p, q in s]
    L = ["DONGU: faiz - carry - doviz borcu (yil yil, bir yil gecikmeli)"]
    L.append("  yil                     " + "".join("{:>9}".format(2026 + t) for t in range(5)))
    L.append("  dongusuz enflasyon %    " + "".join("{:>9.1f}".format(TUFE_YILLIK * 100 - med([k["toplam"][t] for k in kapali])) for t in range(5)))
    L.append("  dongulu enflasyon %     " + "".join("{:>9.1f}".format(TUFE_YILLIK * 100 - med([a["toplam"][t] for a in acik])) for t in range(5)))
    L.append("  dongulu p10-p90         " + "".join("{:>9}".format("{:.0f}-{:.0f}".format(
        TUFE_YILLIK * 100 - yuzdelik([a["toplam"][t] for a in acik], .9), TUFE_YILLIK * 100 - yuzdelik([a["toplam"][t] for a in acik], .1))) for t in range(5)))
    fark = [a["toplam"][4] - k["toplam"][4] for a, k in zip(acik, kapali)]
    L.append("")
    L.append("  Dongunun 5. yil katkisi: medyan {:.2f} puan [{}], negatif olma olasiligi %{:.0f}".format(
        med(fark), aralik(fark), 100 * sum(x < 0 for x in fark) / len(fark)))
    ek = [sum(a["ek_akis"]) for a in acik]
    L.append("  Dongu kaynakli ek kacinilan doviz borcu (5 yil toplam): medyan {:.0f} mlr $ [{}]".format(med(ek), aralik(ek)))
    fm = [sum(a["faiz_maliyet"]) for a in acik]
    mm = [sum(a["mali"]) for a in acik]
    L.append("  Dongunun faiz maliyeti ayagi (5 yil toplam puan): {:.2f}, butce ayagi: {:.2f}".format(med(fm), med(mm)))
    pozitif = [a["carry_fark"][4] for a in acik]
    L.append("  5. yil carry degisimi (puan, + = daraldi): medyan {:.1f} [{}]".format(med(pozitif), aralik(pozitif)))
    L.append("")
    L.append("  Faiz tepkisi (taylor) duyarliligi, 5. yil enflasyon dususu medyan:")
    for tk in (0.0, 0.3, 0.6, 1.0):
        v = [simule(p, q, pay(q), r, dongu=True, taylor=tk)["toplam"][4] for p, q in s]
        L.append("    taylor={:<4}{:>6.2f} puan".format(tk, med(v)))
    L.append("")
    L.append("  Kappa x taylor (5. yil toplam dusus, puan):")
    L.append("    kappa\\taylor  " + "".join("{:>8}".format(tk) for tk in (0.3, 0.6, 1.0)))
    for k in (0.25, 0.5, 1.0, 1.5):
        L.append("    {:<13}".format(k) + "".join("{:>8.2f}".format(med([simule(p, q, pay(q), r, kappa=k, taylor=tk)["toplam"][4] for p, q in s[:3000]])) for tk in (0.3, 0.6, 1.0)))
    return "\n".join(L)


def testler():
    out = []
    # R1: doviz borcu artisi cari acigi asiyor mu? Asiyorsa 'acik finansmani' tek aciklama olamaz.
    for t in (2024, 2025):
        dn = NOP[t] - NOP[t - 1]
        ca = CARI_TL[t] / KUR_ORT[t]
        out.append(("R1 {}: dNOP {:.1f} mlr$ / cari acik {:.1f} mlr$ = {:.1f}x".format(t, dn, ca, dn / ca),
                    dn / ca > 1.0, "carry/arbitraj aciklamasi cari acik aciklamasindan guclu"))
    # R2: carry katsayisi resmi seride (11 yil) sifirdan ayrisiyor mu
    from hekis.nop_veri import boot_havuzu as _bh, fit as _fit, CARRY as _CARRY, DNOP as _DNOP
    cs = sorted(x[1] for x in _bh())
    c10, c90 = cs[int(.1 * len(cs))], cs[int(.9 * len(cs))]
    out.append(("R2 carry katsayisi resmi seri 2015-25: bootstrap p10-p90 {:.2f}-{:.2f} mlr$/puan (kestirim 0,75)".format(c10, c90),
                c10 > 0, "iki ucu sifirin ustundeyse carry anlamli"))
    # R3: ornek disi: 2023'e kadar fit, 2024-25 tahmin
    b23, _, _, _ = _fit(list(range(2015, 2024)))
    h = [(b23[0] + b23[1] * _CARRY[t]) - _DNOP[t] for t in (2024, 2025)]
    out.append(("R3 ornek disi: 2023'e kadar fit (a={:.1f}, c={:.2f}) ile 2024-25 dNOP tahmini {:+.1f}/{:+.1f}, gercek {:+.1f}/{:+.1f}".format(
        b23[0], b23[1], _DNOP[2024] + h[0], _DNOP[2025] + h[1], _DNOP[2024], _DNOP[2025]),
        max(abs(x) for x in h) < 25, "carry 2023'e kadar acikladiginin yanindan gecmiyor: rejim degisimi"))
    # R4: baz yorungeyi makul mu
    s = kos()
    r = RAMPA["yavas"]
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
    # R7: dongusuz hal onceki fx_etki ile ayni mi (kod butunlugu)
    fark = 0.0
    for p, q in s[:500]:
        pay = {"A": q["sA"], "B": q["sB"], "C": q["sC"]}
        a = simule(p, q, pay, r, dongu=False)["e_fx"]
        b = fx_etki(p, q, pay, r)[0]
        fark = max(fark, max(abs(x - y) for x, y in zip(a, b)))
    out.append(("R7 kod butunlugu: dongusuz simule = eski fx_etki, max fark {:.1e}".format(fark), fark < 1e-9, "regresyon testi"))
    # R8: dongu kazanci patlamiyor mu
    oran = []
    for p, q in s[:3000]:
        pay = {"A": q["sA"], "B": q["sB"], "C": q["sC"]}
        k = simule(p, q, pay, r, dongu=False)["toplam"][4]
        a = simule(p, q, pay, r, dongu=True)["toplam"][4]
        if k > 1e-6:
            oran.append(a / k)
    out.append(("R8 dongu carpani (dongulu/dongusuz, 5. yil): medyan {:.2f}, p90 {:.2f}, max {:.2f}".format(med(oran), yuzdelik(oran, .9), max(oran)),
                max(oran) < 1.5, "1'e yakin = dongu zayif, kararli"))
    # R9: faiz tepkisi veride tanimlanabilir mi (2025 gozlem 0,41)
    out.append(("R9 taylor: 10 yil faiz degisimi ~ enflasyon degisimi katsayisi -0,30 (se 0,24), rejim kirilmali; 2025 gozlemi 0,41, ortodoks duzey 1,04 (n=4). Aralik 0,3-1,0 kabul",
                False, "tam tanimlanamaz, duyarlilik tablosuna bak"))
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
    print(dongu_blogu())
    print()
    print(test_blogu())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
