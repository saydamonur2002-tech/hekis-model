"""Modelin amaci: enflasyonun ATALET / UCLU ACMAZ / DOVIZ olarak yuzde ayrismasi.

    python -m hekis.ayrisma

2026 enflasyonu (model icin 28 puan, TCMB yil sonu tahmini; Agu 2026 gozlem 31,5) uc kovaya ayrilir:
  DOVIZ   = kur terimi (indirgenmis form, kalibre/atalet.py). Doviz borcu uzerinden acmaz kaynakli kismi (~0,7) bu terimin icinde.
  ACMAZ   = kira A + mahsup B + ic borc C, dogrudan etki (sonuc.py, 5 yillik katki = kalici duzey etkisi)
  ATALET  = atalet teriminden ACMAZ'IN tasinan kismi cikarilmis SAF atalet (acmaz atalet uzerinden tasindigi icin cift sayim olmasin)
  KALAN   = sabit + kalinti (aciklanamayan)
Indirgenmis form iki spesifikasyonda: (A) 2 terimli, (B) gecikmeli kurlu 3 terimli. Ayrim spesifikasyona baglidir, bu bir bulgu:
yuzdeler tek sayi degil, ARALIKTIR.
Bu bir katki ayristirmasidir, nedensellik kaniti degil: atalet ve beklenti ayni anda olusur, acmaz katkisi senaryo (haircut, sizinti) varsayimlidir.
"""

import statistics

from hekis.atalet import model2, model3
from hekis.sonuc import kos
from hekis.enflasyon import yuzdelik

TOPLAM = 28.0   # 2026 model enflasyonu
A = {"sabit": -2.5, "kur": 7.4, "atalet": 21.0, "kalinti": 2.0}
B = {"sabit": -7.5, "kur": 7.4 + 8.5, "atalet": 13.4, "kalinti": 6.2}   # kur = bu yil + gecen yil


def acmaz():
    r = kos("tam", n=3000)
    d = [x["dir"][-1] for x in r]
    f = [x["fx"][-1] for x in r]
    return d, f


def kovalar(P, acm):
    atalet = P["atalet"] - acm
    kalan = P["sabit"] + P["kalinti"]
    return {"ATALET (saf)": atalet, "UCLU ACMAZ (A+B+C)": acm, "DOVIZ (kur)": P["kur"], "KALAN (sabit+kalinti)": kalan}


def rapor() -> str:
    d, f = acmaz()
    dm = statistics.median(d)
    L = ["ENFLASYON AYRISMASI: ATALET / UCLU ACMAZ / DOVIZ (2026, toplam {:.0f} puan)".format(TOPLAM), ""]
    L.append("Acmaz dogrudan (5 yillik kalici etki): {:.1f} puan [{:.1f}-{:.1f}];  acmazin doviz borcu uzerinden kismi {:.1f} [{:.1f}-{:.1f}] (doviz kovasinin ICINDE)".format(
        dm, yuzdelik(d, .1), yuzdelik(d, .9), statistics.median(f), yuzdelik(f, .1), yuzdelik(f, .9)))
    L.append("")
    for ad, P in (("(A) 2 terimli (kur bu yil)", A), ("(B) 3 terimli (kur bu yil + gecen yil)", B)):
        K = kovalar(P, dm)
        L.append(ad)
        for k, v in K.items():
            L.append("    {:<24} {:>6.1f} puan   %{:>5.1f}".format(k, v, 100 * v / TOPLAM))
        L.append("    toplam {:.1f}".format(sum(K.values())))
    ka, kb = kovalar(A, dm), kovalar(B, dm)
    L.append("")
    L.append("ARALIK (iki spesifikasyon): ATALET %{:.0f}-{:.0f}, DOVIZ %{:.0f}-{:.0f}, UCLU ACMAZ %{:.0f} (MC bandi ile %{:.0f}-{:.0f}), KALAN %{:.0f} ile %{:.0f}".format(
        100 * kb["ATALET (saf)"] / TOPLAM, 100 * ka["ATALET (saf)"] / TOPLAM,
        100 * ka["DOVIZ (kur)"] / TOPLAM, 100 * kb["DOVIZ (kur)"] / TOPLAM,
        100 * dm / TOPLAM, 100 * yuzdelik(d, .1) / TOPLAM, 100 * yuzdelik(d, .9) / TOPLAM,
        100 * ka["KALAN (sabit+kalinti)"] / TOPLAM, 100 * kb["KALAN (sabit+kalinti)"] / TOPLAM))
    L.append("")
    L.append("OKUMA")
    L.append("  - Asil buyuk iki kova ATALET ve DOVIZ; ikisi arasindaki pay kur gecikmesinin atalete mi doviz kovasina mi yazildigina bagli (A: atalet baskin, B: doviz baskin).")
    L.append("  - UCLU ACMAZ dogrudan olarak kucuk (%4-10). Buyuklugu spesifikasyondan degil SIZINTI/HAIRCUT varsayimlarindan geliyor, veriden tanimlanmadi.")
    L.append("  - Acmazin asil agirligi ATALET ve DOVIZ icinde saklanmis olabilir (kalici borc/doviz birikimi), dogrudan terim bunu yakalamaz: alt sinir.")
    L.append("  - Atalet tek bir sey degil: yasal endeksleme (emekli, TBK kira), beklenti (R2 0,92 geriye bakis), ucret (asgari Ocak = 11 + 0,61*onceki TUFE). Hangisinin nedensel oldugu AYRILAMADI (ayni anda olusuyorlar).")
    L.append("  - Olcu (TUIK/ITO/ENAG) orantili buyurse yuzdeler degismez, puanlar buyur (bkz olcum.py).")
    return "\n".join(L)


def testler():
    out = []
    d, _ = acmaz()
    dm = statistics.median(d)
    for ad, P in (("A", A), ("B", B)):
        K = kovalar(P, dm)
        out.append(("T-Y{} kovalar toplami {:.1f} = {:.1f}".format(ad, sum(K.values()), TOPLAM), None, "BILGI: muhasebe kimligi, kanit degil"))
    out.append(("T-Y3 acmaz payi %{:.0f}: iki spesifikasyonda da kucuk kova".format(100 * dm / TOPLAM), dm / TOPLAM < 0.15, "ama haircut/sizinti varsayimli"))
    out.append(("T-Y4 atalet/doviz sirasi spesifikasyona bagli (A atalet %{:.0f}, B %{:.0f})".format(100 * (A["atalet"] - dm) / TOPLAM, 100 * (B["atalet"] - dm) / TOPLAM), None, "BILGI: tek bir yuzde verilemez"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (ayrisma)"]
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
