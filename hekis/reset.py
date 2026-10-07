"""Resetleme: atalet (endeksleme) kirilirsa enflasyon yolu.

    python -m hekis.reset

Fikir: enflasyonun buyuk kismi atalet (TUFE_t ~ 0,68 * TUFE_t-1). Atalet maliyet degil, nominal alisкanlik:
kira, ucret, kamu fiyatlari ve beklentiler gecmis enflasyona endeksli. Koordineli bir 'reset' (ileriye donuk
endeksleme, ucret-fiyat-kira birlikte hedefe cekilir) rho'yu dusururse ne olur?

Bu bir MEKANIK sonuc degil, SENARYO: rho'nun dusebilecegini model bilmez, veri gostermez. Burada rho'nun
dusuk deger aldigi varsayilir ve sonuc sorulur. Ters soru da sorulur: OVP yolu icin rho ne olmali.

Model cekirdegi ovp.py ile ayni (TUFE_t = a + b*kur_t + rho_t*TUFE_t-1 + delta, delta 2026'ya cipali).
Uluslararasi vakalar hafizadan, dogrulanmadi.
"""

import random
import statistics

from hekis.enflasyon import TOHUM, yuzdelik
from hekis.ovp import OVP, TCMB, boot_coef, YILLAR

BAZ_YIL = 2026


def yol(coef, oran, d26, delta, rho_yil, J=None):
    """rho_yil: yil -> rho carpani (None = tahmin edilen rho). J: {yil: kur sicramasi}."""
    a, b, rho = coef
    pi = 30.9
    out = {}
    for t in YILLAR:
        r = rho if rho_yil.get(t) is None else rho_yil[t]
        d = d26 if t == 2026 else oran * pi
        if J and t in J:
            d += J[t]
        pi = max(3.0, a + b * d + r * pi + delta)
        out[t] = pi
    return out


def senaryolar(n=3000, tohum=TOHUM):
    rng = random.Random(tohum)
    pool = boot_coef(n)
    S = {"baz": [], "reset_basarili": [], "reset_yari": [], "reset_sonra_kirilma": []}
    req = {"OVP": [], "TCMB": []}
    for coef in pool:
        a, b, rho = coef
        oran = rng.uniform(0.5, 0.9)
        d26 = rng.uniform(16, 20)
        delta = 28.0 - (a + b * d26 + rho * 30.9) + rng.gauss(0.0, 1.0)   # cipa: 2026 = TCMB 28
        rl = rng.uniform(0.10, 0.35)       # reset sonrasi atalet (VARSAYIM)
        ro = rng.uniform(0.2, 0.5)         # reset sonrasi kur kaymasi/TUFE orani (cipalama)
        S["baz"].append(yol(coef, oran, d26, delta, {}))
        S["reset_basarili"].append(yol(coef, ro, d26, delta, {2027: rl, 2028: rl, 2029: rl}))
        S["reset_yari"].append(yol(coef, ro, d26, delta, {2027: rl, 2028: None, 2029: None}))
        S["reset_sonra_kirilma"].append(yol(coef, ro, d26, delta, {2027: rl, 2028: None, 2029: None}, J={2028: rng.uniform(15, 50)}))
        # ters: resmi yol icin gereken rho (kur kurali baz oran, kalinti cipali)
        for ad, hedef in (("OVP", OVP), ("TCMB", TCMB)):
            onc = 28.0 if hedef[2026] == 28.0 else hedef[2026]
            row = {}
            for t in sorted(hedef):
                if t == 2026:
                    onc = hedef[2026]
                    continue
                d = oran * onc
                row[t] = (hedef[t] - a - b * d - delta) / onc
                onc = hedef[t]
            req[ad].append(row)
    return S, req


def f(v):
    return "{:.1f} [{:.1f}-{:.1f}]".format(statistics.median(v), yuzdelik(v, .1), yuzdelik(v, .9))


