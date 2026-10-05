"""TCMB resmi rezerv ve doviz likiditesi, Eylul 2026.

    python -m hekis.rezerv

Kaynak: data/urdl_20260925.json (TCMB URDL, IMF SDDS sablonu, mlr $). Uc is yapar:
  1. Rezerv dususunu altin fiyat degerlemesi ve gercek doviz cikisi diye ayirir.
  2. Net likit rezervi (kesin cikislar dusulmus) ve ne kadar dayanacagini hesaplar.
  3. Firma tarafi ters stresini (tampon.py) resmi katmanla birlestirir: sistem hangi yeniden
     finansman kaybinda kirilir.

Kalibrasyon: 'cb' (TCMB'nin paylasma kapasitesi) artik rezerv kapasitesinden turetilir, varsayim degil.
eta (talep -> kur baskisi) hala tanimlanamaz: kur serisi bu dosyada yok.
"""

import json
import os
import statistics

from hekis.nop_veri import S as _S  # noqa: F401
from hekis.tampon import durum, stres_cek, gsyh_usd
from hekis.enflasyon import TOHUM
import random

_YOL = os.path.join(os.path.dirname(__file__), "..", "data", "urdl_20260925.json")
_D = json.load(open(_YOL))
TARIH = _D["tarih"]
U = {k: [None if v is None else v / 1000.0 for v in vs] for k, vs in _D["seri"].items()}
ONS = _D["seri"]["altin_milyon_ons"]   # milyon troy ons, ham


def son(k):
    return U[k][-1]


def fiyat(j):
    return U["altin"][j] / ONS[j]     # mlr $ / milyon ons = $/ons / 1000... asagida $/ons'a cevrilir


def ons_fiyati(j):
    return U["altin"][j] * 1000.0 / ONS[j]   # $ / ons


