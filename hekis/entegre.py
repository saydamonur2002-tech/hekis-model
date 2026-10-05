"""Entegre uclu model: (1) atalet sifirlama, (2) uclu acmaz cozumu, (3) doviz akisini normallestirme.

    python -m hekis.entegre

Sira (kullanici): once parasal sifirlama (R), sonra uclu yapi (A), en son doviz akisi normalizasyonu (F).
Cekirdek: ovp.py indirgenmis formu  pi_t = a + b*kur_t + rho_t*pi_{t-1} + delta,  kur_t = oran_t*pi_{t-1},
delta 2026'yi TCMB tahminine (28) cipalar. 2027-2031, bes yil.

R: rho 2027'den itibaren rl'ye (U 0,10-0,35) iner. Parasal sifirlama = endeksleme/beklenti capasi ile atalet kirilir.
   Veride karsiligi YOK (Lucas elestirisi): senaryo varsayimi. 'yari' hassasiyet: rho yarim iner. Acmaz kazancinin kalicilik
   katsayisi da rl'ye iner (kazanc daha cabuk sonuyor: R ile A birbirinin yerine gecer).
A: kira + mahsup + ic borc dogrudan etki + doviz borcu kanali + faiz-carry dongusu (borc_doviz.simule), yavas rampa.
F: doviz akis normallesmesi: kontrolsuz dis borc birikimi kesilir. (i) kacinilan doviz akisi (carry kaynakli dahil) simule'in
   doviz borcu kanalina girer; (ii) kur cipasi cozulur: kur kaymasi/enflasyon orani (0,5-0,9) 1'e yaklasir = reel degerlenmenin geri
   alinmasi, KISA VADELI ENFLASYONIST (b*dkur); (iii) kirilma olasiligi azalir (beklenen maliyet kanali, olasiliklar VARSAYIM).
Cikti: bes yillik yollar, 8 alt kume, sirali ve Shapley katkilari, etkilesim (sinerji/yerine gecme), kirilma riski ayarli beklenen yol.
Bu bir TAHMIN degil, katki ve etkilesim hesabidir. Kirilma olasiligi (pb) bilinmiyor: hassasiyet olarak gosterilir.
"""

import itertools
import random
import statistics

import hekis.borc_doviz as bd
from hekis.borc_doviz import RAMPA, cek_fx, simule
from hekis.enflasyon import TOHUM, yuzdelik
from hekis.ovp import OVP, TCMB, boot_coef

YILLAR = (2027, 2028, 2029, 2030, 2031)
R5 = RAMPA["yavas"]
PHI_F_BIR = (0.5, 1.0)        # F'in kacindigi akis payi (kalan akis uzerinden), U
OT_F = [0.4, 0.8, 1.0, 1.0, 1.0]   # kur kaymasi/enflasyon oraninin 1'e yaklasma rampasi (F acik)
PB_AZ = {"A": 0.3, "F": 0.8}       # kirilma olasiligini azaltma payi (VARSAYIM)


def cekim(rng, coef):
    p, q = cek_fx(rng)
    return {
        "coef": coef, "p": p, "q": q,
        "oran": rng.uniform(0.5, 0.9), "d26": rng.uniform(16, 20),
        "rl": rng.uniform(0.10, 0.35), "phiF": rng.uniform(*PHI_F_BIR),
        "J": rng.uniform(15, 50), "gauss": rng.gauss(0.0, 1.0),
    }


def yol(c, R, A, F, kirilma=False, siddet=1.0):
    """Yil sonu TUFE %, 2027-2031. siddet: R'nin rho dususu payi (1 tam, 0,5 yari)."""
    a, b, rho = c["coef"]
    p, q = dict(c["p"]), c["q"]
    delta = 28.0 - (a + b * c["d26"] + rho * 30.9) + c["gauss"]
    rl = rho + (c["rl"] - rho) * siddet if R else rho
    # kazanc yolu (seviye dususu, puan)
    e = [0.0] * 5
    if A or F:
        p2 = dict(p)
        if R:
            p2["atalet"] = c["rl"] if siddet >= 1 else (p["atalet"] + c["rl"]) / 2
        sa = (q["sA"] + q["sB"] + q["sC"]) if A else 0.0
        pay = sa + c["phiF"] * (1 - sa) if F else sa
        s = simule(p2, q, {"x": pay}, R5, dongu=True)
        e = [(s["e_dir"][t] if A else 0.0) + s["e_fx"][t] for t in range(5)]
    pi = 28.0
    out = []
    for t in range(5):
        o = c["oran"] + (1 - c["oran"]) * OT_F[t] if F else c["oran"]
        d = o * pi
        if kirilma and t == 0:
            d += c["J"]
        pi_ham = max(3.0, a + b * d + rl * pi + delta)
        # kazanc, ham yoldan degil seviyeden dusulur (kalicilik simule icinde); ham yol e'siz ilerler
        out.append(max(3.0, pi_ham - e[t]))
        pi = pi_ham
    return out


