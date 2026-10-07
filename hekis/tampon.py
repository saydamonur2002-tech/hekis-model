"""Kisa vadeli doviz likidite tamponu ve stres.

    python -m hekis.tampon

Kisa vadeli net pozisyon (varlik - yukumluluk) 2022'de 70 mlr $, 2026-07'de 4,4 mlr $. Tampon bitince
yeniden finansman aksarsa firmalar piyasadan doviz alir: kur baskisi, enflasyona gecis.

Stres (yeniden finansman sorunu): gereken = f_k*(KV banka kredisi) + f_i*(KV ithalat borcu)
  + f_t*max(0, KV turev yukumlulugu - KV turev varligi). Karsilanabilir = l*(mevduat+menkul) + e*ihracat alacagi.
  Piyasaya cikan talep D = max(0, gereken - karsilanabilir). TCMB payi cb karsilar.
  Kur baskisi = eta * (1-cb) * D / GSYH$ * 100 puan. Enflasyon = phi1 * baski, atalet ile 3 yil.
Gozlem: TCMB FKDFDVY (nop_veri). f_k, f_i, f_t, l, e, cb, eta VARSAYIM. Olasilik verilmez, kosullu etki.
"""

import random
import statistics

from hekis.kalibre import KUR
from hekis.enflasyon import TOHUM, cek, yuzdelik
from hekis.nop_veri import CARRY, DEP, DONEM, KV_NET, KV_NET_2026_07, NOP, NOP_2026_07, S, YIL
from hekis.birikim import GSYH_USD
from hekis.borc_doviz import GSYH_USD_2025, RAMPA, aralik, baz_akis, cek_fx, med
import hekis.borc_doviz as bd

DURUMLAR = ("2020-12", "2022-12", "2023-12", "2024-12", "2025-12", "2026-07")


def gsyh_usd(d):
    if d == "2026-07":
        return GSYH_USD_2025 * 1.07 ** (19 / 12)  # 2025 ortalamasindan ~19 ay, GSYH$ %7/yil VARSAYIM
    return GSYH_USD[int(d[:4])]


def durum(d):
    j = DONEM.index(d)
    g = lambda k: S[k][j]
    return {
        "kv_kredi": g("kv_dk_ic") + g("yd_1yil_az"),
        "ithalat": g("ithalat_kv"),
        "turev_net": max(0.0, g("turev_yuk_kv") - g("turev_var_kv")),
        "likit": g("mevduat") + g("menkul"),
        "ihr_alacak": g("ihracat_alacak"),
        "kv_net": g("KV_NET"),
        "nop": -g("NOP"),
    }


def stres_cek(rng):
    return {
        # siddet: tarihin en kotu yillik daralmalari (yurt ici banka dk -19%, ithalat borcu -24%, yd<1yil -32%)
        # ve kuyruk (1,5x). Gozlem: nop_veri / FKDFDVY 2008-2025.
        "f_k": rng.uniform(0.15, 0.35), "f_i": rng.uniform(0.15, 0.40), "f_t": rng.uniform(0.5, 1.0),
        "l": rng.uniform(0.30, 0.70), "e": rng.uniform(0.20, 0.50),
        "cb": rng.uniform(0.3, 0.9), "eta": rng.uniform(1.0, 3.0),
    }


def talep(st, z):
    gereken = z["f_k"] * st["kv_kredi"] + z["f_i"] * st["ithalat"] + z["f_t"] * st["turev_net"]
    karsilanir = z["l"] * st["likit"] + z["e"] * st["ihr_alacak"]
    return max(0.0, gereken - karsilanir), gereken, karsilanir


def enflasyon_etkisi(p, baski):
    """Tek seferlik kur baskisi (puan). Yil 1, 2, 3 TUFE artisi (puan), atalet ile."""
    e1 = p["phi1"] * baski
    return [e1, e1 * p["atalet"], e1 * p["atalet"] ** 2]


