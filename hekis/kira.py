"""Kira bilesen: TCMB Yeni Kiraci Kira Endeksi (YKKE), gecikmeli yeniden fiyatlama, kendiliginden dezenflasyon.

    python -m hekis.kira

Veri: data/ykke_2026_08.json (TCMB EVDS TP.YKKE.*, 2018-01..2026-08, aylik, 19 bolge). NOT: kullanici 'Istanbul Ucretliler
endeksinin hizmet/kira bileseni' istedi, gelen dosya ITO'nun degil TCMB'nin YKKE'si. ITO alt kalem tablosu hala yok.

Uc sorular:
  1. Yeni kiralar gercekten asiri mi artti? (seviye)
  2. Simdi hala artiyor mu? (akis)
  3. TUFE'deki kira (mevcut sozlesmeler) yeni kirayi gecikmeyle mi izliyor? Hipotez: TUFE kira_t ~ YKKE yillik_(t-12).
     Tek nokta destekliyor (Subat 2026: mevcut kiraci %53,9 = YKKE Subat 2025 %53,9). Kimlik testi degil.
Hipotez dogruysa TUFE kirasi kendiliginden duser: yeni kira artisi dustu, eski sozlesmeler yetisiyor.
"""

import json
import os
import random
import statistics

from hekis.enflasyon import TOHUM, cek, yuzdelik
from hekis.kalibre import TUFE

_YOL = os.path.join(os.path.dirname(__file__), "..", "data", "ykke_2026_08.json")
D = json.load(open(_YOL))
PER = D["donem"]
IX = {p: i for i, p in enumerate(PER)}
TUFE_ARALIK = {**{t: TUFE[t] for t in range(2018, 2026)}, 2019: 11.84, 2021: 36.08, 2022: 64.27, 2023: 64.77}
TUIK_AGU26 = 31.51
MEVCUT_KIRACI_SUB26 = 53.9   # TCMB, arama ozeti; yeni kiraci 34,2 ayni kaynakta, YKKE'den yeniden uretildi


def lvl(k, p):
    return D["seri"][k][IX[p]]


