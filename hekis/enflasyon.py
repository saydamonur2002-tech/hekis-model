"""Uc ikincil kanal cozulurse enflasyon kac puan duser.

    python -m hekis.enflasyon

Bu bir tahmin degil, katki ayristirmasidir. Her kanal ayri bir yil-1 puan
katkisi uretir. Gozlem, turetilmis ve varsayim ayri etiketlenir. Varsayimlar
nokta degil aralik olarak cekilir (Monte Carlo, sabit tohum).

Kanallar:
  A  konutun sermaye araci olmasi -> kira (TUFE'de yalniz kira var, fiyat yok)
  B  tedarik zinciri kilidi (alacak/verecek) -> mahsup
  C  asiri ic borclanma, dusuk kamusal verimlilik -> talep ve faiz

Doviz kisiti burada YOK. Ana neden olarak kabul edilir, kalan olarak raporlanir.
"""

import random
import statistics

# ---- GOZLEM (repo verisi) -------------------------------------------------
TUFE_YILLIK = 0.315          # TUIK Agustos 2026
GSYH = 63021.0               # milyar TL, 2025 (tek-sistem RAPOR)
TICARI_STOK = 17302.0        # milyar TL, 2025 (Kredi_Akisi.csv)
TICARI_AKIS = 5208.0         # milyar TL, 2025
FINANSMAN_GIDERI = 4300.0    # milyar TL, 2025 firma finansman gideri
IHTIYAC_STOK = 3065.7        # milyar TL, ticari ihtiyac kredisi (Olcum.csv)
BUTCE_FAIZI = 2054.0         # milyar TL, 2025

# ---- DISARIDAN (arama ile, ham seri indirilemedi: TCMB/EVDS ag politikasiyla kapali) ----
# TCMB: sepet kuru %10 artarsa maliyet kaynakli 1 yillik TUFE etkisi ~2,5 puan.
# Mekanik ithal icerik ~3,3 puan. Beklentiler dahil 6 ay kosullu manset ~6,6 puan.
# Kur: Drive V21 notu yil sonu 2023 29,40 / 2024 35,22 / 2025 42,88 -> 2024 %19,8, 2025 %21,7.
# 2026 artisi %20-28 VARSAYIM (JPM yil sonu 53,5 beklentisi ~%25). Kalibrasyon: hekis/kalibre.py
# (TUFE ~ kur + onceki yil TUFE, 10 gozlem): ayni yil geciskenlik 0,43 (se 0,16), atalet 0,68 (se 0,16).

# ---- TURETILMIS -----------------------------------------------------------
R_EFEKTIF = FINANSMAN_GIDERI / TICARI_STOK      # ~%24,9 efektif firma faizi
IHTIYAC_PAY = IHTIYAC_STOK / TICARI_STOK        # ~%17,7, kilit kredisi icin ust tutarlilik cercevesi

N = 20000
TOHUM = 2026


def cek(rng):
    """Bir senaryo icin tum belirsiz parametreleri cek. Hepsi VARSAYIM."""
    return {
        # A kira
        "w_kira": rng.uniform(0.04, 0.075),       # kira TUFE agirligi. 2026 konut grubu %11,40 (2025: %15,21), elektrik-gaz-su dusulunce kira <= ~%7. Dogrulanmadi, VARSAYIM
        "r_kira": rng.uniform(0.42, 0.55),        # TUFE kira yillik; konut grubu Agu 2026 %39,8, TCMB mevcut kiraci Sub 2026 %53,9 / yeni kiraci %34,2
        "yapisal": rng.uniform(-0.02, 0.04),      # stok cozulse de kalacak reel kira artisi
        "bosluk_pay": rng.uniform(0.15, 0.60),    # kira priminin ne kadari atil stoktan
        "kiralanabilir": rng.uniform(0.20, 0.70), # atil stokun talep olan yerde ve kiralanabilir kismi
        "kira_carpan": rng.uniform(1.2, 2.2),     # ucret/beklenti/hizmet endekslemesi (hane butcesinde kira %26)
        # B mahsup
        "kilit_pay": rng.uniform(0.08, 0.25),     # ticari stokun alacak kilidini fonlayan kismi
        "dongu": rng.uniform(0.20, 0.60),         # kilitli alacagin kapali dongu olan kismi. EN BELIRSIZ SAYI
        "vade_alacak": rng.uniform(0.05, 0.15),   # kilitli ticari alacak / GSYH
        "vade_faiz": rng.uniform(1.0, 1.5),       # fiyata yazilan ortuk vade maliyeti / efektif faiz
        "gecis": rng.uniform(0.30, 0.60),         # firma maliyet dusuklugunun fiyata gecen kismi
        "kredi_talep": rng.uniform(0.20, 0.50),   # kredi akisi / GSYH -> enflasyon puani
        "maliyet_tabani": rng.uniform(1.5, 2.0),  # firma maliyet tabani / GSYH
        # C ic borclanma
        "acik_fazla": rng.triangular(0.3, 2.5, 1.2),  # esik ustu acik, GSYH yuzdesi (low, high, mode)
        "beta": rng.uniform(0.15, 0.50),          # %1 GSYH mali itis basina enflasyon puani (net, verimlilik dahil)
        # D doviz
        "d_yil": rng.uniform(0.16, 0.20),         # dolar/TL yillik artis 2026. GOZLEM: 2 Oca-6 Eki +%14,5, aylik %1,1-2,0, yil sonu tempoyla %17-19 (data/usdtry_2026.json)
        "d_cozum": rng.uniform(0.03, 0.12),       # doviz kisiti cozulunce kalacak yillik deger kaybi
        "phi1": rng.uniform(0.25, 0.55),          # ayni yil geciskenlik: TCMB maliyet 0,25 .. veri 0,43+-0,16
        "ortusme_fx": rng.uniform(0.0, 0.20),     # kurun bir kismi A-C kanallarinin sonucu, cift sayim
        # ortak
        "atalet": rng.uniform(0.35, 0.70),        # gecmis enflasyona endekslenme, veri 0,68+-0,16 (kalibre.py)
        "ortusme": rng.uniform(0.05, 0.30),       # B ve C ayni faiz/kredi hattini sayar, cift sayim payi
    }