def rapor() -> str:
    S, req = senaryolar()
    L = ["RESETLEME: ATALET KIRILIRSA ENFLASYON YOLU (yil sonu TUFE %, medyan [p10-p90])", ""]
    L.append("  yil    BAZ (rho~0,68)           RESET BASARILI           RESET YARI (1 yil)       RESET + 2028 KUR KIRILMASI")
    for t in YILLAR:
        L.append("  {}   {:<24} {:<24} {:<24} {}".format(t, f([x[t] for x in S["baz"]]), f([x[t] for x in S["reset_basarili"]]),
                                                        f([x[t] for x in S["reset_yari"]]), f([x[t] for x in S["reset_sonra_kirilma"]])))
    L.append("")
    L.append("  resmi:  OVP 2027 {:.1f}, 2028 {:.1f}, 2029 {:.1f};  TCMB 2027 {:.1f}, 2028 {:.1f}".format(OVP[2027], OVP[2028], OVP[2029], TCMB[2027], TCMB[2028]))
    L.append("  reset sonrasi atalet U(0,10-0,35), kur kaymasi/TUFE orani U(0,2-0,5) (VARSAYIM, Turkiye verisinde karsiligi yok)")
    L.append("")
    L.append("TERS SORU: resmi yol icin rho ne olmali (onceki yil resmi hedefte, kalinti 2026 cipali)")
    for ad in ("OVP", "TCMB"):
        yl = sorted(req[ad][0])
        L.append("  {}: ".format(ad) + "   ".join("{} rho={}".format(t, f([r[t] for r in req[ad]])) for t in yl))
    L.append("  tahmin edilen rho: 0,68 (se 0,16); 2024-25 icin ek dezenflasyon kalintisi ~ -6 puan")
    L.append("")
    pb = sum(1 for x in S["reset_basarili"] if x[2027] <= OVP[2027]) / len(S["reset_basarili"])
    p29 = sum(1 for x in S["reset_basarili"] if x[2029] <= OVP[2029]) / len(S["reset_basarili"])
    L.append("  Reset basariliysa OVP'yi tutturma olasiligi: 2027 %{:.0f}, 2029 %{:.0f}".format(100 * pb, 100 * p29))
    L.append("  UYARI: bu olasiliklar ve %3 taban VARSAYIMIN ARITMETIGIDIR (rho'yu 0,1-0,35 yapinca olur), modelin bulgusu degil.")
    L.append("  Model rho'nun dusup dusemeyecegini bilmez: rho davranis ve guvenilirlik sonucu, yani Lucas elestirisi. Bu tablo")
    L.append("  'atalet gerceksa reset ne yapar' sorusunun hesabi, 'reset calisir' kaniti degil. Geri tepme (talep, bastirilmis goreli fiyat) yok.")
    L.append("")
    L.append("KURUMSAL ENDEKSLEME (dogrulandi): konut kirasi artisi yasal olarak 12 aylik ortalama TUFE ile sinirli (TBK).")
    L.append("  Yani kira, gecmis enflasyona yasayla baglanmis. Ileriye donuk endeksleme (hedefe) bu kanali kirar.")
    L.append("")
    L.append("KOSULLAR (hafizadan, dogrulanmadi): Israil 1985 (basarili: mali sikilastirma + kur capasi + ucret fiyat dondurma),")
    L.append("  Brezilya Real 1994 (basarili, URV ile endeksleme sifirlama), Cruzado 1986 (basarisiz, mali gevsek + talep patlamasi),")
    L.append("  Arjantin Austral 1985 (gecici). Ortak sart: mali itis dusuk, dis capa guvenilir, koordinasyon.")
    L.append("  Turkiye'de bugun: acik/GSYH OVP'de 2027'de 3,1 -> 3,5; altin-disi net likit 7,8 mlr $; OVP gecmis hatasi ~+12 puan.")
    return "\n".join(L)


def testler():
    out = []
    S, req = senaryolar(1500)
    rb = statistics.median(x[2029] for x in S["reset_basarili"])
    bz = statistics.median(x[2029] for x in S["baz"])
    out.append(("T-S1 reset basariliysa 2029 {:.1f} vs baz {:.1f}: kazanc {:.1f} puan. VARSAYIMA bagli (rho dususu)".format(rb, bz, bz - rb), None, "BILGI: rho dususu veriden tahmin edilmedi"))
    r27 = statistics.median(r[2027] for r in req["OVP"])
    out.append(("T-S2 OVP 2027 icin gereken rho {:.2f}, tahmin edilen 0,68 (se 0,16): fark {:.1f} se. OVP yolu ataletin ~%{:.0f} dusmesini istiyor".format(r27, (0.68 - r27) / 0.16, 100 * (0.68 - r27) / 0.68),
                (0.68 - r27) / 0.16 < 2.0, "2 standart hatadan azsa OVP istatistiksel olarak makul"))
    r27t = statistics.median(r[2027] for r in req["TCMB"])
    out.append(("T-S3 TCMB 2027 (%15) icin gereken rho {:.2f}: tahmin edilen 0,68'den {:.1f} se uzak".format(r27t, (0.68 - r27t) / 0.16),
                (0.68 - r27t) / 0.16 < 2.0, "tarihte en dusuk atalet donemi gorulmedi"))
    out.append(("T-S4 Atalet 'maliyet degil nominal aliskanlik' mi, yoksa gecmis kur soklari, kredibilite ve beklenti kaybinin mirasi mi: bu veriyle ayrisamaz (rho tek sayi)", None, "BILGI: ucret, kira, beklenti serisi gerek"))
    out.append(("T-S5 uluslararasi vakalar hafizadan, dogrulanmadi", None, "BILGI"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (reset)"]
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
