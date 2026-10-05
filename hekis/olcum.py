"""Olcum kontrolu: sonuclar alternatif enflasyon olcusunde de ayakta mi.

    python -m hekis.olcum

Ana cerceve: enflasyonun buyuk kismi atalet (okuma 1). Kontrol: TUFE'nin 'gercek' enflasyonu olcmedigi
(okuma 2) olasiligi. TUIK yaninda ENAG (ust) ve ITO (alt) olculeri. ENAG yontemi tartismali, dogru kabul
edilmez; sinir degeri olarak kullanilir.

Veri: ENAG ve TUIK arama ozetleri (Euronews aktarimi), ITO resmi tablo (hekis/ito.py). ENAG icin yalniz 2-3 nokta:
bu bir ISTATISTIK degil, TUTARLILIK testidir. Daha ayrintili ITO analizi: python -m hekis.ito
"""

import math

TUIK = {"2024-12": 44.33, "2025-12": 30.89, "2026-06": 32.11, "2026-08": 31.51}
ENAG = {"2024-12": 83.40, "2025-12": 56.14, "2026-06": 51.49, "2026-07": 50.49, "2026-08": 49.03}
# ITO tuketici = Istanbul Ucretliler Gecinme Indeksi, resmi tablo (data/ITO.md). DUZELTME: onceki surumde 23,25 yazmistim,
# o ITO'nun TOPTAN endeksiydi, tuketici degil. Tuketici Ara 2025 = 40,12.
ITO = {"2025-12": 40.12, "2026-08": 39.62}

# model parcalari (kalibre.py, TUIK serisi): 2026 TUFE ~ sabit + kur + atalet
PARCA_2026 = {"sabit": -2.5, "kur": 7.4, "atalet": 21.0, "kalinti": 2.0}
KANONIK_TUIK = 2.7        # sonuc.py, 5 yilda puan (TUFE puani)


def ln1(x):
    return math.log(1 + x / 100)


def rapor() -> str:
    L = ["OLCUM KONTROLU: TUIK, ENAG, ITO", ""]
    L.append("  donem      TUIK    ENAG   ENAG/TUIK   fark(puan)   fark/TUIK   ITO")
    for k in TUIK:
        if k in ENAG:
            L.append("  {:<9}{:>7.2f}{:>8.2f}{:>10.2f}{:>12.1f}{:>12.2f}   {}".format(
                k, TUIK[k], ENAG[k], ENAG[k] / TUIK[k], ENAG[k] - TUIK[k], (ENAG[k] - TUIK[k]) / TUIK[k], ITO.get(k, "")))
    L.append("")
    L.append("Atalet kontrolu: bir yillik kalicilik (yil sonu / onceki yil sonu) olcuye bagli mi?")
    rt = TUIK["2025-12"] / TUIK["2024-12"]
    re = ENAG["2025-12"] / ENAG["2024-12"]
    L.append("  2024->2025  TUIK x{:.2f} ({:+.1f} puan),  ENAG x{:.2f} ({:+.1f} puan)".format(rt, TUIK["2025-12"] - TUIK["2024-12"], re, ENAG["2025-12"] - ENAG["2024-12"]))
    lt = ln1(TUIK["2025-12"]) - ln1(TUIK["2024-12"])
    le = ln1(ENAG["2025-12"]) - ln1(ENAG["2024-12"])
    L.append("  log(1+pi) degisimi: TUIK {:+.3f}, ENAG {:+.3f}".format(lt, le))
    L.append("  Bu uc rakam atalet katsayisi (rho~0,68) ile ayni cevrede: TUIK {:.2f}, ENAG {:.2f}. Yani 'gecen yilin ~%70'i bu yila tasiniyor' bulgusu olcu degisse de durur.".format(rt, re))
    L.append("")
    L.append("Kur payi kontrolu (2026): kur etkisi 7,4 puan, atalet 21,0. Iki kutup:")
    for ad, k in (("TUIK", 1.0), ("ENAG (Agu 2026, orantili buyutme)", ENAG["2026-08"] / TUIK["2026-08"])):
        toplam = 28.0 * k
        L.append("  {:<36} atalet payi %{:.0f}  kur payi (puan sabit) %{:.0f}  (kur etkisi orantili buyurse %27)".format(
            ad, 100 * PARCA_2026["atalet"] * k / toplam, 100 * PARCA_2026["kur"] / toplam))
    L.append("  Yani kur payi en fazla %27 (TUIK), ENAG'a gore %17'ye iner. Atalet payi her halukarda en buyuk parca.")
    L.append("")
    k_enag = ENAG["2026-08"] / TUIK["2026-08"]
    k_ito = ITO["2026-08"] / TUIK["2026-08"]
    L.append("Kanonik sonuc olcege duyarli mi? Uclu acmaz cozulurse 5 yilda {:.1f} puan (TUIK puani).".format(KANONIK_TUIK))
    L.append("  TUIK: {:.1f};  ITO tuketici olcegi (x{:.2f}, orantili): {:.1f};  ENAG olcegi (x{:.2f}, orantili): {:.1f} puan".format(
        KANONIK_TUIK, k_ito, KANONIK_TUIK * k_ito, k_enag, KANONIK_TUIK * k_enag))
    L.append("  Bant {:.1f}-{:.1f} puan (TUIK alt sinir: ITO ve ENAG ikisi de TUIK'in ustunde). Etki kucuk ve atalete gore ikincil her olcuyle.".format(KANONIK_TUIK, KANONIK_TUIK * k_enag))
    L.append("")
    L.append("Fark zaman icinde kuculuyor: fark/TUIK {:.2f} (Ara 2024) -> {:.2f} (Ara 2025) -> {:.2f} (Haz 2026) -> {:.2f} (Agu 2026).".format(
        (ENAG["2024-12"] - TUIK["2024-12"]) / TUIK["2024-12"], (ENAG["2025-12"] - TUIK["2025-12"]) / TUIK["2025-12"],
        (ENAG["2026-06"] - TUIK["2026-06"]) / TUIK["2026-06"], (ENAG["2026-08"] - TUIK["2026-08"]) / TUIK["2026-08"]))
    return "\n".join(L)


