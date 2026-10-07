"""TUIK TUFE metod kirilimlari: ne kirildi, modele ne yapar.

    python -m hekis.metod

Kaynak: (1) BIRINCIL: TUIK Kamuoyu Duyurusu 30.10.2025 (data/TUIK_DUYURU_30102025.md), ilke duzeyi: baz, siniflama,
agirlik kaynagi, "manset seri degismiyor". (2) Agirlik, madde ve grup sayilari arama ozetlerinden (TUIK/TCMB siteleri
bu ortamdan acilamadi). Guven duzeyi her satirda yazili.
"""

import random
import statistics

from hekis.enflasyon import TUFE_YILLIK, cek, kanallar, yuzdelik

# ---- KIRILIM KATALOGU -------------------------------------------------------------
KIRILIMLAR = [
    # (tarih, ne, etki, guven)
    ("2014", "TUFE 2010 bazli endekse gecis, 2003=100 ve 1983 TEFE'ye baglandi", "zincirleme, seviye surekli", "orta (arama ozeti)"),
    ("Nisan 2022", "TUIK urun bazli fiyatlari yayimlamayi birakti", "olcum degil dogrulanabilirlik kirilimi", "orta (arama ozeti)"),
    ("2024 bulteni", "2014-2023 bulten tablolari Eurostat metodolojisine gore revize", "yayin tablolari, endeks degil", "orta"),
    ("Ocak 2026", "baz 2003=100 -> 2025=100; COICOP -> ECOICOP v2; 12 -> 13 ana grup; 407 -> 428 madde; "
                  "grup agirliklari HBA -> Ulusal Hesaplar HHNTH", "bkz. asagi", "YUKSEK ilke (birincil duyuru), orta sayilar (arama ozeti)"),
    ("Ocak 2026", "TUIK beyani: 2003=100 donemi manset gostergelerde DEGISIKLIK YOK, zincir yapi korunur; yalniz bazi ALT endekslerde "
                  "siniflama kaynakli farklar. Agirlik kaynagi AB tarafindan zorunlu (HICP), takdire bagli degil", "manset seri surekli; alt endeks karsilastirilamaz", "YUKSEK (birincil)"),
]

AGIRLIK_2025_2026 = {   # grup: (2025, 2026), yuzde. 2025 yalniz arama ozetinde verilenler.
    "Gida ve alkolsuz icecek": (24.96, 24.44),
    "Konut, su, elektrik, gaz": (15.21, 11.40),
    "Ulastirma": (15.34, 16.62),
}
AGIRLIK_2026_DIGER = {
    "Alkollu icecek ve tutun": 2.75, "Saglik": 2.79, "Bilgi ve iletisim": 3.10, "Egitim": 2.02,
    "Giyim ve ayakkabi": 7.90, "Lokanta ve konaklama": 11.13, "Sigorta ve finansal hizmet (YENI)": 1.07,
}
# Agustos 2026 yillik degisim ve katki (arama ozeti, TUIK bulteni aktarimi)
AGU26 = {"Gida ve alkolsuz icecek": (33.79, 8.12), "Ulastirma": (35.08, 5.94), "Konut, su, elektrik, gaz": (39.77, 5.01)}
TCMB_ETKI = {"agirlik yapisinin Ocak aylik etkisi": -0.1, "hizmet payi artisinin yillik etkisi": +1.0, "mal/hizmet kaymasi (puan)": 7.4}
JAN26 = {"aylik": 4.84, "yillik": 30.65}
ENAG_HAZ26 = {"TUIK": 32.11, "ENAG": 51.49}   # Haziran 2026 yillik, Euronews aktarimi; ENAG'in yontemi ve guvenilirligi tartismali


