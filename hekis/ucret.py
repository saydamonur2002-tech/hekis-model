"""Asgari ucret: ucret artislari gecmis enflasyonu mu izliyor, hedefi mi?

    python -m hekis.ucret

Veri: data/asgari_ucret.json (net/brut, 2015-2026, arama sonuclarindan; resmi PDF okunamadi). TUFE: kalibre.TUFE (Drive V24).
Sorular: (1) Ocak artisi onceki yil enflasyonuna mi endeksli (kesin atalet kanali)? (2) hedefin mi uzerinde?
(3) ucret artisi eklenince AR kalicilik (rho) dusuyor mu? (4) reel asgari ucret.
Asgari ucret tum ucretler degil: referans ve yaygin endeksleme noktasi. Ozel sektor ucret verisi yok.
"""

import json
import os

from hekis.kalibre import KUR, TUFE, ols

_YOL = os.path.join(os.path.dirname(__file__), "..", "data", "asgari_ucret.json")
K = json.load(open(_YOL))["kararlar"]
BRUT = {t: b for t, b, n in K}
NET = {t: n for t, b, n in K}
TUFE_ARALIK = dict(TUFE)
TUFE_ARALIK[2015] = 8.81
PKA_2026 = 29.61           # PKA Eylul 2026 yil sonu beklentisi
# OVP'nin bir onceki yilin Eylul'unda verdigi cari yil enflasyon hedefi/tahmini. 2026: arama ozeti (16). 2024-25: HAFIZADAN.
HEDEF = {2024: 33.0, 2025: 17.5, 2026: 16.0}


def onceki(t, seri=BRUT):
    """Ocak t karari: onceki gecerli tutara gore artis %."""
    ks = sorted(seri)
    k = "%d-01" % t
    p = ks[ks.index(k) - 1]
    return (seri[k] / seri[p] - 1) * 100


def aralik_tutar(y, seri=BRUT):
    cand = [k for k in seri if k.startswith(str(y))]
    return seri[sorted(cand)[-1]]


def yillik_toplam(y, seri=BRUT):
    return (aralik_tutar(y, seri) / aralik_tutar(y - 1, seri) - 1) * 100


