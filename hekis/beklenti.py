"""TCMB Piyasa Katilimcilari Anketi (Eylul 2026): beklentiler ne diyor?

    python -m hekis.beklenti

Veri: data/pka_2026_09.json (67 katilimci). Sorular:
  1. Beklentiler ataleti iceriyor mu (beklenen kalicilik)? Hedefe capalanmis mi?
  2. PKA, OVP, TCMB ve model yollari nerede ayriliyor?
  3. Kur ve faiz beklentisi modelin varsayimlariyla (kayma kurali, faiz26) uyumlu mu?
"""

import json
import os

from hekis.kalibre import TUFE

_YOL = os.path.join(os.path.dirname(__file__), "..", "data", "pka_2026_09.json")
P = json.load(open(_YOL))
E = P["tufe_yillik"]
TUIK_AGU26 = 31.51
TCMB_HEDEF = 5.0     # TCMB orta vadeli hedef (arama ozeti, Karahan)
OVP = {2026: 28.4, 2027: 21.0}
TCMB_TAHMIN = {2026: 28.0, 2027: 15.0}
KUR_2025_SON = 42.88


def rapor() -> str:
    L = ["PIYASA KATILIMCILARI ANKETI, EYLUL 2026", ""]
    L.append("1. ENFLASYON BEKLENTILERI (yillik %)")
    L.append("   2026 sonu {:.2f} (onceki anket {:.2f}); 12 ay sonrasi {:.2f}; 2027 sonu {:.2f}; 24 ay sonrasi {:.2f}".format(
        E["2026_sonu"], P["onceki_anket"]["2026_sonu"], E["12_ay_sonrasi"], E["gelecek_yil_sonu_2027"], E["24_ay_sonrasi"]))
    r1 = E["12_ay_sonrasi"] / TUIK_AGU26
    r2 = E["24_ay_sonrasi"] / E["12_ay_sonrasi"]
    L.append("   BEKLENEN KALICILIK: 12 ay sonrasi / bugun ({:.2f}) = {:.2f};  24 ay / 12 ay = {:.2f}".format(TUIK_AGU26, r1, r2))
    L.append("   Gerceklesen kalicilik 0,67-0,74 (TUIK, ITO, ENAG); model rho 0,68. Beklentiler ayni cevrede: yilda ~%25 dezenflasyon.")
    L.append("   HEDEFE CAPA: 24 ay sonrasi beklenti {:.1f} vs TCMB hedefi {:.0f}: {:.1f} puan fark. Beklentiler hedefe cakilmamis, ataleti kendisi tasiyor.".format(
        E["24_ay_sonrasi"], TCMB_HEDEF, E["24_ay_sonrasi"] - TCMB_HEDEF))
    L.append("   Uzun vade sutunu (baslik PDF'de kesik): {:.2f}".format(E["uzun_vade_baslik_kesik"]))
    L.append("")

    L.append("2. YOLLAR (yil sonu TUFE %)")
    L.append("   2026: PKA {:.2f}, OVP {:.1f}, TCMB {:.1f}   |   2027: PKA {:.2f}, OVP {:.1f}, TCMB {:.1f}".format(
        E["2026_sonu"], OVP[2026], TCMB_TAHMIN[2026], E["gelecek_yil_sonu_2027"], OVP[2027], TCMB_TAHMIN[2027]))
    L.append("   Piyasa 2027'de TCMB'nin %15'inin {:.1f} puan USTUNDE, OVP'nin %21'inin {:.1f} puan ustunde. Model (cipali baz) 26,7 (ovp.py): piyasadan yuksek.".format(
        E["gelecek_yil_sonu_2027"] - TCMB_TAHMIN[2027], E["gelecek_yil_sonu_2027"] - OVP[2027]))
    L.append("   Piyasanin 2026->2027 dusus: {:.1f} puan ({:.0f}%); OVP {:.1f} (%{:.0f}); TCMB {:.1f} (%{:.0f}).".format(
        E["2026_sonu"] - E["gelecek_yil_sonu_2027"], 100 * (1 - E["gelecek_yil_sonu_2027"] / E["2026_sonu"]),
        OVP[2026] - OVP[2027], 100 * (1 - OVP[2027] / OVP[2026]), TCMB_TAHMIN[2026] - TCMB_TAHMIN[2027], 100 * (1 - TCMB_TAHMIN[2027] / TCMB_TAHMIN[2026])))
    L.append("   Yani piyasa yilda ~%23 dusus bekliyor (kalicilik 0,77), OVP %26, TCMB %46. Piyasa ataletin kirilmasina inanmiyor.")
    L.append("")

    k = P["kur"]
    d26 = (k["2026_sonu"] / KUR_2025_SON - 1) * 100
    d12 = (k["12_ay_sonrasi"] / k["cari_ay_sonu"] - 1) * 100
    d27_9ay = (k["12_ay_sonrasi"] / k["2026_sonu"] - 1) * 100            # Aralik 2026 -> Eylul 2027: 9 ay
    d27 = ((k["12_ay_sonrasi"] / k["2026_sonu"]) ** (12 / 9) - 1) * 100  # yillik
    L.append("3. KUR: cari ay sonu {:.2f} (gozlem 6 Ekim 49,12), 2026 sonu {:.2f}, 12 ay sonrasi {:.2f}".format(k["cari_ay_sonu"], k["2026_sonu"], k["12_ay_sonrasi"]))
    L.append("   Beklenen kur artisi: 2026 {:.1f}%; onumuzdeki 12 ay {:.1f}%; Aralik 2026 -> Eylul 2027 {:.1f}% (9 ay), yillik {:.1f}%".format(d26, d12, d27_9ay, d27))
    L.append("   Model kurali kur_t = oran*TUFE_t-1 (oran 0,5-0,9). Piyasanin ima ettigi oran: 2027 icin {:.1f}/{:.2f} = {:.2f}; onumuzdeki 12 ay icin {:.1f}/{:.2f} = {:.2f}".format(
        d27, E["2026_sonu"], d27 / E["2026_sonu"], d12, TUIK_AGU26, d12 / TUIK_AGU26))
    L.append("   Oran ~0,6: modelin 0,5-0,9 araliginin icinde, 2024-26 gozlemleriyle (0,31, 0,49, 0,63) tutarli.")
    L.append("")

    f = P["politika_faizi"]
    L.append("4. POLITIKA FAIZI beklentisi: simdi {:.2f}, 2026 sonu {:.2f}, 12 ay sonrasi {:.2f}, 24 ay sonrasi {:.2f}".format(f["ilk_toplanti"], f["2026_sonu"], f["12_ay_sonrasi"], f["24_ay_sonrasi"]))
    L.append("   Ex-ante reel faiz (politika faizi - 12 ay sonrasi TUFE beklentisi): bugun {:.1f}, 12 ay sonra {:.1f} ({:.2f} - {:.2f})".format(
        f["ilk_toplanti"] - E["12_ay_sonrasi"], f["12_ay_sonrasi"] - E["24_ay_sonrasi"], f["12_ay_sonrasi"], E["24_ay_sonrasi"]))
    L.append("   Carry 2026 = faiz ~37 - kur artisi ~{:.0f}% = ~{:.0f} puan: borc_doviz faiz26 priori guncellendi (35-40).".format(d26, f["ilk_toplanti"] - d26))
    L.append("")
    c = P["cari_islemler_mlr_usd"]
    L.append("5. CARI ACIK beklentisi: 2026 {:.1f}, 2027 {:.1f} mlr $ (OVP: -47,5 / -38,5): piyasa OVP'den {:.1f} / {:.1f} mlr $ daha kotumser.".format(
        c["2026"], c["2027"], c["2026"] - (-47.5), c["2027"] - (-38.5)))
    return "\n".join(L)