def kanallar(p, uygulama=1.0):
    """Yil-1 puan katkisi. uygulama: cozumun ne kadari hayata gecer (0-1)."""
    # A: kira primi, esik: enflasyon + yapisal. Dogrudan ve ikincil.
    prim = max(0.0, p["r_kira"] - (TUFE_YILLIK + p["yapisal"]))
    atfedilen = p["bosluk_pay"] * p["kiralanabilir"]
    # w_kira: kiranin TUFE icindeki payi (konut grubu 0,142'nin alt kalemi)
    a_dogrudan = p["w_kira"] * prim * atfedilen * 100
    a = a_dogrudan * p["kira_carpan"]

    # B: uc ayak. Faiz maliyeti, ortuk vade farki, kredi talebi.
    kilitli_kredi = TICARI_STOK * p["kilit_pay"]
    b_faiz = kilitli_kredi * p["dongu"] * R_EFEKTIF * p["gecis"]
    b_vade = (GSYH * p["vade_alacak"]) * p["dongu"] * R_EFEKTIF * p["vade_faiz"] * p["gecis"]
    b_maliyet = (b_faiz + b_vade) / (GSYH * p["maliyet_tabani"]) * 100
    b_talep = (TICARI_AKIS * p["kilit_pay"] * p["dongu"]) / GSYH * p["kredi_talep"] * 100
    b = b_maliyet + b_talep

    # C: esik ustu acik.
    c = p["acik_fazla"] * p["beta"]

    toplam = (a + b + c) * (1.0 - p["ortusme"])
    k = p["ortusme"]

    # D: doviz. Kur artisi cozum rejiminde d_cozum'a iner. Ayni yil geciskenligi
    # yil 1'de, gecikmeli etki atalet uzerinden yil 2-3'te gelir (A-C ile ayni yil3 kurali).
    fark = max(0.0, p["d_yil"] - p["d_cozum"])
    d1 = p["phi1"] * fark * 100
    d3 = yil3(p, d1)
    cift = 1.0 - p["ortusme_fx"]
    return {
        "D doviz": d1 * cift * uygulama,
        "D doviz y3": d3 * cift * uygulama,
        "hepsi": (toplam + d1 * cift) * uygulama,
        "A kira": a * uygulama,
        "B mahsup": b * uygulama,
        "C ic borc": c * uygulama,
        "toplam": toplam * uygulama,
        "ortusme": k,
    }


def yil3(p, y1):
    """Ataletle 3 yilda birikim. Katki her yil tekrar eder, endeksleme tasir."""
    w = p["atalet"]
    return y1 * (1 + w + w * w)


def yuzdelik(v, q):
    v = sorted(v)
    return v[min(len(v) - 1, int(q * len(v)))]


def spearman(x, y):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for i, j in enumerate(o):
            r[j] = float(i)
        return r
    rx, ry = rank(x), rank(y)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    sx = sum((a - mx) ** 2 for a in rx) ** 0.5
    sy = sum((b - my) ** 2 for b in ry) ** 0.5
    return sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / (sx * sy)


