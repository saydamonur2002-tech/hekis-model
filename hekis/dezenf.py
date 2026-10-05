"""Dezenflasyon politikasinin ENFLASYONIST etkisi: politikanin kendi maliyetleri ve borc alinmis kazanci.

    python -m hekis.dezenf

Politika = yuksek reel faiz + kontrollu kur kaymasi (kur cipasi, 2026 yillik ~%19). Iki yuzu var:
  KAZANC  : kur kaymasi enflasyondan yavas -> TUFE'den duser (reduced form: b * (onceki TUFE - kayma))
  MALIYET : (1) firma faiz maliyeti, (2) butce faizi -> mali itis (iç borclanma, C kanali),
            (3) carry -> doviz borcu birikimi -> kirilma riski (beklenen maliyet), (4) kira/yonetilen fiyat telafisi (VERI YOK, olculmedi)
Neti ve geri odemeyi (kirilmada kazancin geri verilmesi) verir.
Bu bir TAHMIN degil, onceki modullerin parametre dagilimiyla katki hesabidir. Faiz maliyeti ve mali kanal parametreleri
(rho_bs, beta) VERIDEN tahmin edilmedi, onsel aralik. Kur kazanci ise 11 yillik regresyondan (b: bootstrap).
"""

import random
import statistics

from hekis.borc_doviz import cek_fx
from hekis.enflasyon import BUTCE_FAIZI, GSYH, TICARI_STOK, TOHUM, yuzdelik
from hekis.kalibre import TUFE
from hekis.ovp import boot_coef

PKA_12AY = 23.70          # PKA Eylul 2026, 12 ay sonrasi beklenti (nominal faiz karsilastirmasi icin)
ONCEKI = TUFE[2025]       # 30.9


def kos(n=4000, tohum=TOHUM):
    rng = random.Random(tohum)
    pool = boot_coef(n)
    S = {"kazanc": [], "faiz": [], "mali": [], "maliyet": [], "net": [], "geri": [], "reel": []}
    for i in range(n):
        p, q = cek_fx(rng)
        a, b, rho = pool[i]
        reel = q["faiz26"] - PKA_12AY               # ex-ante reel faiz, puan
        # kazanc: kur enflasyon kadar kaysaydi (reel kur sabit) vs gozlenen kayma
        kazanc = b * (ONCEKI - p["d_yil"] * 100)
        # firma faiz maliyeti: reel faiz kadar fazla maliyet, TL stok, fiyata gecis
        faiz = q["rho_bs"] * (reel / 100) * TICARI_STOK * q["tl_pay"] / (GSYH * p["maliyet_tabani"]) * 100
        # butce: fazla faiz yuku (reel/nominal oran) -> mali itis
        mali = (BUTCE_FAIZI * q["reprice"] * (reel / max(q["faiz26"], 1.0))) / GSYH * 100 * p["beta"]
        S["kazanc"].append(kazanc); S["faiz"].append(faiz); S["mali"].append(mali)
        S["maliyet"].append(faiz + mali); S["net"].append(kazanc - faiz - mali); S["reel"].append(reel)
        J = rng.uniform(15, 50)
        S["geri"].append(p["phi1"] * J * (1 + p["atalet"] + p["atalet"] ** 2))   # kirilmada 3 yil kum. maliyet
    return S


def f(v):
    return "{:.1f} [{:.1f}-{:.1f}]".format(statistics.median(v), yuzdelik(v, .1), yuzdelik(v, .9))


def rapor() -> str:
    S = kos()
    L = ["DEZENFLASYON POLITIKASININ ENFLASYONIST ETKISI (yillik, puan; medyan [p10-p90])", ""]
    L.append("Politika: politika faizi %35-40, PKA 12 ay beklentisi %{:.1f} -> ex-ante reel faiz {}; kur kaymasi %16-20".format(PKA_12AY, f(S["reel"])))
    L.append("")
    L.append("  KAZANC (kur cipasi, TUFE'yi dusuren):      -{}".format(f(S["kazanc"])))
    L.append("  MALIYET 1 firma faiz maliyeti (fiyata):    +{}".format(f(S["faiz"])))
    L.append("  MALIYET 2 butce faizi / mali itis:         +{}".format(f(S["mali"])))
    L.append("  toplam dogrudan maliyet:                   +{}".format(f(S["maliyet"])))
    L.append("  NET (kazanc - maliyet):                    -{}".format(f(S["net"])))
    L.append("  maliyet / kazanc (medyan): {:.2f}".format(statistics.median(m / k for m, k in zip(S["maliyet"], S["kazanc"]))))
    L.append("")
    L.append("MALIYET 3 (en buyuk): kazanc BORC ALINMIS. Kur cipasi cozulmeyen A+B+C ile carry->doviz borcu uretir; kirilma olursa")
    L.append("  kazanc geri verilir. Kirilmada 3 yil kumulatif TUFE artisi: {} puan; 3 yillik kur kazanci ~ 3 x {:.1f} = {:.1f}".format(
        f(S["geri"]), statistics.median(S["kazanc"]), 3 * statistics.median(S["kazanc"])))
    kg = statistics.median(S["geri"]); k3 = 3 * statistics.median(S["kazanc"])
    for pr in (0.1, 0.25, 0.5):
        L.append("  kirilma olasiligi %{:.0f}: beklenen geri odeme {:.1f} puan  (3 yillik kazancin %{:.0f}'i)".format(100 * pr, pr * kg, 100 * pr * kg / k3))
    L.append("  Bas-basa olasilik: kirilma %{:.0f}'u gecerse kur cipasinin 3 yillik net kazanci SIFIRIN ALTINA doner (kirilma olasiligi bilinmiyor).".format(100 * k3 / kg))
    L.append("")
    L.append("OLCULMEYEN (veri yok): yonetilen fiyat/vergi telafisi (kur cipasi altinda ertelenen zamlar sonra TUFE'ye biner), kira ve hizmet fiyat")
    L.append("  katiligi, talep tarafi etkisi (yuksek faiz talebi dusurur: bu ENFLASYON DUSURUCU, burada sayilmadi), ihracat rekabet gucu kaybi.")
    L.append("  Yani 'maliyet' tarafi alt sinir, 'kazanc' tarafi ise talep kanali eklenince buyur: net etki isaret degistirebilir.")
    return "\n".join(L)


def testler():
    out = []
    S = kos(2000)
    k, m = statistics.median(S["kazanc"]), statistics.median(S["maliyet"])
    out.append(("T-D1 kur kazanci {:.1f} puan, dogrudan maliyet {:.1f}: kazanc maliyetin {:.1f} kati".format(k, m, k / m), None, "BILGI: kazanc karsi-olgusu (kur=TUFE) kasitli uc nokta; oran bu secime bagli"))
    pk = sum(1 for a in S["net"] if a < 0) / len(S["net"])
    out.append(("T-D2 neti negatif cikan cekim orani %{:.0f}".format(100 * pk), None, "BILGI: parametre onseline bagli"))
    k3 = 3 * k; g = statistics.median(S["geri"])
    out.append(("T-D3 3 yillik kur kazanci {:.1f} < kirilma maliyeti {:.1f}: kazanci geri vermek tek kirilmayla mumkun".format(k3, g), None, "BILGI: iki tarafin da varsayima bagli aritmetigi, test degil"))
    out.append(("T-D4 faiz maliyeti ve mali kanal parametreleri (rho_bs, beta) veriden tahmin edilmedi; talep kanali dahil degil", None, "BILGI"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (dezenflasyon politikasi)"]
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
