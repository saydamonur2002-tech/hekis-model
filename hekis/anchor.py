"""Dis capa: 2024 tasarruf finansman (katilim evim) sistemi verisi.

Modelin tasarimi bu sisteme BENZEMEZ: o, uyelerin birikimiyle cekilisli/siralamali finansman; HEKIS, bos stoku havuza
alan kira sistemi. Veri yalniz olcek ve talep icin dis kontrol olarak kullanilir, parametre almaz.
Kaynak: haber ozetleri (sozlesme 498 mr TL, musteri 630 bin, aktif 92 mr TL; dogrulanmamis, konut/tasit ayrimi yok).
Karsilastirma baz yili 2024, model 2026: nominal buyume farki dikkate alinmadi.

    python -m hekis.anchor
"""

from __future__ import annotations

from hekis import evaluate as E
from hekis.zones import run_three_zone

TF_2024 = {"sozlesme_mr": 498.0, "musteri": 630_000, "aktif_mr": 92.0, "sozlesme_buyume": 2.06, "musteri_buyume": 0.75}
MEVDUAT_2026_MR = 32_000.0  # TL mevduat 20,7 trilyon + doviz ~11,3 trilyon (DOLARIZASYON_URETIM.md)
ISSUE_MR = 89.2


def report() -> dict:
    z = run_three_zone()
    return {
        "ort_sozlesme": TF_2024["sozlesme_mr"] * 1e9 / TF_2024["musteri"],
        "hekis_hane": z["N"],
        "hane_orani": z["N"] / TF_2024["musteri"],
        "aktif_mevduat": TF_2024["aktif_mr"] / MEVDUAT_2026_MR,
        "senet_mevduat": ISSUE_MR / MEVDUAT_2026_MR,
        "senet_aktif": ISSUE_MR / TF_2024["aktif_mr"],
        "kapsam": z["coverage"],
        "birim_deger": z["V"][0],
    }


def main() -> int:
    r = report()
    print("2024 tasarruf finansman (dis capa, benzetme yok):")
    print(f"  musteri basina ortalama sozlesme {r['ort_sozlesme']:,.0f} TL (konut+tasit karisik)".replace(",", "."))
    print(f"  HEKIS havuz birim degeri {r['birim_deger']:,.0f} TL".replace(",", "."))
    print(f"  HEKIS yerlesen hane {r['hekis_hane']:,.0f} = sistemin 2024 musterisinin {r['hane_orani']:.1%}".replace(",", "."))
    print(f"  sistem aktifi mevduatin {r['aktif_mevduat']:.2%}, HEKIS senedi {r['senet_mevduat']:.2%}; senet / aktif = {r['senet_aktif']:.2f}")
    print(f"  HEKIS kapsami (uygun kiraciya) {r['kapsam']:.1%}: talep siniri degil, arz ve katilim siniri")
    print("Okuma: en hizli buyuyen 2024 kanali bile mevduatin ~%0,3'unu cekti; senet ayni mertebede. Dolarizasyon kapasitesi ~0 sonucu dis olcekle de uyumlu.")
    print("Sinir: sistemin musterisi tasarruf eden orta gelir; HEKIS'in uygun kiraciisi (duz memur maasi alti) baska nufus. Talep kaniti sayilmaz.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