def testler():
    out = []
    r = E["24_ay_sonrasi"] / E["12_ay_sonrasi"]
    out.append(("T-B1 beklenen kalicilik {:.2f}; gerceklesen 0,67-0,74. Beklenti biraz daha YUKSEK kalicilik varsayiyor (+{:.2f})".format(r, r - 0.74),
                abs(r - 0.70) < 0.10, "beklentiler ataleti iceriyor, hedefe cakili degil"))
    out.append(("T-B2 24 ay beklenti {:.1f} hedefin ({:.0f}) ustunde: capa yok".format(E["24_ay_sonrasi"], TCMB_HEDEF), E["24_ay_sonrasi"] - TCMB_HEDEF > 8, "kredibilite"))
    d_kur = (P["kur"]["cari_ay_sonu"] / 49.1174 - 1) * 100
    out.append(("T-B3 PKA cari ay kuru {:.2f} gozlemle (6 Eki 49,12) tutarli: fark %{:.1f}".format(P["kur"]["cari_ay_sonu"], d_kur), abs(d_kur) < 1.0, "veri tutarliligi"))
    out.append(("T-B4 PKA 2026 sonu {:.2f} Agustos yilligi {:.2f}'in altinda: beklenen dezenflasyon {:.1f} puan".format(E["2026_sonu"], TUIK_AGU26, TUIK_AGU26 - E["2026_sonu"]), E["2026_sonu"] < TUIK_AGU26, "yil icinde dusus bekleniyor"))
    out.append(("T-B5 PKA bir beklenti, tahmin degil; 67 katilimci, 52 finansal. Beklentiler gerceklesenden sistematik sapabilir (OVP gibi)", None, "BILGI"))
    out.append(("T-B6 'uzun vade' sutun basligi PDF'de kesik (12,09), yorum disi birakildi", None, "BILGI"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (beklenti)"]
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