def rapor() -> str:
    L = ["ASGARI UCRET: ENDEKSLEME SINAMASI", ""]
    L.append("  yil   Ocak artisi(brut)  Temmuz ara zam  yil toplam(Aralik)  onceki yil TUFE  ayni yil TUFE  Ocak/onceki TUFE")
    for t in range(2016, 2027):
        ocak = onceki(t)
        tem = (BRUT["%d-07" % t] / BRUT["%d-01" % t] - 1) * 100 if "%d-07" % t in BRUT else 0.0
        top = yillik_toplam(t)
        pp = TUFE_ARALIK[t - 1]
        py = TUFE_ARALIK.get(t, PKA_2026)
        L.append("  {}  {:>14.1f}  {:>14.1f}  {:>18.1f}  {:>15.1f}  {:>13.1f}  {:>12.2f}".format(
            t, ocak, tem, top, pp, py, ocak / pp) + ("   (2026: PKA beklentisi)" if t == 2026 else ""))
    L.append("")
    ys = list(range(2016, 2027))
    g = [onceki(t) for t in ys]
    pp = [TUFE_ARALIK[t - 1] for t in ys]
    b, se, r2, res = ols([[1, x] for x in pp], g)
    L.append("1. ENDEKSLEME: Ocak artisi = a + b*onceki yil TUFE (n=11, 2016-2026): a={:.1f}, b={:.2f} (se {:.2f}), R2={:.2f}".format(b[0], b[1], se[1], r2))
    ys2 = list(range(2019, 2027))
    b2, se2, r22, _ = ols([[1, TUFE_ARALIK[t - 1]] for t in ys2], [onceki(t) for t in ys2])
    L.append("   2019-2026 (n=8): b={:.2f} (se {:.2f}), R2={:.2f}. Tam endeksleme b=1.".format(b2[1], se2[1], r22))
    L.append("   Ocak artisi / onceki yil TUFE: 2024 {:.2f}, 2025 {:.2f}, 2026 {:.2f}: gecmis enflasyonun ~0,7-0,9'u kadar ucret artisi.".format(
        onceki(2024) / TUFE_ARALIK[2023], onceki(2025) / TUFE_ARALIK[2024], onceki(2026) / TUFE_ARALIK[2025]))
    L.append("")
    L.append("2. HEDEFLE KIYAS (OVP onceki Eylul hedefi): Ocak artisi - hedef")
    for t in (2024, 2025, 2026):
        L.append("   {}: ucret artisi {:.1f}, hedef {:.1f} ({}): {:+.1f} puan; ayni yil gerceklesen/beklenen enflasyon {:.1f}".format(
            t, onceki(t), HEDEF[t], "hafizadan" if t < 2026 else "arama ozeti", onceki(t) - HEDEF[t], TUFE_ARALIK.get(t, PKA_2026)))
    L.append("   Ucret artisi hedefin ~11-13 puan USTUNDE, gecmis enflasyona yakin: ucret hedefi degil gecmisi izliyor.")
    L.append("")
    reel = 1.0
    L.append("3. REEL ASGARI UCRET (Aralik/Aralik, brut / TUFE)")
    cum = []
    for t in range(2016, 2026):
        r = (1 + yillik_toplam(t) / 100) / (1 + TUFE_ARALIK[t] / 100) - 1
        reel *= 1 + r
        cum.append((t, 100 * r))
    L.append("   " + ", ".join("{} {:+.1f}".format(t, v) for t, v in cum))
    L.append("   2015-2025 kumulatif reel x{:.2f}; 2026 Ocak: {:.1f} artis vs beklenen {:.1f}: reel {:+.1f}".format(
        reel, onceki(2026), PKA_2026, ((1 + onceki(2026) / 100) / (1 + PKA_2026 / 100) - 1) * 100))
    L.append("")

    # AR + ucret
    d = {t: (KUR[t] / KUR[t - 1] - 1) * 100 for t in range(2015, 2026)}
    ys3 = list(range(2016, 2026))
    wd = {t: yillik_toplam(t) for t in ys3}
    wj = {t: onceki(t) for t in ys3}
    b0, se0, r20, _ = ols([[1, d[t], TUFE_ARALIK[t - 1]] for t in ys3], [TUFE_ARALIK[t] for t in ys3])
    L.append("4. ATALET ve UCRET: TUFE_t = a + b*kur_t + rho*TUFE_t-1 + c*ucret artisi_t (n=10)")
    L.append("   ucretsiz              : rho={:.2f} (se {:.2f}), R2={:.2f}".format(b0[2], se0[2], r20))
    for ad, w in (("Aralik/Aralik toplam artis", wd), ("yalniz Ocak karari", wj)):
        b1, se1, r21, _ = ols([[1, d[t], TUFE_ARALIK[t - 1], w[t]] for t in ys3], [TUFE_ARALIK[t] for t in ys3])
        L.append("   ucretli ({:<26}): rho={:.2f} (se {:.2f}), c={:.3f} (se {:.3f}, t={:.1f}), R2={:.2f}".format(ad, b1[2], se1[2], b1[3], se1[3], b1[3] / se1[3], r21))
    # kaldirac: 2022-23 disarida, bir yili disarida birak
    lo = []
    for out in ys3:
        k = [t for t in ys3 if t != out]
        bb, _, _, _ = ols([[1, d[t], TUFE_ARALIK[t - 1], wd[t]] for t in k], [TUFE_ARALIK[t] for t in k])
        lo.append((bb[2], bb[3]))
    k2 = [t for t in ys3 if t not in (2022, 2023)]
    b2, se2, r22, _ = ols([[1, d[t], TUFE_ARALIK[t - 1], wd[t]] for t in k2], [TUFE_ARALIK[t] for t in k2])
    L.append("   bir yili disarida birakinca (Aralik/Aralik): rho {:.2f}-{:.2f}, c {:.2f}-{:.2f}".format(min(x[0] for x in lo), max(x[0] for x in lo), min(x[1] for x in lo), max(x[1] for x in lo)))
    L.append("   2022-23 (ara zamli, asiri) disarida (n=8): rho={:.2f} (se {:.2f}), c={:.3f} (se {:.3f})".format(b2[2], se2[2], b2[3], se2[3]))
    L.append("   YORUM: Aralik/Aralik toplam artisla rho {:.2f} -> 0,32 gorunur, AMA FRAGIL: yalniz Ocak kararinda anlamsiz (t~0,5), 2022-23 disarida".format(b0[2]))
    L.append("   etki YOK (rho 0,72, c negatif). Sonuc iki asiri ara zam yilina bagli. 'Ataletin yarisi ucret kanalidir' KANITLANMADI.")
    L.append("   Saglam olan: Ocak artisi gecmis enflasyonu izliyor (b=0,61, R2=0,80) ve hedefin ~11-16 puan ustunde. Davranis gercek, enflasyona gecisi ayrilamadi.")
    return "\n".join(L)