def kos(n=3000, tohum=TOHUM, siddet=1.0):
    rng = random.Random(tohum)
    pool = boot_coef(n)
    bd.REJIM = "tam"
    S = {}
    kum = {}
    for coef in pool:
        c = cekim(rng, coef)
        for R, A, F in itertools.product((0, 1), repeat=3):
            S.setdefault((R, A, F), []).append(yol(c, R, A, F, False, siddet))
            kum.setdefault((R, A, F), []).append(yol(c, R, A, F, True, siddet))
        c["_"] = None
    return S, kum, pool


def med(v, t):
    return statistics.median(x[t] for x in v)


def beklenen(S, K, pb0, anahtar):
    R, A, F = anahtar
    pb = pb0 * (1 - (PB_AZ["A"] if A else 0)) * (1 - (PB_AZ["F"] if F else 0))
    return [statistics.median((1 - pb) * s[t] + pb * k[t] for s, k in zip(S[anahtar], K[anahtar])) for t in range(5)], pb


def shapley(S, t):
    """Her sirada R,A,F eklenmesinin marjinal dususu, 6 sira ortalamasi (medyan yol uzerinden)."""
    m = {k: med(v, t) for k, v in S.items()}
    out = {"R": 0.0, "A": 0.0, "F": 0.0}
    sirs = list(itertools.permutations("RAF"))
    for sr in sirs:
        cur = {"R": 0, "A": 0, "F": 0}
        for x in sr:
            onc = m[(cur["R"], cur["A"], cur["F"])]
            cur[x] = 1
            yeni = m[(cur["R"], cur["A"], cur["F"])]
            out[x] += (onc - yeni) / len(sirs)
    return out


def f(v):
    return "{:.1f}".format(v)


