"""Atalet gercek mi? Uc soru.

    python -m hekis.atalet

1. ISTATISTIKSEL: kalicilik rastgele mi (permutasyon), olcuye ve yonteme bagli mi?
2. GOLGE: 'atalet' aslinda gecmis kur soklarinin (gecikmeli geciskenlik) golgesi mi? Gecikmeli kur eklenince rho ne olur?
3. MEKANIZMA: olculebilen endeksleme kanallari (kira sozlesmesi) ataletin ne kadarini aciklar?

Cekirdek: hekis/kalibre.py (TUFE_t = a + b*kur_t [+ b1*kur_t-1] + rho*TUFE_t-1, 2015-25, n<=10).
"""

import random

from hekis.kalibre import KUR, TUFE, ols

D = {t: (KUR[t] / KUR[t - 1] - 1) * 100 for t in range(2015, 2026)}
YS = list(range(2016, 2026))


def model2(ys=YS):
    return ols([[1, D[t], TUFE[t - 1]] for t in ys], [TUFE[t] for t in ys])


def model3(ys=YS[1:]):
    return ols([[1, D[t], D[t - 1], TUFE[t - 1]] for t in ys], [TUFE[t] for t in ys])


def permutasyon(n=4000, tohum=3):
    b0 = model2()[0][2]
    rng = random.Random(tohum)
    say = 0
    for _ in range(n):
        lag = [TUFE[t - 1] for t in YS]
        rng.shuffle(lag)
        b, _, _, _ = ols([[1, D[t], lag[i]] for i, t in enumerate(YS)], [TUFE[t] for t in YS])
        if b[2] >= b0:
            say += 1
    return say / n


def rapor() -> str:
    L = ["ATALET GERCEK MI?", ""]
    b, se, r2, _ = model2()
    L.append("1. ISTATISTIKSEL")
    L.append("  TUFE_t = a + b*kur_t + rho*TUFE_t-1 (n=10): rho={:.2f} (se {:.2f}), R2={:.2f}".format(b[2], se[2], r2))
    L.append("  Permutasyon: onceki yil TUFE'si yillar arasinda karistirilirsa rho>={:.2f} olasiligi %{:.1f}".format(b[2], 100 * permutasyon()))
    try:
        import numpy as np
        import statsmodels.api as sm
        X = np.array([[1, D[t], TUFE[t - 1]] for t in YS], float)
        y = np.array([TUFE[t] for t in YS], float)
        h = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 1})
        L.append("  Newey-West(1) se(rho)={:.2f} (elle {:.2f}). DIKKAT: n=10'da HAC hata payini kucuk gosterir, guvenme; permutasyon p degeri daha guvenilir".format(h.bse[2], se[2]))
    except ImportError:
        pass
    from hekis.ito import UGE
    L.append("  Olcu bagimsizligi: bir yillik kalicilik TUIK 0,69-0,70, ITO tuketici 0,73-0,74, ENAG 0,67; aylik ITO 'yillik-yillik' rho 0,45 (se 0,19), aylik degisim phi 0,38 (se 0,14)")
    L.append("  Yani kalicilik istatistiksel olarak VAR ve olcuye bagli degil. Buyuklugu 0,4-0,7 araliginda.")
    L.append("")

    b3, se3, r23, _ = model3()
    L.append("2. GOLGE TESTI: gecikmeli kur eklenince (omitted persistent shock)")
    L.append("  TUFE_t = a + b0*kur_t + b1*kur_t-1 + rho*TUFE_t-1 (n=9): b0={:.2f} (se {:.2f}), b1={:.2f} (se {:.2f}), rho={:.2f} (se {:.2f}), R2={:.2f}".format(
        b3[1], se3[1], b3[2], se3[2], b3[3], se3[3], r23))
    L.append("  rho 0,68 -> {:.2f}: ataletin ~%{:.0f}'i gecmis kur soklarinin golgesiymis.".format(b3[3], 100 * (b[2] - b3[3]) / b[2]))
    pi_prev = TUFE[2025]
    d26, d25 = 17.5, D[2025]
    kur_a, kur_b, ata = b3[1] * d26, b3[2] * d25, b3[3] * pi_prev
    top = b3[0] + kur_a + kur_b + ata
    L.append("  2026 ayristirmasi (gecikmeli kurla): sabit {:.1f} + kur bu yil {:.1f} + kur gecen yil {:.1f} + atalet {:.1f} = {:.1f}".format(b3[0], kur_a, kur_b, ata, top))
    poz = (kur_a + kur_b) + ata
    L.append("  Pozitif parcalar icinde: kur (bu yil + gecen yil) {:.1f} puan (%{:.0f}), SAF atalet {:.1f} puan (%{:.0f}). Sabit terim {:.1f} (negatif) payi dusurur.".format(
        kur_a + kur_b, 100 * (kur_a + kur_b) / poz, ata, 100 * ata / poz, b3[0]))
    L.append("  Bu 3 terimli modelin 2026 tahmini {:.1f}, TCMB 28: kalinti {:+.1f}. Iki terimli modelde atalet %75 / kur %27 idi. AYRIM SPESIFIKASYONA BAGLI.".format(top, 28 - top))
    # leave-one-out rho
    ys = YS[1:]
    lo = []
    for out in ys:
        k = [t for t in ys if t != out]
        bb, _, _, _ = ols([[1, D[t], D[t - 1], TUFE[t - 1]] for t in k], [TUFE[t] for t in k])
        lo.append(bb[3])
    L.append("  Bir yili disarida birakinca saf rho {:.2f}-{:.2f}".format(min(lo), max(lo)))
    L.append("")

    L.append("3. MEKANIZMA: olculebilen endeksleme ne kadarini aciklar")
    L.append("  Kira sozlesmesi (TBK: artis 12 aylik ortalama TUFE ile sinirli, dogrulandi; YKKE-ITO gecikme sinamasi): TUFE'ye 2026 ~1,2-1,6 puan, 2027 ~0,6-1,2")
    L.append("  Saf atalet {:.0f} puan: olculebilen kira kanali bunun ~%{:.0f}'i. Gerisi (ucret, beklenti, yonetilen fiyat, hizmet) OLCULMEDI.".format(ata, 100 * 1.4 / ata))
    L.append("  Elimde olmayan: asgari ucret/ucret serisi, TCMB beklenti anketi, yonetilen fiyat sepeti.")
    return "\n".join(L)


def testler():
    out = []
    p = permutasyon(2000)
    out.append(("T-AT1 permutasyon p={:.3f}: kalicilik rastgele degil".format(p), p < 0.05, "10 gozlem, tek sinama"))
    b3, se3, _, _ = model3()
    out.append(("T-AT2 gecikmeli kur eklenince rho {:.2f} (se {:.2f}) hala sifirdan ayrisiyor mu".format(b3[3], se3[3]), b3[3] / se3[3] > 2.0, "t={:.1f}: sinirda".format(b3[3] / se3[3])))
    b, _, _, _ = model2()
    out.append(("T-AT3 rho kur kontroluyle {:.2f} -> {:.2f}: ataletin yarisi kur golgesi degil".format(b[2], b3[3]), (b[2] - b3[3]) / b[2] < 0.5, "azalma {:.0f}%".format(100 * (b[2] - b3[3]) / b[2])))
    out.append(("T-AT4 olculebilen endeksleme (kira) saf ataletin ~%7'i: mekanizma buyuk olcude kanitsiz", None, "BILGI: ucret ve beklenti verisi gerek"))
    out.append(("T-AT5 ornek disi tahmin zayif (gerceklik.py T2): rho dogru ama stabil degil", None, "BILGI"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (atalet)"]
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