def testler():
    out = []
    # T-U1 tutar tutarliligi: brut->net oran makul
    oran = [NET[t] / BRUT[t] for t in BRUT]
    out.append(("T-U1 net/brut orani {:.2f}-{:.2f} makul bant (0,79-0,85)".format(min(oran), max(oran)), 0.78 <= min(oran) and max(oran) <= 0.86, "veri tutarliligi"))
    out.append(("T-U2 2026 Ocak artisi brut %{:.1f}, net %{:.1f} (haberler %27)".format(onceki(2026), onceki(2026, NET)), abs(onceki(2026) - 27.0) < 0.5, "arama sonucuyla uyumlu"))
    ys = list(range(2016, 2027))
    b, se, r2, _ = ols([[1, TUFE_ARALIK[t - 1]] for t in ys], [onceki(t) for t in ys])
    out.append(("T-U3 Ocak artisi onceki yil TUFE'sine endeksli mi: b={:.2f} (se {:.2f}), R2={:.2f}; sifir degil".format(b[1], se[1], r2), b[1] / se[1] > 2.0, "n=11, 2016 +29 ve 2022-23 asiri"))
    ys2 = list(range(2024, 2027))
    sap = [onceki(t) - HEDEF[t] for t in ys2]
    out.append(("T-U4 ucret artisi hedefin ustunde: {}".format(", ".join("{:+.1f}".format(x) for x in sap)), all(x > 5 for x in sap), "2024-25 hedefler hafizadan"))
    d = {t: (KUR[t] / KUR[t - 1] - 1) * 100 for t in range(2015, 2026)}
    ys3 = list(range(2016, 2026))
    wd = {t: yillik_toplam(t) for t in ys3}
    b0, _, _, _ = ols([[1, d[t], TUFE_ARALIK[t - 1]] for t in ys3], [TUFE_ARALIK[t] for t in ys3])
    b1, se1, _, _ = ols([[1, d[t], TUFE_ARALIK[t - 1], wd[t]] for t in ys3], [TUFE_ARALIK[t] for t in ys3])
    k2 = [t for t in ys3 if t not in (2022, 2023)]
    b2, se2, _, _ = ols([[1, d[t], TUFE_ARALIK[t - 1], wd[t]] for t in k2], [TUFE_ARALIK[t] for t in k2])
    out.append(("T-U7 SAGLAMLIK: ucret eklenince rho {:.2f} -> {:.2f} (tam orneklem), ama 2022-23 disarida rho {:.2f}, c {:+.2f}: etki iki yila bagli, gecmez".format(b0[2], b1[2], b2[2], b2[3]),
                b2[2] < 0.6 * b0[2], "ucret kanalli atalet kanitlanmadi"))
    out.append(("T-U5 yalniz asgari ucret: ozel sektor ucret verisi yok. Asgari ucret ataletin gostergesi, ucret ataletinin degil", None, "BILGI"))
    out.append(("T-U6 net seri AGI ve duzenlemelerden etkilenir; brut kullanildi. Kaynak: arama sonuclari, resmi PDF okunamadi", None, "BILGI"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (ucret)"]
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
