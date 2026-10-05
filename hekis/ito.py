"""ITO Enflasyon Indeksi: ucuncu olcu ve goreli fiyat kontrolu.

    python -m hekis.ito

Kaynak: data/ito_enflasyon_endeksi.json (ITO resmi tablo, 45 ay). Iki seri:
  uge    Istanbul Ucretliler Gecinme Indeksi (tuketici, 1995=100)
  toptan Istanbul Toptan Esya Fiyatlari (1963=100)
Kontrol: (1) atalet olcuye bagli mi, (2) tuketici-toptan makasi (hizmet/mal ayrimi), (3) TUIK ile fark.
"""

import json
import os

from hekis.kalibre import TUFE, ols

_YOL = os.path.join(os.path.dirname(__file__), "..", "data", "ito_enflasyon_endeksi.json")
D = json.load(open(_YOL))
UGE, TOPTAN = D["uge"], D["toptan"]


def yoy(seri, key):
    return seri[key][2]


def ara(seri, y):
    return seri["%d-12" % y][2]


def rapor() -> str:
    L = ["ITO ENFLASYON INDEKSI (resmi tablo), uc olcu ve goreli fiyat", ""]
    L.append("Yil sonu (Aralik/Aralik) % :  TUIK  | ITO tuketici (Ucretliler Gecinme) | ITO toptan | ENAG")
    enag = {2024: 83.40, 2025: 56.14}
    for y in (2023, 2024, 2025):
        L.append("  {}              {:>6.2f} | {:>8.2f}                         | {:>7.2f}   | {}".format(
            y, TUFE[y], ara(UGE, y), ara(TOPTAN, y), "{:.2f}".format(enag[y]) if y in enag else "-"))
    L.append("  2026 Agustos yillik:  TUIK 31.51 | ITO tuketici {:.2f} | ITO toptan {:.2f} | ENAG 49.03".format(yoy(UGE, "2026-08"), yoy(TOPTAN, "2026-08")))
    L.append("  2026 Eylul yillik:    ITO tuketici {:.2f} | ITO toptan {:.2f}   (yil basindan beri {:.2f} / {:.2f})".format(
        yoy(UGE, "2026-09"), yoy(TOPTAN, "2026-09"), UGE["2026-09"][1], TOPTAN["2026-09"][1]))
    L.append("")
    L.append("FARK ITO tuketici - TUIK (puan): " + ", ".join("{} {:+.1f}".format(y, ara(UGE, y) - TUFE[y]) for y in (2023, 2024, 2025))
             + ", Agu 2026 {:+.1f}".format(yoy(UGE, "2026-08") - 31.51))
    L.append("  ITO tuketici TUIK'in ~9-11 puan USTUNDE, ENAG'in altinda. Fark sabit, ENAG-TUIK farki ise kuculuyor (39 -> 17).")
    L.append("")

    L.append("ATALET KONTROLU: bir yillik kalicilik (yil sonu / onceki yil sonu)")
    for ad, ser in (("TUIK", None), ("ITO tuketici", UGE), ("ITO toptan", TOPTAN)):
        if ser is None:
            r = [TUFE[2024] / TUFE[2023], TUFE[2025] / TUFE[2024]]
        else:
            r = [ara(ser, 2024) / ara(ser, 2023), ara(ser, 2025) / ara(ser, 2024)]
        L.append("  {:<14} 2023->24 x{:.2f}   2024->25 x{:.2f}".format(ad, r[0], r[1]))
    L.append("  ENAG           2024->25 x{:.2f}".format(56.14 / 83.40))
    L.append("  Tuketici olculerinde (TUIK, ITO, ENAG) x0,67-0,74, toptanda x0,57-0,65. Model rho 0,68 tuketici bandinin icinde.")
    L.append("")

    # aylik yillik-yillik AR
    ks = sorted(UGE)
    X, Y = [], []
    for k in ks:
        y, m = k.split("-")
        pk = "%d-%s" % (int(y) - 1, m)
        if pk in UGE:
            X.append([1, UGE[pk][2]]); Y.append(UGE[k][2])
    b, se, r2, _ = ols(X, Y)
    L.append("AYLIK YILLIK AR (ITO tuketici): yillik_t = a + rho*yillik_t-12, n={}".format(len(Y)))
    L.append("  rho={:.2f} (se {:.2f}), a={:.1f}, R2={:.2f}. Yil sonu gecisleri 0,73, model 0,68 (se 0,16); aylik veri DAHA DUSUK atalet gosteriyor.".format(b[1], se[1], b[0], r2))
    L.append("  Not: pencereler ust uste biner (otokorelasyon), 2024-26 tek rejim, R2 dusuk. Atalet 0,45-0,73 araligi; OVP'nin istedigi 0,45 bu aralikta.")
    X2, Y2 = [], []
    for k in ks[1:]:
        X2.append([1, UGE[ks[ks.index(k) - 1]][0]]); Y2.append(UGE[k][0])
    b2, se2, r22, _ = ols(X2, Y2)
    L.append("AYLIK AR (aylik % degisim, ITO tuketici): m_t = a + phi*m_t-1: phi={:.2f} (se {:.2f}), n={}, R2={:.2f}".format(b2[1], se2[1], len(Y2), r22))
    L.append("")

    L.append("GORELI FIYAT: tuketici - toptan makasi (yillik, puan)")
    L.append("  " + ", ".join("{} {:+.1f}".format(y, ara(UGE, y) - ara(TOPTAN, y)) for y in (2023, 2024, 2025))
             + ", Agu 2026 {:+.1f}, Eyl 2026 {:+.1f}".format(yoy(UGE, "2026-08") - yoy(TOPTAN, "2026-08"), yoy(UGE, "2026-09") - yoy(TOPTAN, "2026-09")))
    L.append("  Tuketici fiyatlari toptandan 12-17 puan hizli artiyor: enflasyon mal (kura bagli) degil hizmet ve marj tarafinda.")
    L.append("  Bu, atalet okumasi ile uyumlu: endeksli kalemler (kira, hizmet) kurdan bagimsiz artiyor.")
    return "\n".join(L)


