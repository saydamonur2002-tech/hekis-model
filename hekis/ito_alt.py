"""ITO Istanbul Ucretliler Gecinme Indeksi alt kalemleri: konut, hizmet, gecikme sinamasi.

    python -m hekis.ito_alt

Kaynak: ITO Fiyat Indeksleri Kitabi (kullanici PDF, 2026-10-05): yillik % degisim Ocak 2021-Aralik 2025 (9 seri),
seviye 1996-2024 yillik ortalama ve 2025 aylik (1995=100). data/ito_alt_kalem.json.
KONUT HARCAMALARI TUFE kirasi degildir: kira + elektrik/gaz/su + bakim bilesimi, Istanbul ucretlileri sepeti.

Sorular:
  1. Konut genelden ne kadar ayrisiyor, ne zaman (kira sozlesmelerinin gecikmesi)?
  2. Konutun goreli fiyati tarihsel duzeyine gore nerede (yetisme payi var mi)?
  3. Yeni kira (YKKE) ile konut arasindaki gecikme 12 ay mi? (kira.py hipotezi)
"""

import json
import os
import random
import statistics

from hekis.enflasyon import TOHUM, cek
from hekis.kira import IX as YIX, yoy as ykke_yoy, geri as yg

_YOL = os.path.join(os.path.dirname(__file__), "..", "data", "ito_alt_kalem.json")
D = json.load(open(_YOL))
Y = D["seri"]
SEV = D["seviye"]
KONUT_IX = 9      # seviye listesinde konut sirasi (genel = 0)

ADLAR = {"genel": "GENEL", "gida": "Gida", "konut": "KONUT", "ev_esyasi": "Ev esyasi", "giyim": "Giyim",
         "saglik_kisisel": "Saglik+kisisel bakim", "ulastirma_haberlesme": "Ulastirma+haberlesme",
         "kultur_egitim": "Kultur+egitim", "diger": "Diger"}


def corr(x, y):
    mx, my = sum(x) / len(x), sum(y) / len(y)
    sx = sum((a - mx) ** 2 for a in x) ** .5
    sy = sum((b - my) ** 2 for b in y) ** .5
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def lag_corr(ad, L):
    X, Z = [], []
    for k in sorted(Y[ad]):
        q = yg(k, L)
        v = ykke_yoy("TR", q) if q in YIX else None
        if v is not None:
            X.append(v)
            Z.append(Y[ad][k])
    return corr(X, Z), len(X)