def rapor() -> str:
    L = ["TUIK TUFE METOD KIRILIMLARI", ""]
    L.append("KIRILIM KATALOGU (ilke: birincil TUIK duyurusu 30.10.2025; sayilar: arama ozetleri)")
    for t, n, e, g in KIRILIMLAR:
        L.append("  {:<11} {}".format(t, n))
        L.append("              etki: {}   [guven: {}]".format(e, g))
    L.append("")
    import json as _json
    import os as _os
    T = _json.load(open(_os.path.join(_os.path.dirname(__file__), "..", "data", "tufe_agirlik_2016_2026.json")))
    AG, KAP = T["agirlik"], T["kapsam"]
    ADL = {"gida": "Gida ve alkolsuz icecek", "alkol_tutun": "Alkollu icecek ve tutun", "giyim": "Giyim ve ayakkabi",
           "konut": "Konut, su, elektrik, gaz", "mobilya": "Mobilya ve ev bakimi", "saglik": "Saglik", "ulastirma": "Ulastirma",
           "bilgi_iletisim": "Bilgi ve iletisim", "eglence_kultur": "Eglence, spor, kultur", "egitim": "Egitim",
           "lokanta_konaklama": "Lokanta ve konaklama", "sigorta_finans": "Sigorta ve finansal hizmet", "kisisel_bakim_diger": "Kisisel bakim ve diger"}
    L.append("AGIRLIK DEGISIMI 2025 -> 2026 (yuzde), BIRINCIL KAYNAK: TUIK ana grup agirliklari tablosu (COICOP 2018, 2025=100)")
    for k, ad in ADL.items():
        L.append("  {:<28}{:>7.2f} -> {:>6.2f}  ({:+.2f})".format(ad, AG[k]["2025"], AG[k]["2026"], AG[k]["2026"] - AG[k]["2025"]))
    L.append("  Toplam 2025 {:.2f}, 2026 {:.2f}".format(sum(AG[k]["2025"] for k in AG), sum(AG[k]["2026"] for k in AG)))
    hiz = sum(AG[k]["2026"] - AG[k]["2025"] for k in ("lokanta_konaklama", "eglence_kultur", "sigorta_finans"))
    L.append("  Konut -3,86 puan; lokanta+konaklama +2,82, eglence-kultur +2,21, sigorta-finans +0,82: hizmet-agirlikli gruplar toplam +{:.2f} puan".format(hiz))
    L.append("  Konut agirligi 2016-2025: " + ", ".join("{:.1f}".format(AG["konut"][str(y)]) for y in range(2016, 2026)) + " -> 2026 {:.1f} (uzun donem ort ~15, 2026 dusus kirilim)".format(AG["konut"]["2026"]))
    L.append("  Kapsam 2025 -> 2026: madde {:.0f} -> {:.0f}, isyeri {:.0f} -> {:.0f}, fiyat {:.0f} -> {:.0f}, KIRA SAYISI {:.0f} -> {:.0f} (2023'ten beri 5.246, 2016-22: 4.274)".format(
        KAP["madde"]["2025"], KAP["madde"]["2026"], KAP["isyeri"]["2025"], KAP["isyeri"]["2026"], KAP["fiyat"]["2025"], KAP["fiyat"]["2026"], KAP["kira_sayisi"]["2025"], KAP["kira_sayisi"]["2026"]))
    L.append("  NOT: kira kaleminin kendi agirligi bu tabloda YOK (yalniz 2 haneli grup). Kira ornegi yalniz 5.246 sozlesme.")
    L.append("")
    L.append("TCMB DEGERLENDIRMESI (arama ozeti): agirlik yapisi Ocak enflasyonunu ~{:+.1f} puan etkiler; hizmet payi artisi yillik enflasyona ~{:+.1f} puan (mal-hizmet kaymasi {:.1f} puan)".format(
        TCMB_ETKI["agirlik yapisinin Ocak aylik etkisi"], TCMB_ETKI["hizmet payi artisinin yillik etkisi"], TCMB_ETKI["mal/hizmet kaymasi (puan)"]))
    L.append("TUIK: baz gecisinde aylik ve yillik oranlar zincirleme, gecmis seri kirilmadi. Ocak 2026 aylik %{:.2f}, yillik %{:.2f}.".format(JAN26["aylik"], JAN26["yillik"]))
    L.append("")

    # Agustos 2026 ayristirma
    L.append("AGUSTOS 2026 KATKI AYRISTIRMASI (yillik %31,51)")
    L.append("  grup                         yillik   katki   efektif agirlik(katki/yillik)")
    toplam_k, toplam_w = 0.0, 0.0
    for g, (y, k) in AGU26.items():
        L.append("  {:<28}{:>7.2f}{:>8.2f}   %{:.1f}".format(g, y, k, 100 * k / y))
        toplam_k += k
        toplam_w += k / y
    konut_y, konut_k = AGU26["Konut, su, elektrik, gaz"]
    w_konut = konut_k / konut_y
    tufe = 31.51
    fark = konut_k - w_konut * tufe
    L.append("  3 grubun katkisi {:.2f} puan (toplamin %{:.0f}'i), efektif agirlik toplami %{:.1f}".format(toplam_k, 100 * toplam_k / tufe, 100 * toplam_w))
    L.append("  Konut grubu genel enflasyon hizinda artsaydi katki {:.2f}; gercek {:.2f}: genel ustu fazla = {:.2f} puan".format(w_konut * tufe, konut_k, fark))
    L.append("  (grup elektrik, gaz, su, bakim da icerir: kira tek basina bu fazlanin altindadir)")
    L.append("")

    # A kanali ust siniri
    rng = random.Random(2026)
    a_dir = []
    for _ in range(20000):
        p = cek(rng)
        prim = max(0.0, p["r_kira"] - (TUFE_YILLIK + p["yapisal"]))
        a_dir.append(p["w_kira"] * prim * p["bosluk_pay"] * p["kiralanabilir"] * 100)
    asma = sum(1 for x in a_dir if x > fark) / len(a_dir)
    L.append("A KANALI UST SINIR TESTI: dogrudan A katkisi (haircut oncesi, kira carpani oncesi) medyan {:.2f} [{:.2f}-{:.2f}], konut fazlasi {:.2f}'i asma olasiligi %{:.1f}".format(
        statistics.median(a_dir), yuzdelik(a_dir, .1), yuzdelik(a_dir, .9), fark, 100 * asma))
    # tam bos stok cozumu: konutun tum primi kapanirsa
    tam = []
    rng = random.Random(7)
    for _ in range(20000):
        p = cek(rng)
        prim = max(0.0, p["r_kira"] - (TUFE_YILLIK + p["yapisal"]))
        tam.append(p["w_kira"] * prim * 100)
    L.append("  Kira tam adil duzeye insaydi (atif payi 1): dogrudan {:.2f} [{:.2f}-{:.2f}] puan; konut grubu fazlasi {:.2f}".format(
        statistics.median(tam), yuzdelik(tam, .1), yuzdelik(tam, .9), fark))
    L.append("")

    # model aciginin kirilim ile ilgisi
    L.append("MODEL ACIGI VE KIRILIM")
    L.append("  gozlenen kur temposuyla model 2026 TUFE ~26.0 (kirilma.py T-K3); gozlem Agustos yillik 31,5. Acik ~5.5 puan.")
    L.append("  TCMB'ye gore hizmet payi artisi ~+1.0 puan: acigin ~%{:.0f}'ini kirilim aciklar. Kalan ~4.5 puan baska surucu.".format(100 * 1.0 / 5.5))
    L.append("  Not: model Aralik/Aralik yilligi kalibre; gozlem Agustos yilligi. Zaman uyumsuzlugu da aciga girer.")
    L.append("  ENAG-TUIK (Haziran 2026): {:.1f} vs {:.1f}, fark {:.1f} puan. ENAG'in yontemi tartismali, olcum belirsizligi siniri olarak yazilir, dogru kabul edilmez.".format(
        ENAG_HAZ26["ENAG"], ENAG_HAZ26["TUIK"], ENAG_HAZ26["ENAG"] - ENAG_HAZ26["TUIK"]))
    return "\n".join(L)


