"""Kamu zamlari ve PKA beklenti zaman serisi: atalet hangi kanaldan tasiniyor?

    python -m hekis.kamu

Veri: data/kamu_zamlari.json (arama ozeti, guven bayrakli), data/pka_zaman_serisi.json (EVDS PKA, 2014-04..2026-09),
data/asgari_ucret.json. Gerceklesme: kalibre.TUFE (yil sonu), TUIK Haz 2026 yillik 32,11.
Sorular: (1) emekli artisi mekanik geriye endeksleme mi? (2) beklenti gerceklesmenin NEDENI mi SONUCU mu
(Ocak yil-sonu beklentisi, onceki yil gerceklesmesi, gerceklesme)? (3) beklenti capalandi mi (24 ay vs %5 hedef)?
n=12 yil: her sonuc YON gostergesi, istatistiksel kanit degil.
"""

import json
import os
import statistics

from hekis.kalibre import TUFE, ols
from hekis.ucret import BRUT, onceki

_D = os.path.join(os.path.dirname(__file__), "..", "data")
K = json.load(open(os.path.join(_D, "kamu_zamlari.json")))
PKA = json.load(open(os.path.join(_D, "pka_zaman_serisi.json")))["veri"]
TYA = json.load(open(os.path.join(_D, "tufe_yillik_aylik.json")))["veri"]   # EVDS TP.TUKFIY2025.GENEL_3, yillik % degisim, aylik
EMEKLI = {t: v for t, v, g in K["emekli_ssk_bagkur"]}
HEDEF_UZUN = 5.0


def corr(x, y):
    mx, my = statistics.mean(x), statistics.mean(y)
    sx = sum((a - mx) ** 2 for a in x) ** .5
    sy = sum((b - my) ** 2 for b in y) ** .5
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def ocak_bek(y, alan="yilsonu"):
    """Y yilinin Ocak ayinda yil sonu enflasyon beklentisi."""
    return PKA["%d-01" % y].get(alan)


def aralik_bek12(y):
    """Y-1 Aralik'ta 12 ay sonrasi (= Y yil sonu) beklenti."""
    return PKA["%d-12" % (y - 1)].get("ay12")