def rapor() -> str:
    L = ["ITO ALT KALEMLER: KONUT, HIZMET ve GECIKME SINAMASI", ""]
    L.append("1. YILLIK % DEGISIM (Aralik/Aralik), Istanbul Ucretliler Gecinme, alt gruplar")
    L.append("  grup                    2021   2022   2023   2024   2025   2025 genel'e gore")
    for a in ("genel", "konut", "ulastirma_haberlesme", "diger", "gida", "saglik_kisisel", "kultur_egitim", "ev_esyasi", "giyim"):
        v = [Y[a]["%d-12" % y] for y in range(2021, 2026)]
        L.append("  {:<22}{:>6.1f}{:>7.1f}{:>7.1f}{:>7.1f}{:>7.1f}   {:>+8.1f}".format(ADLAR[a], *v, v[-1] - Y["genel"]["2025-12"]))
    kz = [Y["konut"]["%d-12" % y] - Y["genel"]["%d-12" % y] for y in range(2021, 2026)]
    L.append("  Konut - genel (puan): " + ", ".join("{} {:+.1f}".format(y, k) for y, k in zip(range(2021, 2026), kz)))
    L.append("  2022-23'te konut genelin ALTINDA (-13, -29), 2024-25'te ustunde (+27, +19): kira sozlesmeleri gecikmeyle yetisiyor.")
    L.append("  (Hafizadan, dogrulanmadi: Haziran 2022-Temmuz 2023 arasi kira artisi yasal olarak %25 ile sinirliydi, 2023 cukurunu aciklar.)")
    L.append("")

    yl = [k for k in sorted(SEV) if len(k) == 4]
    rel = {k: SEV[k][KONUT_IX] / SEV[k][0] for k in yl}
    rel["2025-12"] = SEV["2025-12"][KONUT_IX] / SEV["2025-12"][0]
    tar = [rel[k] for k in yl if 1996 <= int(k) <= 2020]
    ort, sd = statistics.mean(tar), statistics.pstdev(tar)
    L.append("2. KONUTUN GORELI FIYATI (konut endeksi / genel endeks)")
    L.append("  1996-2020 ortalama {:.3f} (sd {:.3f}). 2020 {:.3f}, 2021 {:.3f}, 2022 {:.3f}, 2023 {:.3f} (dip), 2024 {:.3f}, Aralik 2025 {:.3f}".format(
        ort, sd, rel["2020"], rel["2021"], rel["2022"], rel["2023"], rel["2024"], rel["2025-12"]))
    L.append("  Aralik 2025 tarihsel ortalamanin {:.2f} sd ALTINDA: konut hala goreli ucuz. Ortalamaya donerse genele gore ~%{:.0f} daha artar.".format(
        (ort - rel["2025-12"]) / sd, 100 * (ort / rel["2025-12"] - 1)))
    L.append("  UYARI: bu YKKE'deki reel x2,5'e ters gorunur. Konut endeksi mevcut sozlesmeleri ve elektrik-gaz-su'yu da icerir, yasal tavan ve yetisme kaydirir.")
    L.append("")

    L.append("3. GECIKME SINAMASI: konut yillik_t ile YKKE (TR) yillik_(t-L) korelasyonu, 2021-01..2025-12")
    best = {}
    for a in ("konut", "genel"):
        rs = [(Lg,) + lag_corr(a, Lg) for Lg in range(0, 31)]
        best[a] = max(rs, key=lambda r: r[1])
        L.append("  {:<6} en iyi gecikme {:>2} ay (r={:.2f}, n={});  r(L=0)={:.2f}, r(L=6)={:.2f}, r(L=12)={:.2f}, r(L=18)={:.2f}, r(L=24)={:.2f}".format(
            a, best[a][0], best[a][1], best[a][2], *[next(r[1] for r in rs if r[0] == Lg) for Lg in (0, 6, 12, 18, 24)]))
    L.append("  Kontrol: genel enflasyon yeni kiraya AYNI AYDA bagli (r=0,90), konut ise ayni ayda zayif (0,43), gecikmeyle daha guclu.")
    L.append("  kira.py hipotezi (12 ay) bu seride DESTEKLENMIYOR: r(12) = {:.2f}. En iyi ~{} ay, o da zayif (r={:.2f}).".format(
        lag_corr("konut", 12)[0], best["konut"][0], best["konut"][1]))
    L.append("")

    # gecikmeye gore kendiliginden dezenflasyon
    rng = random.Random(TOHUM)
    w = statistics.median(cek(rng)["w_kira"] for _ in range(4000))
    L.append("4. KENDILIGINDEN KIRA DEZENFLASYONU, gecikme duyarliligi (TUFE kira_t ~ YKKE yillik_(t-L), kira agirligi medyan %{:.1f} VARSAYIM)".format(100 * w))
    L.append("  L    kira Ara 2025  Ara 2026  Ara 2027(*)   2026 katki   2027 katki (puan TUFE)")
    for Lg in (12, 18, 24):
        def k(p):
            q = yg(p, Lg)
            if q in YIX:
                return ykke_yoy("TR", q)
            return ykke_yoy("TR", "2026-08")     # YKKE'nin son gozlemi tasinir
        a25, a26, a27 = k("2025-12"), k("2026-12"), k("2027-12")
        L.append("  {:<4}{:>11.1f}{:>11.1f}{:>12.1f}{:>13.2f}{:>13.2f}".format(Lg, a25, a26, a27, w * (a25 - a26), w * (a26 - a27)))
    L.append("  (*) YKKE Agustos 2026 sonrasi yok, son gozlem (%26,4) tasindi. Gecikme uzadikca dezenflasyon 2027'ye kayar, toplam ayni.")
    ito_konut = Y["konut"]["2025-12"]
    L.append("  SEVIYE KONTROLU: ITO konut Ara 2025 yillik %{:.1f}. L=24 icin kira %{:.0f} ve konutun yarisi kira ise elektrik-gaz-su-bakim %{:.0f}'e dusmeli: IMKANSIZ.".format(
        ito_konut, ykke_yoy("TR", yg("2025-12", 24)), 2 * ito_konut - ykke_yoy("TR", yg("2025-12", 24))))
    L.append("  L=18 icin kira %{:.0f}, diger kalemler %{:.0f}; L=12 icin kira %{:.0f}, diger %{:.0f}. Makul aralik 12-18 ay: 2026 katki 1,2-1,6, 2027 katki 0,6-1,2 puan.".format(
        ykke_yoy("TR", yg("2025-12", 18)), 2 * ito_konut - ykke_yoy("TR", yg("2025-12", 18)),
        ykke_yoy("TR", yg("2025-12", 12)), 2 * ito_konut - ykke_yoy("TR", yg("2025-12", 12))))
    L.append("")
    L.append("OKUMA: konut kalemi gecmis kira sicramasini gecikmeyle yansitiyor, ama gecikme tek sayi degil (12-24 ay) ve yasal tavan gibi")
    L.append("  kurumsal etkilerle kirleniyor. Kira dezenflasyonu geliyor, zamanlamasi belirsiz. Konutun goreli fiyati hala tarihsel ortalamanin altinda.")
    return "\n".join(L)