def ters_stres(d, n=4000, tohum=TOHUM):
    """Kirilma orani: yeniden finansman kaybi (butun KV kalemlerine esit f) kac olunca D>0 olur."""
    rng = random.Random(tohum)
    st = durum(d)
    out = []
    for _ in range(n):
        z = stres_cek(rng)
        kars = z["l"] * st["likit"] + z["e"] * st["ihr_alacak"]
        pay = st["kv_kredi"] + st["ithalat"] + z["f_t"] * st["turev_net"]
        out.append(kars / pay)
    return out


def kos(d, n=4000, tohum=TOHUM):
    rng = random.Random(tohum)           # ayni cekimler butun durumlarda, adil karsilastirma
    st = durum(d)
    g = gsyh_usd(d)
    out = []
    for _ in range(n):
        z = stres_cek(rng)
        p = cek(rng)
        D, gerek, kars = talep(st, z)
        net = (1 - z["cb"]) * D
        baski = z["eta"] * net / g * 100
        out.append((D, net, baski, enflasyon_etkisi(p, baski)))
    return out


def rapor() -> str:
    L = ["LIKIDITE TAMPONU VE STRES (kosullu etki: yeniden finansman aksarsa)", ""]
    L.append("Kisa vadeli kalemler (TCMB FKDFDVY, mlr $)")
    L.append("  donem     KV net  KV banka krd  KV ithalat  net turev(a)  likit varlik  ihr.alacak")
    for d in DURUMLAR:
        st = durum(d)
        L.append("  {:<8}{:>7.1f}{:>12.1f}{:>12.1f}{:>12.1f}{:>13.1f}{:>12.1f}".format(
            d, st["kv_net"], st["kv_kredi"], st["ithalat"], st["turev_net"], st["likit"], st["ihr_alacak"]))
    L.append("  (a) KV turev yukumlulugu - KV turev varligi, negatifse 0")
    L.append("")
    L.append("Ayni stres cekimleri (f_k %15-35, f_i %15-40: tarihin en kotu daralmalari ve kuyrugu) her durumda:")
    L.append("  donem     P(D>0)   D medyan   kur baskisi puan   TUFE artisi yil1  yil2  yil3 (medyan)")
    for d in DURUMLAR:
        o = kos(d)
        pd_ = sum(1 for x in o if x[0] > 0) / len(o)
        L.append("  {:<8}  %{:>4.0f}  {:>8.1f}  {:>8.1f} [{:>4.1f}-{:>4.1f}]   {:>6.2f} {:>5.2f} {:>5.2f}".format(
            d, 100 * pd_, med([x[0] for x in o]), med([x[2] for x in o]), yuzdelik([x[2] for x in o], .1), yuzdelik([x[2] for x in o], .9),
            med([x[3][0] for x in o]), med([x[3][1] for x in o]), med([x[3][2] for x in o])))
    L.append("")
    L.append("TERS STRES: butun kisa vadeli kalemlerde yeniden finansman kaybi kac olunca tampon tukenir (f*)")
    L.append("  donem      f* medyan [p10-p90]   tarihin en kotusune (-%24) oran")
    for d in DURUMLAR:
        f = ters_stres(d)
        L.append("  {:<8}   %{:>4.0f}  [{:.0f}-{:.0f}]           {:.1f}x".format(d, 100 * med(f), 100 * yuzdelik(f, .1), 100 * yuzdelik(f, .9), med(f) / 0.24))
    L.append("")
    o22, o26 = kos("2022-12"), kos("2026-07")
    fark = [b[3][0] - a[3][0] for a, b in zip(o22, o26)]
    L.append("Tampon 2022'den 2026-07'ye erimeseydi (ayni stres): yil-1 TUFE artisi farki medyan {:.2f} puan [{}]".format(med(fark), aralik(fark)))
    L.append("")

    # ileri: tampon yolu, baz ve cozum
    psi = S["KV_YUK"][-1] / S["YUKUMLULUK"][-1]
    L.append("TAMPON YOLU 2026-30 (psi = yeni yukumlulugun kisa vadeli payi {:.2f}, nu 0-0,3 varlik karsiligi)".format(psi))
    pay_r = RAMPA["yavas"]
    for rj in ("tam", "son2yil"):
        bd.REJIM = rj
        rng = random.Random(TOHUM + 3)
        yb, ys = [], []
        for _ in range(3000):
            p, q = cek_fx(rng)
            f0 = baz_akis(p, q)
            pay = q["sA"] + q["sB"] + q["sC"]
            nu = rng.uniform(0.0, 0.3)   # yeni borcun kisa vadeli varliga donusen kismi (2022-26: ~0)
            cb_, cs_ = 0.0, 0.0
            rb, rs = [], []
            for t in range(5):
                cb_ += f0[t]
                cs_ += f0[t] * (1 - pay * pay_r[t])
                rb.append(KV_NET_2026_07 - (psi - nu) * cb_)
                rs.append(KV_NET_2026_07 - (psi - nu) * cs_)
            yb.append(rb); ys.append(rs)
        L.append("  rejim={:<8} yil   " .format(rj) + "".join("{:>8}".format(2026 + t) for t in range(5)))
        L.append("    baz tampon         " + "".join("{:>8.1f}".format(med([x[t] for x in yb])) for t in range(5)))
        L.append("    cozumlu tampon     " + "".join("{:>8.1f}".format(med([x[t] for x in ys])) for t in range(5)))
        L.append("    P(baz tampon<0)    " + "".join("{:>7.0f}%".format(100 * sum(x[t] < 0 for x in yb) / len(yb)) for t in range(5)))
    bd.REJIM = "tam"
    return "\n".join(L)