def testler():
    out = []
    import json as _json
    import os as _os
    T = _json.load(open(_os.path.join(_os.path.dirname(__file__), "..", "data", "tufe_agirlik_2016_2026.json")))["agirlik"]
    top25 = sum(T[k]["2025"] for k in T)
    top26 = sum(T[k]["2026"] for k in T)
    out.append(("M1 birincil tablo: agirliklar 2025 {:.2f}, 2026 {:.2f} (100'e toplanmali)".format(top25, top26), abs(top25 - 100) < 0.05 and abs(top26 - 100) < 0.05, "kimlik"))
    # arama ozeti ile birincil tablo uyumu
    fark = max(abs(T["gida"]["2026"] - 24.44), abs(T["konut"]["2026"] - 11.40), abs(T["ulastirma"]["2026"] - 16.62), abs(T["lokanta_konaklama"]["2026"] - 11.13))
    out.append(("M1b arama ozetindeki 2026 agirliklari (24,44 / 11,40 / 16,62 / 11,13) birincil tabloyla tutarli, en buyuk fark {:.2f}".format(fark), fark < 0.02, "onceki ikincil kaynaklar dogru cikti"))
    # efektif agirlik kimligi
    ef = {g: k / y for g, (y, k) in AGU26.items()}
    _base = {"Gida ve alkolsuz icecek": T["gida"]["2026"], "Konut, su, elektrik, gaz": T["konut"]["2026"], "Ulastirma": T["ulastirma"]["2026"]}
    sap = [abs(100 * ef[g] - _base[g]) for g in ef]
    out.append(("M2 katki/yillik = efektif agirlik, baz agirliktan en fazla {:.1f} puan sapti (fiyat kaymasi)".format(max(sap)), max(sap) < 2.5, "kimlik"))
    konut_y, konut_k = AGU26["Konut, su, elektrik, gaz"]
    fark = konut_k - konut_k / konut_y * 31.51
    rng = random.Random(2026)
    asma = 0
    for _ in range(20000):
        p = cek(rng)
        prim = max(0.0, p["r_kira"] - (TUFE_YILLIK + p["yapisal"]))
        if p["w_kira"] * prim * p["bosluk_pay"] * p["kiralanabilir"] * 100 > fark:
            asma += 1
    out.append(("M3 A kanali dogrudan katkisi konut grubunun genel ustu fazlasini ({:.2f} puan) asmiyor: asma olasiligi %{:.1f}".format(fark, 100 * asma / 20000),
                asma / 20000 < 0.01, "ust sinir testi"))
    out.append(("M4 kira kaleminin kendi agirligi TUIK tablosunda YOK (yalniz 2 haneli grup). w_kira 4,0-7,5% hala VARSAYIM, ust sinir konut grubu %11,4 eksi elektrik-gaz-su", None, "BILGI: 4 haneli (COICOP 04.1) agirlik gerek"))
    out.append(("M5 agirlik, madde sayisi ve grup sayisi artik BIRINCIL tabloyla dogrulandi (arama ozetleri dogru cikti). TUIK 2026 metodoloji dokumani ve TCMB analizi hala okunamadi: TCMB'nin '+1 puan hizmet etkisi' ikincil", None, "BILGI"))
    out.append(("M6 alt endeks karsilastirilabilirligi: duyuruya gore alt endekslerde siniflama farki olabilir. Konut grubu 2025 'Konut' (%49,5 yillik, Drive) ile 2026 'Konut, su, elektrik, gaz ve diger yakitlar' (%39,8) ayni kapsam olmayabilir", None, "BILGI: grup duzeyinde 2025-26 kiyasi dikkatle okunmali, manset kiyasi guvenli"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (metod)"]
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