def geri(p, n):
    y, m = map(int, p.split("-"))
    t = y * 12 + (m - 1) - n
    return "%d-%02d" % (t // 12, t % 12 + 1)


def yoy(k, p):
    q = geri(p, 12)
    return (lvl(k, p) / lvl(k, q) - 1) * 100 if q in IX else None


def reel(a, b):
    return ((1 + a / 100) / (1 + b / 100) - 1) * 100


def rapor() -> str:
    L = ["KIRA BILESEN: TCMB YENI KIRACI KIRA ENDEKSI (YKKE)", ""]
    L.append("1. SEVIYE: yeni kira yillik (Aralik/Aralik) ve reel (TUFE'ye gore), %")
    L.append("  yil    TR    Istanbul   Ankara   TUIK    reel TR   reel Istanbul")
    cum_tr, cum_t = 1.0, 1.0
    for y in range(2019, 2026):
        p = "%d-12" % y
        tr, ist, ank = yoy("TR", p), yoy("TR10", p), yoy("TR51", p)
        L.append("  {}  {:>6.1f}  {:>7.1f}  {:>8.1f}  {:>6.1f}  {:>8.1f}  {:>9.1f}".format(
            y, tr, ist, ank, TUFE_ARALIK[y], reel(tr, TUFE_ARALIK[y]), reel(ist, TUFE_ARALIK[y])))
        cum_tr *= 1 + tr / 100
        cum_t *= 1 + TUFE_ARALIK[y] / 100
    L.append("  2019-2025 kumulatif: yeni kira x{:.1f}, TUFE x{:.1f}, REEL KIRA x{:.2f} (Ocak 2018 baslangic payi dahil degil)".format(cum_tr, cum_t, cum_tr / cum_t))
    i0 = D["seri"]["TR"][0]
    L.append("  Ocak 2018 -> Aralik 2025: TR x{:.1f}, Istanbul x{:.1f}".format(lvl("TR", "2025-12") / i0, lvl("TR10", "2025-12") / D["seri"]["TR10"][0]))
    L.append("")

    L.append("2. AKIS: son 13 ay yeni kira yillik artisi, TR / Istanbul (%)")
    p0 = IX["2025-08"]
    L.append("  TR       " + " ".join("{:>5.1f}".format(yoy("TR", p)) for p in PER[p0:]))
    L.append("  Istanbul " + " ".join("{:>5.1f}".format(yoy("TR10", p)) for p in PER[p0:]))
    tr_a, ist_a = yoy("TR", "2026-08"), yoy("TR10", "2026-08")
    L.append("  Agustos 2026: TR {:.1f} (TUIK {:.2f}: reel {:+.1f}), Istanbul {:.1f} (reel {:+.1f}). Ulusal yeni kira artik enflasyonun ALTINDA, Istanbul ~yaninda.".format(
        tr_a, TUIK_AGU26, reel(tr_a, TUIK_AGU26), ist_a, reel(ist_a, TUIK_AGU26)))
    L.append("")

    L.append("3. GECIKMELI YENIDEN FIYATLAMA hipotezi: TUFE kira (mevcut sozlesme) ~ YKKE yillik, gecikme L ay")
    L.append("  Subat 2026'da mevcut kiraci artisi {:.1f}% (TCMB). YKKE TR yillik, Subat 2026'dan geri:".format(MEVCUT_KIRACI_SUB26))
    for Lg in (0, 6, 12, 18, 24):
        L.append("    gecikme {:>2} ay ({}): {:>6.1f}".format(Lg, geri("2026-02", Lg), yoy("TR", geri("2026-02", Lg))))
    L.append("  Yalniz 12 aylik gecikme tutuyor ({:.1f} = {:.1f}). Yillik sozlesmelerin gecen yilin piyasa seviyesine yenilenmesi mantikli. Tek nokta.".format(
        yoy("TR", geri("2026-02", 12)), MEVCUT_KIRACI_SUB26))
    L.append("")

    L.append("4. KENDILIGINDEN DEZENFLASYON (hipotez dogruysa): TUFE kira ~ YKKE yillik(t-12)")
    path = [("2025-12", "Ara 2025"), ("2026-08", "Agu 2026"), ("2026-12", "Ara 2026"), ("2027-08", "Agu 2027")]
    L.append("  donem      TUFE kira (tahmin)   kaynak YKKE donemi (yillik)")
    vals = {}
    for p, ad in path:
        q = geri(p, 12)
        v = yoy("TR", q) if q in IX and yoy("TR", q) is not None else None
        vals[p] = v
        L.append("  {:<9}  {:>10.1f}          {} ({})".format(ad, v, q, "gozlem"))
    L.append("  Ara 2026 -> Ara 2027: YKKE Ara 2026 henuz yok. Son gozlem ({:.1f}, Agu 2026) tasinirsa TUFE kira 2027'de ~{:.0f}'a iner.".format(tr_a, tr_a))
    rng = random.Random(TOHUM)
    w = [cek(rng)["w_kira"] for _ in range(5000)]
    d26 = vals["2025-12"] - vals["2026-12"]   # Ara 2025 (57.7) -> Ara 2026 (36.0)
    d27 = vals["2026-12"] - tr_a              # 36.0 -> 26.4 (tahmin: Aralik 2026 yeni kira = Agustos gozlemi)
    c26 = [x * d26 for x in w]
    c27 = [x * d27 for x in w]
    f = lambda v: "{:.2f} [{:.2f}-{:.2f}]".format(statistics.median(v), yuzdelik(v, .1), yuzdelik(v, .9))
    L.append("  Kira disenflasyonunun TUFE'ye katkisi (kira agirligi 4,0-7,5% VARSAYIM): 2026 {:.1f} puan dusus x agirlik = {} puan; 2027 {:.1f} puan x agirlik = {} puan".format(
        d26, f(c26), d27, f(c27)))
    L.append("  Yani politika olmadan, kira kalemi 2026'da ~1,2, 2027'de ~0,6 puan dezenflasyon uretir. Bu OVP'nin istedigi ek dezenflasyonun (-3,7) ~%15'i.")
    L.append("")

    L.append("5. A (KIRA/KONUT) KANALINA ETKISI")
    L.append("  Modelde A (bosluk/varlik enflasyonu cozulurse) yil-1 ~0,2 puan. Veri: yeni kira akisi artik enflasyonun altinda,")
    L.append("  yani cozulecek guncel PRIM yok. TUFE kirasindaki yukseklik gecmis reel kira sicramasinin (x{:.1f}) sozlesmelere yetismesi,".format(cum_tr / cum_t))
    L.append("  ve politikadan bagimsiz kendiliginden soner. A kanalinin dogrudan etkisi 0,2'nin altinda, kendiliginden soneni 1,2 + 0,6.")
    L.append("  Seviye ise kalici: kira reel olarak ~2,2-2,5 kat (Oca 2018 -> Ara 2025: x2,2; Ara 2018 -> Ara 2025 zincir: x2,5). Hane gelirine yuk, enflasyon akisina degil.")
    return "\n".join(L)


def testler():
    out = []
    out.append(("T-Y1 YKKE TR Subat 2026 yillik {:.1f} = TCMB'nin yayimladigi 34,2".format(yoy("TR", "2026-02")), abs(yoy("TR", "2026-02") - 34.2) < 0.1, "bagimsiz dogrulama, veri dogru okundu"))
    out.append(("T-Y2 12 ay gecikmeli YKKE ({:.1f}) = mevcut kiraci Subat 2026 (53,9), 6/18 ay gecikme tutmuyor ({:.1f}/{:.1f})".format(
        yoy("TR", geri("2026-02", 12)), yoy("TR", geri("2026-02", 6)), yoy("TR", geri("2026-02", 18))),
        abs(yoy("TR", geri("2026-02", 12)) - 53.9) < 0.15, "TEK nokta, hipotez, kimlik degil"))
    reel_ist = reel(yoy("TR10", "2026-08"), TUIK_AGU26)
    reel_tr = reel(yoy("TR", "2026-08"), TUIK_AGU26)
    out.append(("T-Y3 yeni kira Agustos 2026 reel: TR {:+.1f}, Istanbul {:+.1f}. Guncel kira primi yok, Istanbul'da bile kucuk".format(reel_tr, reel_ist), reel_tr < 2.0, "A kanali akis olarak sinirli"))
    cum = 1.0
    for y in range(2019, 2026):
        cum *= (1 + yoy("TR", "%d-12" % y) / 100) / (1 + TUFE_ARALIK[y] / 100)
    out.append(("T-Y4 reel yeni kira 2019-2025 x{:.2f}: seviye sicramasi gercek (kira 'asla bu kadar yuksek olamaz' tezi seviyede destekleniyor)".format(cum), cum > 1.5, "seviye var, akis normallesti"))
    # T-Y-grup: konut grubu Agu 2026 %39,77 (agirlik 11,40) = kira*w + diger*(11,40-w)
    grup, gw = 39.77, 11.40
    kira_agu = yoy("TR", geri("2026-08", 12))
    diger = [(gw * grup - w * 100 * kira_agu) / (gw - w * 100) for w in (0.04, 0.055, 0.075)]
    out.append(("T-Y8 konut grubu tutarliligi: Agu 2026 grup %39,77, kira ~{:.1f} (YKKE gecikmeli) ise elektrik-gaz-su-bakim artisi {:.0f}-{:.0f}% cikar (w_kira 4-7,5): makul".format(
        kira_agu, min(diger), max(diger)), 25 < min(diger) and max(diger) < 45, "zayif test: her agirlikta makul, hipotezi reddetmez"))
    out.append(("T-Y5 TUFE kirasi (mevcut kiraci) serisi elimde yok: gecikme hipotezi tek nokta, TUFE kira alt kalemi veya TCMB mevcut kiraci serisi gerek", None, "BILGI"))
    out.append(("T-Y6 kira agirligi (4,0-7,5%) hala dogrulanmadi: kendiliginden dezenflasyon katkisi (1,2/0,6 puan) ona dogrusal bagli", None, "BILGI"))
    out.append(("T-Y7 Aralik 2026 YKKE henuz yok: 2027 dezenflasyonu Agustos gozlemini tasiyor, YKKE daha da dusebilir", None, "BILGI"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (kira)"]
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