def testler():
    out = []
    # T-A1 capraz dogrulama
    from hekis.ito import UGE
    fark = max(abs(Y["genel"]["%d-12" % y] - UGE["%d-12" % y][2]) for y in (2023, 2024, 2025) if "%d-12" % y in Y["genel"])
    out.append(("T-A1 iki ITO kaynagi tutarli: genel Aralik yillik 2023-25 farki en fazla {:.2f} puan".format(fark), fark < 0.02, "kitap ile genel tablo ayni"))
    out.append(("T-A2 60 ay x 9 seri okundu, eksik yok", all(len(Y[a]) == 60 for a in Y), "ayristirma"))
    r12 = lag_corr("konut", 12)[0]
    rs = [(Lg, lag_corr("konut", Lg)[0]) for Lg in range(0, 31)]
    bl = max(rs, key=lambda r: r[1])
    out.append(("T-A3 12 ay gecikme hipotezi (kira.py): konut r(12)={:.2f}, en iyi gecikme {} ay (r={:.2f})".format(r12, bl[0], bl[1]), r12 >= bl[1] - 0.1, "12 ay en iyiye yakin degil: hipotez bu seride DESTEKLENMIYOR"))
    yl = [k for k in sorted(SEV) if len(k) == 4]
    tar = [SEV[k][KONUT_IX] / SEV[k][0] for k in yl if 1996 <= int(k) <= 2020]
    cur = SEV["2025-12"][KONUT_IX] / SEV["2025-12"][0]
    out.append(("T-A4 konut goreli fiyati tarihsel araliginda mi: {:.3f} vs ort {:.3f} +-{:.3f}".format(cur, statistics.mean(tar), statistics.pstdev(tar)),
                abs(cur - statistics.mean(tar)) < 2 * statistics.pstdev(tar), "2 sd icinde: asiri sapma yok ama 1,5 sd altinda"))
    k24 = ykke_yoy("TR", yg("2025-12", 24))
    out.append(("T-A7 seviye kontrolu: L=24 icin Ara 2025 kira %{:.0f} > ITO konut %{:.1f}: kira konutun ~yarisi ise diger kalemler negatif olmali, L=24 reddedilir".format(k24, Y["konut"]["2025-12"]),
                k24 < 1.3 * Y["konut"]["2025-12"], "L=24 seviye olarak imkansiz"))
    out.append(("T-A5 konut harcamalari TUFE kirasi degil (kira+enerji+bakim, Istanbul ucretlileri). Kira alt kalemi ve agirliklari ITO tablosunda yok", None, "BILGI"))
    out.append(("T-A6 2022-23 yasal kira tavani (%25) hafizadan, dogrulanmadi. Gecikme sinamasini kirletir", None, "BILGI"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (ito_alt)"]
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