def testler():
    out = []
    # T-T1: tampon gecmiste kur sokunu onledi mi / sokta eridi mi
    yil = list(range(2016, 2026))
    kv = [KV_NET[t - 1] for t in yil]
    dep = [DEP[t] for t in yil]
    mk, md = statistics.fmean(kv), statistics.fmean(dep)
    cov = sum((a - mk) * (b - md) for a, b in zip(kv, dep))
    r = cov / (sum((a - mk) ** 2 for a in kv) * sum((b - md) ** 2 for b in dep)) ** .5
    out.append(("T-T1 onceki yil tampon ile bu yilki kur artisi korelasyonu {:+.2f} (n=10). Tampon korumadi, kur artisi yuksek tampon yillarini izledi".format(r),
                r < -0.3, "koruyucu tampon r<0 verirdi. Tampon sokun oncul gostergesi degil"))
    # T-T2: sok yillarinda tampon eridi mi (2018, 2021, 2022)
    d18 = KV_NET[2018] - KV_NET[2017]
    d21 = KV_NET[2021] - KV_NET[2020]
    out.append(("T-T2 sok yillarinda tampon degisimi: 2018 {:+.1f}, 2021 {:+.1f}. Tampon sokta erimedi, sok sonrasi birikti".format(d18, d21),
                d18 > 0 and d21 < 0.5 * abs(d18) + 5, "tampon kriz oncesi degil sonrasi buyuyor: borc cozulmesi ile ayni hareket"))
    # T-T3: 2024'te tampon cokusu nasil
    d24 = KV_NET[2024] - KV_NET[2023]
    out.append(("T-T3 2024 tampon degisimi {:+.1f} mlr $ (66 -> 14,6), NOP bozulmasi +75,6 ile ayni yil".format(d24),
                d24 < -30, "tampon cokusu ve NOP bozulmasi ayni yilda, ayri degil"))
    # T-T4: 2022'de ayni stres tampon yuzunden sifir talep mi
    o22 = kos("2022-12")
    p22 = sum(1 for x in o22 if x[0] > 0) / len(o22)
    o26 = kos("2026-07")
    p26 = sum(1 for x in o26 if x[0] > 0) / len(o26)
    f22, f26 = med(ters_stres("2022-12")), med(ters_stres("2026-07"))
    out.append(("T-T4 stres talep: P(D>0) 2022 %{:.0f}, 2026-07 %{:.0f}. Kirilma orani f*: {:.0f}% -> {:.0f}%".format(100 * p22, 100 * p26, 100 * f22, 100 * f26),
                f26 > 0.24, "f* tarihin en kotu daralmasindan (%24) buyukse tampon yeterli"))
    # T-T5: eta kalibre edilemez
    out.append(("T-T5 eta (kur baskisi / GSYH oranli piyasa talebi) ve cb TCMB rezerv verisi olmadan tanimlanamaz", False, "rezerv serisi gerek"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (tampon)"]
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