def _ay(k, n):
    t = int(k[:4]) * 12 + int(k[5:]) - 1 + n
    return "%d-%02d" % (t // 12, t % 12 + 1)


def _inv(a):
    n = len(a)
    m = [a[i][:] + [1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for i in range(n):
        p = max(range(i, n), key=lambda k: abs(m[k][i]))
        m[i], m[p] = m[p], m[i]
        pv = m[i][i]
        m[i] = [x / pv for x in m[i]]
        for k in range(n):
            if k != i:
                f = m[k][i]
                m[k] = [x - f * y for x, y in zip(m[k], m[i])]
    return [r[n:] for r in m]


def hac(X, y, L):
    """OLS + Newey-West (Bartlett) se. Ust uste binen 12 aylik ufuklar icin klasik se yanlis (~3x kucuk)."""
    b = ols(X, y)[0]
    n, k = len(X), len(X[0])
    e = [v - sum(bi * xi for bi, xi in zip(b, r)) for r, v in zip(X, y)]
    S = [[0.0] * k for _ in range(k)]
    for l in range(L + 1):
        w = 1.0 if l == 0 else 1 - l / (L + 1.0)
        for t in range(l, n):
            for i in range(k):
                for j in range(k):
                    v = X[t][i] * X[t - l][j] * e[t] * e[t - l] * w
                    S[i][j] += v
                    if l > 0:
                        S[j][i] += v
    xi = _inv([[sum(r[i] * r[j] for r in X) for j in range(k)] for i in range(k)])
    V = [[sum(xi[i][a] * S[a][c] * xi[c][j] for a in range(k) for c in range(k)) for j in range(k)] for i in range(k)]
    yb = sum(y) / n
    r2 = 1 - sum(v * v for v in e) / sum((v - yb) ** 2 for v in y)
    return b, [V[i][i] ** .5 for i in range(k)], r2


def aylik(h, alan):
    """(ay, beklenti_t, pi_t, gerceklesen_pi_{t+h})"""
    out = []
    for k, d in sorted(PKA.items()):
        if alan in d and k in TYA and _ay(k, h) in TYA:
            out.append((k, d[alan], TYA[k], TYA[_ay(k, h)]))
    return out


def aylik_rapor(h, alan):
    X = aylik(h, alan)
    E = [x[1] for x in X]; pi = [x[2] for x in X]; R = [x[3] for x in X]
    n = len(X)
    err = [r - e for r, e in zip(R, E)]
    nv = [r - p for r, p in zip(R, pi)]
    rm = lambda v: (sum(a * a for a in v) / len(v)) ** .5
    L = ["  ufuk {} ay ({}), n={} ({}..{}), ust uste binen: Newey-West se (gecikme {})".format(h, alan, n, X[0][0], X[-1][0], h)]
    L.append("    ort. hata (gerc-bek) {:+.1f}; MAE beklenti {:.1f} vs saf (bugunku yillik TUFE) {:.1f}; RMSE {:.1f} vs {:.1f}".format(
        statistics.mean(err), statistics.mean(abs(a) for a in err), statistics.mean(abs(a) for a in nv), rm(err), rm(nv)))
    for ad, cols in (("gerc = a + b*bek", [[1, e] for e in E]), ("gerc = a + b*bek + c*bugun", [[1, e, p] for e, p in zip(E, pi)])):
        b, se, r2 = hac(cols, R, h)
        L.append("    {:<28} ".format(ad) + "  ".join("{:.2f}({:.2f})".format(x, s) for x, s in zip(b, se)) + "  R2 {:.2f}".format(r2))
    b, se, r2 = hac([[1, p] for p in pi], E, h)
    L.append("    bek = a + d*bugun             d={:.2f}({:.2f})  R2 {:.2f}  (beklenti bugunku enflasyonun fonksiyonu)".format(b[1], se[1], r2))
    for a, z in (("2014", "2020"), ("2021", "2023"), ("2024", "2026")):
        idx = [i for i, x in enumerate(X) if a <= x[0][:4] <= z]
        if idx:
            L.append("    alt donem {}-{}: n={} ort. hata {:+.1f}, MAE beklenti {:.1f} vs saf {:.1f}".format(
                a, z, len(idx), statistics.mean(err[i] for i in idx), statistics.mean(abs(err[i]) for i in idx), statistics.mean(abs(nv[i]) for i in idx)))
    return L, (err, nv, E, pi, R)


def rapor() -> str:
    L = ["KAMU ZAMLARI VE BEKLENTI ZAMAN SERISI", ""]
    L.append("1. EMEKLI = MEKANIK GERIYE ENDEKSLEME (yasal): bir takvim yilindaki iki artisin bilesigi = Haziran yillik TUFE")
    for y, hz in ((2025, 35.05), (2026, 32.11)):
        c = ((1 + EMEKLI["%d-01" % y] / 100) * (1 + EMEKLI["%d-07" % y] / 100) - 1) * 100
        L.append("  {}: artislar {:.2f} ve {:.2f} -> bilesik {:.1f}; Haz {} yillik TUFE {:.2f} {}".format(
            y, EMEKLI["%d-01" % y], EMEKLI["%d-07" % y], c, y, hz, "(2025: arama ozeti, TUIK aktarimi)" if y == 2025 else "(TUIK)"))
    L.append("  Bu bir mekanizma gozlemi: emekli geliri (~yuzde 10+ nufus, yuksek tuketim payi) gecmis enflasyona YASAYLA bagli. 2024 Oca artisi 49,25: mekanik degerin ustunde olabilir (dusuk guven).")
    L.append("")
    L.append("2. MEMUR: Oca 2026 %18,60 (11 + 6,85 fark), Tem 2026 %13,52 (7 + 6,09 fark). Tek parca zam %18,6 / onceki yil TUFE 30,9 = 0,60;")
    L.append("   asgari ucret Ocak 2026 (brut %27,0) 0,87; Ocak 2025 memur 11,5 / 44,4 = 0,26, asgari 30,0 / 44,4 = 0,68. Memur zammi asgariden DUSUK ve toplu sozlesmeyle belirleniyor.")
    L.append("")
    L.append("3. BEKLENTI: NEDEN MI, SONUC MU? (Ocak yil sonu beklentisi, Y=2015-2025, n={})".format(11))
    ys = list(range(2015, 2026))
    E = [ocak_bek(y) for y in ys]
    R = [TUFE[y] for y in ys]
    P = [TUFE[y - 1] for y in ys]
    L.append("  yil  Ocak yil-sonu bek.  gerceklesen  onceki yil  hata(gerc-bek)")
    for y, e, r, p in zip(ys, E, R, P):
        L.append("  {}  {:>14.1f}  {:>12.1f}  {:>10.1f}  {:>12.1f}".format(y, e, r, p, r - e))
    err = [r - e for r, e in zip(R, E)]
    L.append("  ort. hata {:+.1f} puan (siddet ort. {:.1f}); beklenti ile onceki yil gerceklesmesi korelasyonu {:.2f}; beklenti ile gerceklesme {:.2f}".format(
        statistics.mean(err), statistics.mean(abs(x) for x in err), corr(E, P), corr(E, R)))
    b, se, r2, _ = ols([[1, e] for e in E], R)
    L.append("  gerceklesme = a + b*beklenti: b={:.2f} (se {:.2f}), R2={:.2f}".format(b[1], se[1], r2))
    b2, se2, r22, _ = ols([[1, e, p] for e, p in zip(E, P)], R)
    L.append("  gerceklesme = a + b*beklenti + c*onceki yil: b={:.2f} (se {:.2f}), c={:.2f} (se {:.2f}), R2={:.2f}".format(b2[1], se2[1], b2[2], se2[2], r22))
    b3, se3, r23, _ = ols([[1, p] for p in P], E)
    L.append("  beklenti = a + d*onceki yil: d={:.2f} (se {:.2f}), R2={:.2f}  (beklenti ne kadar geriye bakiyor)".format(b3[1], se3[1], r23))
    L.append("  Yorum: Ocak beklentisi onceki yil gerceklesmesini ~0,97 korelasyonla izliyor (geriye bakis, adaptif) ve gerceklesmeyi ort. {:+.1f} puan DUSUK tahmin etmis; iki degisken ortak dogrusal oldugundan (b/c ayrilamaz, se buyuk) beklentinin ek aciklayici gucu yok. Nedensellik ayrilamaz.".format(statistics.mean(err)))
    L.append("")
    L.append("4. CAPA: 24 ay ve uzun vade beklentisi (hedef %5)")
    for m in ("2018-01", "2021-01", "2023-01", "2025-01", "2026-01", "2026-09"):
        d = PKA[m]
        L.append("  {}: 24 ay {:.1f}  uzun {}".format(m, d["ay24"], "{:.1f}".format(d["uzun"]) if "uzun" in d else "-"))
    u = [(m, v["uzun"]) for m, v in sorted(PKA.items()) if "uzun" in v]
    L.append("  uzun vade (basligi dogrulanmadi) {} .. {}: min {:.1f} max {:.1f}; hedef 5 ile fark son {:.1f}".format(
        u[0][0], u[-1][0], min(x for _, x in u), max(x for _, x in u), u[-1][1] - HEDEF_UZUN))
    L.append("")
    L.append("5. AYLIK TEST (gercek TUFE yillik serisi, EVDS TP.TUKFIY2025.GENEL_3; ilk bolum 3'un yerine bu esastir)")
    for h, alan in ((12, "ay12"), (24, "ay24")):
        t, _ = aylik_rapor(h, alan)
        L.extend(t)
    return "\n".join(L)


def testler():
    out = []
    ys = list(range(2015, 2026))
    E = [ocak_bek(y) for y in ys]
    R = [TUFE[y] for y in ys]
    P = [TUFE[y - 1] for y in ys]
    c26 = ((1 + EMEKLI["2026-01"] / 100) * (1 + EMEKLI["2026-07"] / 100) - 1) * 100
    out.append(("T-K1 emekli 2026 bilesik {:.2f} vs TUIK Haz 2026 yillik 32,11".format(c26), abs(c26 - 32.11) < 0.3, "mekanik geriye endeksleme tutarli (tek yil)"))
    out.append(("T-K2 Ocak beklentisi ile onceki yil gerceklesmesi korelasyonu {:.2f} (gerceklesmeyle {:.2f})".format(corr(E, P), corr(E, R)), None, "BILGI: beklenti geriye mi ileriye mi bakiyor, n=11"))
    err = statistics.mean(r - e for r, e in zip(R, E))
    out.append(("T-K3 beklenti hatasi ort. {:+.1f} puan: beklenti gerceklesmeyi sistematik dusuk tahmin".format(err), err > 0, "yonlu, anlamliligi n=11'de zayif"))
    u = PKA["2026-09"]["ay24"]
    out.append(("T-K4 24 ay beklentisi {:.1f} vs hedef 5: capa yok".format(u), u > 2 * HEDEF_UZUN, "beklenti hedefe capalanmamis"))
    X = aylik(12, "ay12")
    err = [x[3] - x[1] for x in X]; nv = [x[3] - x[2] for x in X]
    me, mn = statistics.mean(abs(a) for a in err), statistics.mean(abs(a) for a in nv)
    out.append(("T-K6 12 ay beklentisi MAE {:.1f} vs 'bugunku enflasyon devam' {:.1f} (n={}): beklenti saf kurali %15'ten fazla gecemiyor (kucuk fark)".format(me, mn, len(X)), me > 0.85 * mn, "beklentinin ek bilgi icerigi yok/az"))
    pi = [x[2] for x in X]; E = [x[1] for x in X]
    b, se, r2 = hac([[1, p] for p in pi], E, 12)
    out.append(("T-K7 beklenti = {:.1f} + {:.2f}*bugunku enflasyon, R2 {:.2f}".format(b[0], b[1], r2), r2 > 0.8, "beklenti buyuk olcude geriye bakis (adaptif)"))
    out.append(("T-K5 kamu zam verisi arama ozeti, 2024 degerleri dusuk guven; resmi tablo gerek", None, "BILGI"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (kamu / beklenti)"]
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
