"""Kur rejimi: kontrollu kayma ve kirilma senaryosu.

    python -m hekis.kirilma

Gozlem (data/usdtry_2026.json, TCMB EVDS): 2026'da dolar/TL duzgun kayiyor. Haftalik %0,3-0,4, aylik %1,1-2,0,
rezerv cikisindan bagimsiz. Bu rejimde baski kura degil rezerve yansir: eta ~ 0, TCMB payi cb ~ 1.
Soru su: rejim kirilirsa (net likit biterse) ne olur, ve uc kanalin cozumu bunun yaninda ne kadar?

Kirilma: kur, kayma hizinin ustunde J kadar bir kerelik sicrar. J, tarihin sok yillarinda kayma
(%20) ustu gerceklesen artislardan alinir: 2018 +20, 2021 +61, 2022 +20, 2023 +37 puan.
Enflasyon: phi1*J, atalet ile yil 1-3. Olasilik verilmez: kosullu maliyet.
"""

import datetime as dt
import json
import os
import random
import statistics

from hekis.enflasyon import TOHUM, cek, yuzdelik
from hekis.kalibre import KUR
from hekis.rezerv import U, TARIH

_YOL = os.path.join(os.path.dirname(__file__), "..", "data", "usdtry_2026.json")
GUN = json.load(open(_YOL))
KS = sorted(GUN)
KUR_2025_SON = 42.88


def kur(tarih):
    d = dt.date.fromisoformat(tarih)
    while d.isoformat() not in GUN:
        d -= dt.timedelta(days=1)
    return GUN[d.isoformat()]


AYLAR = ["2026-01-30", "2026-02-27", "2026-03-31", "2026-04-30", "2026-05-29", "2026-06-30", "2026-07-31", "2026-08-31", "2026-09-30"]
HAFTA = [("2026-08-31", "2026-09-04"), ("2026-09-04", "2026-09-11"), ("2026-09-11", "2026-09-18"), ("2026-09-18", "2026-09-25")]
SOK_ASIRI = {2018: 20.1, 2021: 61.6, 2022: 20.3, 2023: 37.2}   # kur artisi - %20 kayma, puan (kalibre.KUR)


def tempo():
    aylik = []
    onc = KUR_2025_SON
    for a in AYLAR:
        k = kur(a)
        aylik.append((k / onc - 1) * 100)
        onc = k
    return aylik


def ng(j):
    return U["resmi_rezerv"][j] - U["altin"][j]