def testler():
    out = []
    rt = TUIK["2025-12"] / TUIK["2024-12"]
    re = ENAG["2025-12"] / ENAG["2024-12"]
    out.append(("T-Ö1 bir yillik kalicilik: TUIK {:.2f}, ENAG {:.2f} (fark {:.2f}). Olcu degisse de ~%70 tasiniyor".format(rt, re, abs(rt - re)), abs(rt - re) < 0.15, "atalet bulgusu olcuden bagimsiz (yalniz bir gecis, 2 nokta)"))
    k = ENAG["2026-08"] / TUIK["2026-08"]
    atalet_enag = PARCA_2026["atalet"] * k / (28.0 * k)
    kur_enag = PARCA_2026["kur"] / (28.0 * k)
    out.append(("T-Ö2 atalet payi %{:.0f} (orantili buyutmede TANIM GEREGI ayni), kur payi ENAG'da %{:.0f}: siralama degismez ama bu bir test degil, aritmetik".format(100 * atalet_enag, 100 * kur_enag), None, "BILGI: olcu hatasi tum enflasyonu ayni oranda buyutuyorsa pay degismez"))
    gap = [(ENAG[k] - TUIK[k]) / TUIK[k] for k in ("2024-12", "2025-12", "2026-06", "2026-08")]
    out.append(("T-Ö3 olcu farki azaliyor ({:.2f} -> {:.2f}). Zamanla yaklasmanin nedeni (yontem, enflasyon dususu) ayrilamaz".format(gap[0], gap[-1]), None, "BILGI"))
    out.append(("T-Ö4 yalniz 2-3 gozlem, 2020-23 ENAG yok. Kalibre edilmis rho'yu ENAG ile yeniden tahmin EDEMEM", None, "BILGI: ENAG 2020-23 serisi gerek"))
    out.append(("T-Ö5 ENAG'in yontemi ve ITO'nun yeni indeksi dogrulanmadi (arama ozeti)", None, "BILGI"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (olcum)"]
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