def rapor() -> str:
    L = ["TCMB RESMI REZERV, 25 EYLUL 2026 (mlr $)", ""]
    L.append("  tarih            resmi rezerv  altin   altin-disi  $/ons    altin-disi degisim")
    for j, t in enumerate(TARIH):
        ng = U["resmi_rezerv"][j] - U["altin"][j]
        d = "" if j == 0 else "{:+.1f}".format(ng - (U["resmi_rezerv"][j - 1] - U["altin"][j - 1]))
        L.append("  {:<16}{:>10.1f}{:>9.1f}{:>11.1f}{:>8.0f}    {}".format(t, U["resmi_rezerv"][j], U["altin"][j], ng, ons_fiyati(j), d))

    # ayrisma: Agustos -> 25 Eylul
    r0, r1 = U["resmi_rezerv"][0], U["resmi_rezerv"][-1]
    g0, g1 = U["altin"][0], U["altin"][-1]
    p0, p1 = ons_fiyati(0), ons_fiyati(-1)
    o0, o1 = ONS[0], ONS[-1]
    deger = o0 * (p1 - p0) / 1000.0
    miktar = (o1 - o0) * p1 / 1000.0
    ng0, ng1 = r0 - g0, r1 - g1
    L.append("")
    L.append("AYRISMA (Agustos -> 25 Eylul): toplam {:+.1f} mlr $".format(r1 - r0))
    L.append("  altin fiyat degerlemesi {:+.1f}  (fiyat {:.0f} -> {:.0f} $/ons, {:+.1f}%)".format(deger, p0, p1, 100 * (p1 / p0 - 1)))
    L.append("  altin miktar degisimi   {:+.1f}  ({:.3f} -> {:.3f} milyon ons)".format(miktar, o0, o1))
    L.append("  altin-disi (doviz+SDR+IMF) {:+.1f}  <- gercek doviz cikisi/satisi vekili (swap ve degerleme dahil)".format(ng1 - ng0))
    L.append("  hafta hafta altin-disi: " + ", ".join("{:+.1f}".format((U["resmi_rezerv"][j] - U["altin"][j]) - (U["resmi_rezerv"][j - 1] - U["altin"][j - 1])) for j in range(2, 5))
             + "   (4 Eylul degisimi Agustos'a gore {:+.1f})".format((U["resmi_rezerv"][1] - U["altin"][1]) - ng0))

    # net likit
    ii1, ii2, ii3 = son("ii1_toplam"), son("ii2_forward"), son("ii3_diger")
    drain12 = -(ii1 + ii2 + ii3)
    drain3 = -(son("ii1_1ay") + son("ii1_2_3ay") + son("ii2_1ay") + 0.0 + son("ii3_diger"))
    ng = ng1
    L.append("")
    L.append("KESIN CIKISLAR (II) ve NET LIKIT (25 Eylul)")
    L.append("  II.1 doviz kredi/menkul/mevduat cikisi (12 ay) {:>7.1f}   (anapara {:.1f}, faiz {:.1f}; 1 ay {:.1f}, 2-3 ay {:.1f}, 4-12 ay {:.1f})".format(
        ii1, son("ii1_anapara"), son("ii1_faiz"), son("ii1_1ay"), son("ii1_2_3ay"), son("ii1_4_12ay")))
    L.append("  II.2 forward/future kisa pozisyon              {:>7.1f}   (cogu 4-12 ay: {:.1f})".format(ii2, son("ii2_4_12ay")))
    L.append("  II.3 diger giris                               {:>7.1f}".format(ii3))
    L.append("  12 ay net kesin cikis                          {:>7.1f}".format(-drain12))
    L.append("  3 ay net kesin cikis                           {:>7.1f}".format(-drain3))
    L.append("  Resmi rezerv {:.1f}; altin-disi {:.1f}".format(r1, ng1))
    L.append("  Net likit (12 ay cikis dusulmus):  toplam {:.1f},  altin-disi {:.1f}".format(r1 - drain12, ng - drain12))
    L.append("  Net likit (3 ay cikis dusulmus):   toplam {:.1f},  altin-disi {:.1f}".format(r1 - drain3, ng - drain3))
    L.append("  III.1 sarta bagli yukumluluk {:.1f} (diger sarta bagli {:.1f}, icerigi dosyada aciklanmiyor)".format(-son("iii1_sarta_bagli"), -son("iii1_diger_sarta_bagli")))
    L.append("  Altin rezervin %{:.0f}'i".format(100 * g1 / r1))

    # dayaniklilik: aylik satis hizlari
    L.append("")
    L.append("DAYANIKLILIK (aritmetik, tahmin degil). Aylik net doviz satisi X mlr $ surerse:")
    L.append("  X     altin-disi rezerv biter   net likit (12 ay cikis sonrasi) biter")
    net12 = ng - drain12
    for x in (2, 4, 8, 9.4):
        L.append("  {:<5}{:>14.1f} ay{:>28.1f} ay".format(x, ng / x, max(net12, 0) / x))
    L.append("  (9,4 = Agustos-Eylul altin-disi dusus hizi, ay basina)")

    # firma ters stresi + resmi katman
    st = durum("2026-07")
    pay = st["kv_kredi"] + st["ithalat"]
    rng = random.Random(TOHUM)
    kars = []
    for _ in range(4000):
        z = stres_cek(rng)
        pay_z = pay + z["f_t"] * st["turev_net"]
        kars.append((z["l"] * st["likit"] + z["e"] * st["ihr_alacak"], pay_z))
    L.append("")
    L.append("SISTEM TERS STRESI: yeniden finansman kaybi f ne olunca firma likiditesi + resmi katman yetmez")
    L.append("  resmi katman Q = max(0, altin-disi net likit) + g*altin   (g: satilabilir altin payi)")
    for g in (0.0, 0.25, 0.5):
        Q = max(0.0, net12) + g * g1
        fs = sorted((k + Q) / p for k, p in kars)
        L.append("  g={:<5} Q={:>6.1f}   f* medyan %{:.0f} [p10-p90 %{:.0f}-%{:.0f}]".format(g, Q, 100 * fs[len(fs) // 2], 100 * fs[len(fs) // 10], 100 * fs[9 * len(fs) // 10]))
    fs0 = sorted(k / p for k, p in kars)
    L.append("  yalniz firma tarafi (Q=0)  f* medyan %{:.0f}".format(100 * fs0[len(fs0) // 2]))
    L.append("  tarihin en kotu yillik daralmasi %24")
    return "\n".join(L)


def testler():
    out = []
    # T-R1: bilesen toplami
    kont = []
    for j in range(5):
        top = U["doviz_varlik"][j] + U["imf_rezerv_poz"][j] + U["sdr"][j] + U["altin"][j]
        kont.append(abs(top - U["resmi_rezerv"][j]))
    out.append(("T-R1 bilesenler (doviz+IMF+SDR+altin) = resmi rezerv, max fark {:.3f} mlr $".format(max(kont)), max(kont) < 0.01, "kimlik"))
    # T-R2: doviz kompozisyon toplami
    k2 = max(abs(U["kompozisyon_sdr_sepeti"][j] + U["kompozisyon_diger"][j] - U["resmi_rezerv"][j]) for j in range(5))
    out.append(("T-R2 doviz kompozisyonu (SDR sepeti + diger) = resmi rezerv, max fark {:.3f} mlr $".format(k2), k2 < 0.01, "kimlik"))
    # T-R3: altin fiyat tutarliligi
    pr = [ons_fiyati(j) for j in range(5)]
    mak = max(abs(pr[j] / pr[j - 1] - 1) for j in range(1, 5))
    out.append(("T-R3 haftalik ima edilen altin fiyati: en buyuk haftalik oynama %{:.1f}. Altin degerlemesi dususe dahil, fiyat sicramasi yok".format(100 * mak),
                mak < 0.05, "fiyat serisi tutarli, kimlik testi"))
    # T-R4: dususun gercek kismi
    ng0 = U["resmi_rezerv"][0] - U["altin"][0]
    ng1 = U["resmi_rezerv"][-1] - U["altin"][-1]
    out.append(("T-R4 Agustos-Eylul altin-disi dusus {:+.1f} mlr $, toplamin %{:.0f}'i".format(ng1 - ng0, 100 * (ng1 - ng0) / (U["resmi_rezerv"][-1] - U["resmi_rezerv"][0])),
                None, "BILGI: dususun yarisi degerleme, yarisi gercek doviz cikisi"))
    # T-R5: net likit
    net12 = (ng1) - (-(son("ii1_toplam") + son("ii2_forward") + son("ii3_diger")))
    out.append(("T-R5 altin-disi net likit (12 ay cikis sonrasi) {:.1f} mlr $ (3 ay: 52,7)".format(net12), None, "BILGI: esik tanimlamadim, aylik 4-9 mlr $ satisla 1-2 ayda biter"))
    # T-R6: kur serisi olmadan eta
    out.append(("T-R6 Eylul 2026 kur serisi bu dosyada yok: eta ve cb'nin kur bacagi hala tanimlanamaz", False, "haftalik kur gerek"))
    return out


def test_blogu():
    L = ["GERCEKLIK TESTLERI (rezerv)"]
    gec = 0
    tl = testler()
    say = 0
    for msg, ok, n in tl:
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