def rapor() -> str:
    L = ["KUR REJIMI: KONTROLLU KAYMA (2026) ve KIRILMA SENARYOSU", ""]
    ay = tempo()
    k = kur("2026-10-06")
    gun = (dt.date(2026, 10, 6) - dt.date(2025, 12, 31)).days
    L.append("2026 kuru: 42,88 -> {:.2f} (6 Eki), YTD {:+.1f}%, yillik tempo {:.1f}%".format(k, (k / KUR_2025_SON - 1) * 100, ((k / KUR_2025_SON) ** (365 / gun) - 1) * 100))
    L.append("  aylik % degisim: " + " ".join("{:.2f}".format(a) for a in ay) + "   (min {:.2f}, max {:.2f}, sd {:.2f})".format(min(ay), max(ay), statistics.pstdev(ay)))
    L.append("")
    L.append("Haftalik kur degisimi ve altin-disi rezerv degisimi (mlr $):")
    L.append("  hafta                       kur %    altin-disi rezerv")
    kd, rd = [], []
    for i, (a, b) in enumerate(HAFTA):
        dk = (kur(b) / kur(a) - 1) * 100
        dr = ng(i + 1) - ng(i)
        kd.append(dk); rd.append(dr)
        L.append("  {} -> {}   {:>6.2f}   {:>+8.1f}".format(a, b, dk, dr))
    mk, mr = statistics.fmean(kd), statistics.fmean(rd)
    cov = sum((a - mk) * (b - mr) for a, b in zip(kd, rd))
    r = cov / (sum((a - mk) ** 2 for a in kd) * sum((b - mr) ** 2 for b in rd)) ** .5
    L.append("  kur sd {:.3f} puan, rezerv sd {:.1f} mlr $; korelasyon {:+.2f} (n=4, kur sd ~0: anlamsiz). Rezerv -5,6 oynarken kur 0,37'de kaldi".format(
        statistics.pstdev(kd), statistics.pstdev(rd), r))
    L.append("  Yorum: baski rezervde, kurda degil. Bu rejimde eta ~ 0 ve TCMB payi cb ~ 1, ta ki net likit bitene kadar.")
    L.append("")

    # kirilma senaryosu
    L.append("KIRILMA SENARYOSU: bir kerelik kur sicramasi J (kayma ustu), TUFE'ye etkisi (puan)")
    L.append("  tarihte kayma (%20) ustu gerceklesen: " + ", ".join("{} +{:.0f}".format(y, v) for y, v in SOK_ASIRI.items()))
    rng = random.Random(TOHUM)
    y1, y2, y3, kum = [], [], [], []
    for _ in range(4000):
        p = cek(rng)
        J = rng.uniform(15, 50)
        e1 = p["phi1"] * J
        a = p["atalet"]
        y1.append(e1); y2.append(e1 * a); y3.append(e1 * a * a); kum.append(e1 * (1 + a + a * a))
    f = lambda v: "{:.1f} [{:.1f}-{:.1f}]".format(statistics.median(v), yuzdelik(v, .1), yuzdelik(v, .9))
    L.append("  yil 1: {}   yil 2: {}   yil 3: {}".format(f(y1), f(y2), f(y3)))
    L.append("  3 yilda birikmis enflasyon artisi: {}".format(f(kum)))
    L.append("")
    # cozumun degeri
    import hekis.borc_doviz as bd
    from hekis.borc_doviz import RAMPA, cek_fx, simule
    bd.REJIM = "tam"
    rng = random.Random(TOHUM + 7)
    cozum, oran = [], []
    for kk in range(3000):
        p, q = cek_fx(rng)
        pay = {"A": q["sA"], "B": q["sB"], "C": q["sC"]}
        e = simule(p, q, pay, RAMPA["yavas"], dongu=True)["toplam"]
        J = rng.uniform(15, 50)
        e_k = p["phi1"] * J * (1 + p["atalet"] + p["atalet"] ** 2)
        cum = e[0] + e[1] + e[2]            # 3 yillik kumulatif (yillik oran dususlerinin toplami), kirilma ile ayni olcu
        cozum.append(cum)
        oran.append(e_k / max(cum, 0.05))
    L.append("KARSILASTIRMA, ayni olcu: 3 yillik kumulatif (yillik enflasyon farklarinin toplami, puan)")
    L.append("  cozum (A+B+C+dongu) kazanci: {}".format(f(cozum)))
    L.append("  kirilma maliyeti / cozum kazanci (medyan): {:.1f}x".format(statistics.median(oran)))
    L.append("  Bas-basa nokta: cozum kirilma olasiligini mutlak {:.0f} puan dusurse beklenen kazanc esitlenir (kirilma olasiligi bilinmiyor)".format(100 / statistics.median(oran)))
    return "\n".join(L)


def testler():
    out = []
    ay = tempo()
    out.append(("T-K1 aylik kayma 1,1-2,0 araliginda, sd {:.2f}: duzgun. Kur rejimi kontrollu".format(statistics.pstdev(ay)),
                statistics.pstdev(ay) < 0.35, "kayma hizi dalgalanmiyor"))
    kd = [(kur(b) / kur(a) - 1) * 100 for a, b in HAFTA]
    rd = [ng(i + 1) - ng(i) for i in range(4)]
    out.append(("T-K2 en buyuk rezerv cikisi haftasinda ({:+.1f} mlr $) kur haftaligi {:.2f}% (ortalama {:.2f}%): kur yanit vermedi".format(
        min(rd), kd[rd.index(min(rd))], statistics.fmean(kd)), kd[rd.index(min(rd))] < statistics.fmean(kd) * 1.3, "eta ~ 0, TCMB baskiyi rezerve yansitiyor"))
    # T-K3: model 2026 enflasyonunu tutturur mu, gozlenen kur temposuyla
    import hekis.gerceklik as g
    b, _, _, _ = g.fit(2025)
    pred = g.tahmin(b, 17.5, g.TUFE[2025])
    out.append(("T-K3 2026 TUFE: gozlenen kur temposu (%17,5) ile model {:.1f}, gozlem Agustos yillik 31,5. Model ~{:.0f} puan eksik".format(pred, 31.5 - pred),
                abs(31.5 - pred) < 3, "kur disi surucu (ataletin yukari tasidigi, yonetilen fiyat, ucret) var"))
    out.append(("T-K4 J (kirilma buyuklugu) tarihsel 4 vakadan: kirilma olasiligi veriden ve burada TCMB politika/kur beklentisi verisi olmadan tahmin edilemez", False, "olasilik verilmedi"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (kur rejimi)"]
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