def kos(n=N, tohum=TOHUM):
    rng = random.Random(tohum)
    draws = [cek(rng) for _ in range(n)]
    sonuc = [kanallar(p) for p in draws]
    return draws, sonuc


def rapor() -> str:
    draws, sonuc = kos()
    satir = []
    satir.append("Enflasyon: uc ikincil kanal cozulurse (yil-1 puan, TUFE %31,5 uzerinden)")
    satir.append("Aralik p10 / medyan / p90. Tam cozum = uygulama %100.")
    satir.append("")
    satir.append("{:<12}{:>8}{:>10}{:>8}".format("kanal", "p10", "medyan", "p90"))
    for ad in ("A kira", "B mahsup", "C ic borc", "toplam"):
        v = [s[ad] for s in sonuc]
        satir.append("{:<12}{:>8.2f}{:>10.2f}{:>8.2f}".format(
            ad, yuzdelik(v, 0.10), statistics.median(v), yuzdelik(v, 0.90)))
    satir.append("")

    tot = [s["toplam"] for s in sonuc]
    t3 = [yil3(p, s["toplam"]) for p, s in zip(draws, sonuc)]
    yarim = [0.5 * s["toplam"] for s in sonuc]
    yarim3 = [0.5 * yil3(p, s["toplam"]) for p, s in zip(draws, sonuc)]
    satir.append("Toplam, farkli hikayeler:")
    for ad, v in (("Tam cozum, yil 1", tot), ("Tam cozum, yil 3", t3),
                  ("Yarim uygulama, yil 1", yarim), ("Yarim uygulama, yil 3", yarim3)):
        satir.append("  {:<24}{:>6.2f}  [{:.2f} - {:.2f}]".format(
            ad, statistics.median(v), yuzdelik(v, 0.10), yuzdelik(v, 0.90)))
    satir.append("")
    kal = statistics.median(t3)
    satir.append("Tam cozum yil 3 sonrasi kalan: %{:.1f} (doviz, beklenti, ucret ataleti, yonetilen fiyat)".format(
        TUFE_YILLIK * 100 - kal))
    satir.append("")

    satir.append("Neyi surukluyor? Spearman, ikincil toplam ile parametre:")
    adlar = list(draws[0].keys())
    skor = sorted(((spearman([p[a] for p in draws], tot), a) for a in adlar), key=lambda t: -abs(t[0]))
    for r, a in skor[:7]:
        satir.append("  {:<16}{:>7.2f}".format(a, r))
    satir.append("")

    satir.extend(_doviz_blogu(draws, sonuc))
    return "\n".join(satir)


def _doviz_blogu(draws, sonuc):
    """Doviz kanali ve butun resim. Yil 3 = ikincil y3 + doviz y3, cift sayim dusulmus."""
    satir = ["== DOVIZ KANALI EKLENIRSE (hepsi birlikte cozulurse) =="]
    d1 = [s["D doviz"] for s in sonuc]
    d3 = [s["D doviz y3"] for s in sonuc]
    h1 = [s["hepsi"] for s in sonuc]
    h3 = [yil3(p, s["toplam"]) + s["D doviz y3"] for p, s in zip(draws, sonuc)]
    for ad, v in (("D doviz, yil 1", d1), ("D doviz, yil 3", d3),
                  ("HEPSI, yil 1", h1), ("HEPSI, yil 3", h3)):
        satir.append("  {:<18}{:>6.2f}  [{:.2f} - {:.2f}]".format(
            ad, statistics.median(v), yuzdelik(v, 0.10), yuzdelik(v, 0.90)))
    satir.append("")
    for ad, v in (("yil 1", h1), ("yil 3", h3)):
        satir.append("  Baslangic %{:.1f}, {} sonrasi: %{:.1f}  [%{:.1f} - %{:.1f}]".format(
            TUFE_YILLIK * 100, ad, TUFE_YILLIK * 100 - statistics.median(v),
            TUFE_YILLIK * 100 - yuzdelik(v, 0.90), TUFE_YILLIK * 100 - yuzdelik(v, 0.10)))
    satir.append("")
    satir.append("Hepsini surukleyen:")
    skor = sorted(((spearman([p[a] for p in draws], h3), a) for a in draws[0]), key=lambda t: -abs(t[0]))
    for r, a in skor[:6]:
        satir.append("  {:<16}{:>7.2f}".format(a, r))
    return satir


def main() -> int:
    print(rapor())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