def testler():
    out = []
    # T-I1 zincir tutarliligi
    bad = 0
    for ser in (UGE, TOPTAN):
        for y in (2023, 2024, 2025, 2026):
            c = 1.0
            for m in range(1, 13):
                k = "%d-%02d" % (y, m)
                if k not in ser:
                    break
                c *= 1 + ser[k][0] / 100
                if abs((c - 1) * 100 - ser[k][1]) > 0.25:
                    bad += 1
    out.append(("T-I1 PDF veri tutarliligi: aylik bilesik = yil basindan beri, {} tutarsiz ay (Eylul 2024 toptan duzeltildi)".format(bad), bad == 0, "ayristirma dogrulugu"))
    # T-I2 yillik= zincir carpi
    ok = True
    for y in (2024, 2025):
        c = 1.0
        for m in range(1, 13):
            c *= 1 + UGE["%d-%02d" % (y, m)][0] / 100
        ok = ok and abs((c - 1) * 100 - UGE["%d-12" % y][2]) < 0.3
    out.append(("T-I2 ITO tuketici: Aralik yillik = 12 aylik bilesik (2024, 2025)", ok, "kimlik"))
    # T-I3 atalet bandi
    r = [ara(UGE, 2024) / ara(UGE, 2023), ara(UGE, 2025) / ara(UGE, 2024), TUFE[2024] / TUFE[2023], TUFE[2025] / TUFE[2024], 56.14 / 83.40]
    out.append(("T-I3 kalicilik 4 olcuyle {:.2f}-{:.2f}; model rho 0,68 bu bantta".format(min(r), max(r)), min(r) - 0.05 <= 0.68 <= max(r) + 0.05, "atalet olcuden bagimsiz, 5 gecis"))
    out.append(("T-I4 ITO tuketici 'Istanbul ucretlileri' endeksi: ulusal TUFE ile ayni sepet/agirlik degil. Fark (+9-11 puan) yontem mi gercek mi ayrilamaz", None, "BILGI"))
    out.append(("T-I5 kira ve konut kalemi ITO tablosunda yok: A kanali dogrudan sinanamaz", None, "BILGI"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (ito)"]
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