def rapor() -> str:
    S, K, _ = kos()
    L = ["ENTEGRE UCLU MODEL: R sifirlama + A uclu acmaz + F doviz akisi normalizasyonu", ""]
    L.append("Yil sonu TUFE %, medyan (kirilma YOK). Baz: 2026 = 28 (TCMB), cipali.   OVP: 2027 {:.0f}, 2028 {:.1f}, 2029 {:.0f};  TCMB 2027 {:.0f}, 2028 {:.0f}".format(OVP[2027], OVP[2028], OVP[2029], TCMB[2027], TCMB[2028]))
    L.append("  kurulum           " + "".join("{:>8}".format(y) for y in YILLAR))
    ad = {(0, 0, 0): "baz (hicbiri)", (1, 0, 0): "R", (0, 1, 0): "A", (0, 0, 1): "F", (1, 1, 0): "R+A", (1, 0, 1): "R+F", (0, 1, 1): "A+F", (1, 1, 1): "R+A+F (hepsi)"}
    for k in sorted(ad, key=lambda z: sum(z)):
        L.append("  {:<18}".format(ad[k]) + "".join("{:>8.1f}".format(med(S[k], t)) for t in range(5)))
    L.append("")
    L.append("SIRALI KATKI (kullanici sirasi R -> A -> F), 2029 ve 2031'de puan dusus:")
    for t, y in ((2, 2029), (4, 2031)):
        b0, b1, b2, b3 = (med(S[k], t) for k in ((0, 0, 0), (1, 0, 0), (1, 1, 0), (1, 1, 1)))
        L.append("  {}: baz {} ; +R {:+.1f} ; +A {:+.1f} ; +F {:+.1f} ;  toplam {:+.1f} -> {}".format(y, f(b0), b1 - b0, b2 - b1, b3 - b2, b3 - b0, f(b3)))
    L.append("")
    L.append("SHAPLEY (6 siranin ortalamasi, puan dusus; negatif = enflasyonist):")
    for t, y in ((0, 2027), (2, 2029), (4, 2031)):
        sh = shapley(S, t)
        top = sum(sh.values())
        L.append("  {}: R {:+.1f}  A {:+.1f}  F {:+.1f}  toplam {:+.1f}".format(y, sh["R"], sh["A"], sh["F"], top))
    L.append("")
    L.append("ETKILESIM (2029): hepsi - (R tek + A tek + F tek), puan. Negatif = birbirinin yerine gecer (cift sayim yok), pozitif = sinerji")
    b0 = med(S[(0, 0, 0)], 2)
    tek = sum(b0 - med(S[k], 2) for k in ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
    hep = b0 - med(S[(1, 1, 1)], 2)
    L.append("  tek tek toplam {:+.1f}, birlikte {:+.1f}, etkilesim {:+.1f}".format(tek, hep, hep - tek))
    L.append("")
    L.append("KIRILMA RISKI AYARLI (beklenen yol, 2029). pb0 = kirilma olasiligi (BILINMIYOR); A acik pb x0,7, F acik pb x0,2 (VARSAYIM)")
    for pb0 in (0.0, 0.15, 0.30):
        r = []
        for k in ((0, 0, 0), (1, 0, 0), (1, 1, 0), (1, 1, 1), (0, 0, 1)):
            e, pb = beklenen(S, K, pb0, k)
            r.append("{} {:.1f}".format(ad[k].split()[0], e[2]))
        L.append("  pb0=%{:.0f}:  ".format(100 * pb0) + "   ".join(r))
    L.append("  kirilma GERCEKLESIRSE 2029 medyan: " + "   ".join("{} {:.1f}".format(ad[k].split()[0], med(K[k], 2)) for k in ((0, 0, 0), (1, 0, 0), (1, 1, 0), (1, 1, 1), (0, 0, 1))))
    tb = sum(1 for x in S[(1, 1, 1)] if x[2] <= 3.0001) / len(S[(1, 1, 1)])
    L.append("  UYARI: R acikken yollarin %{:.0f}'i 2029'da %3 tabanina dokundu (taban yapay); R'nin buyuklugu rho dususu varsayiminin aritmetigi.".format(100 * tb))
    L.append("  UYARI: F tek basina kur kaymasi/enflasyon orani 1'e giderken b+rho > 1 oldugundan indirgenmis formda enflasyon KENDINI BESLER (cipa tek nominal capa).")
    L.append("")
    # yari R
    Sy, _, _ = kos(n=1500, siddet=0.5)
    L.append("R YARI BASARILI (rho yarim iner), 2029: baz {} ; hepsi {} (tam R'de {})".format(
        f(med(Sy[(0, 0, 0)], 2)), f(med(Sy[(1, 1, 1)], 2)), f(med(S[(1, 1, 1)], 2))))
    F2029 = med(S[(0, 0, 1)], 2) - med(S[(0, 0, 0)], 2)
    L.append("F tek basina 2029'da baza gore {:+.1f} puan (pozitif = enflasyonist: reel degerlenme geri alinir, borc kanali kazanci bunu karsilamaz)".format(F2029))
    return "\n".join(L)


def testler():
    out = []
    S, K, _ = kos(1500)
    b = med(S[(0, 0, 0)], 2)
    r = b - med(S[(1, 0, 0)], 2)
    a = b - med(S[(0, 1, 0)], 2)
    fz = b - med(S[(0, 0, 1)], 2)
    h = b - med(S[(1, 1, 1)], 2)
    out.append(("T-E1 R tek {:+.1f}, A tek {:+.1f}, F tek {:+.1f}, hepsi {:+.1f} (2029 puan dusus)".format(r, a, fz, h), None, "BILGI: R rho varsayimi, F kirilma olasiligi varsayimi"))
    out.append(("T-E2 R, A'dan buyuk ({:.1f} vs {:.1f}): sifirlama varsayimi sonucu belirliyor".format(r, a), None, "BILGI: R rho dususunun aritmetigi, kanit degil"))
    out.append(("T-E3 F tek basina enflasyonist ({:+.1f}): kisa vadede reel degerlenmeyi geri alir".format(fz), None, "BILGI: b+rho>1 iken kur cipasiz enflasyon kendini besler"))
    out.append(("T-E4 hepsi 2029'da {:.1f}; OVP {:.0f}".format(med(S[(1, 1, 1)], 2), OVP[2029]), None, "BILGI: OVP ile karsilastirma, R varsayimina bagli"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (entegre)"]
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
