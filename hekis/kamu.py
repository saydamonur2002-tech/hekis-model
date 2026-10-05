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
