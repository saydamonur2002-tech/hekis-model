"""ALT MODEL (konut uygulamasi): yaptirim blokaji. owner.py karar kuralinin uygulama ayagi.

Genel model `hekis/blokaj.py` (secici yaptirim tekeli). Bu dosya onun konut kanununa ozel dar uygulamasi.

Kanun yazili, bedel kesilmiyor. Kim durduruyor?

    python -m hekis.blokaj_konut

Tez: merkez resmen toplaniyor, fiilen dagiliyor. Denetim kaydi olayi biliyor, hareket bloke.
Burada tez kanun taslaginin kendi sayisina baglanir: owner.py kurali yuzde 4 bedel, bes yilda satis.
Bu oran sifir sizinti varsayar. Sizinti olursa kimin stoku cikar, kimin cikmaz.

Iki grup: SIRADAN malik ve HIZIP BAGLANTILI malik (pay f). Tespit her yil d olasilikla olur, herkes icin.
Hizip baglantili birimin dosyasi kalici olarak KAPANABILIR. Kapanma uc ayri kapidan gelir:
  l = mevzuata uygun gerekce ile kapatma (yasal bicim)
  b = siyasi hat durdurur (denetim biliyor, yaptirima cevrilmiyor)
  c = denetim organi hatla ic ice, dosya kayda hic girmez (ele gecirilmis)
  m = tahakkuk otomatiklesince muafiyet kapisina kayma (sahte oturma belgesi gibi)
Kapanma kalici. Tespit yillik. Bu fark onemli: kapanan birim bedelin bir kismini degil, hic odemez.

Bu bir tanimlama modeli degil, karar araci. f, d, l, b, c, m gozlem degil. Hicbiri veriden olculmedi.
Uc kapinin sonuca etkisi ayni formda girer, yani toplam kapanma ayni ise cikti ayni cikar.
Fark cozumde: hangi kapi acik ise yalniz onu kapatan onlem ise yarar. Yanlis teshis onlemi bosa harcar.
Onlemlerin her kapiya etkisi (carpanlar) varsayimdir.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace

from hekis.owner import years_to_sell

PIYASA = 3_619_875      # Esenyurt ortalama, owner.py ile ayni
HAVUZ = 0.80
ORAN = 0.04             # ucuncu ve sonrasi yillik bedel, KANUN_TASLAGI.md madde 3
ILK_YIL = 0.5           # gecis: ilk yil oranin yarisi
UFUK = 7                # yil. Sifir sizintida 5,5 yil, 7 yil biraz pay birakir


@dataclass(frozen=True)
class Okuma:
    ad: str
    l: float = 0.0
    b: float = 0.0
    c: float = 0.0
    m: float = 0.0

    @property
    def kapanma(self) -> float:
        return 1 - (1 - self.l) * (1 - self.b) * (1 - self.c) * (1 - self.m)


def yil_sayisi(etkin: float, havuz: float = HAVUZ, oran: float = ORAN) -> float | None:
    """Beklenen tahakkukla satis yili. Gecis dahil. Tek birim icin MC cevabi degil, ortalama yoludur."""
    fark = 1 - havuz
    if etkin <= 0:
        return None
    ilk = oran * ILK_YIL * etkin
    if fark <= ilk:
        return fark / ilk
    return 1 + (fark - ilk) / (oran * etkin)


def kos(f: float, d: float, ok: Okuma, n: int = 40_000, seed: int = 7) -> dict:
    rng = random.Random(seed)
    sirad_sat = sirad_n = hizip_sat = hizip_n = 0
    yuk_sirad = yuk_hizip = 0.0
    yillar = []
    fark = 1 - HAVUZ
    for _ in range(n):
        hizip = rng.random() < f
        kapali = hizip and rng.random() < ok.kapanma
        if hizip:
            hizip_n += 1
        else:
            sirad_n += 1
        toplam = 0.0
        satti = False
        if not kapali:
            for t in range(1, UFUK + 1):
                if rng.random() < d:
                    odeme = ORAN * (ILK_YIL if t == 1 else 1.0)
                    toplam += odeme
                    if hizip:
                        yuk_hizip += odeme
                    else:
                        yuk_sirad += odeme
                    if toplam >= fark:
                        satti = True
                        yillar.append(t)
                        break
        if satti:
            if hizip:
                hizip_sat += 1
            else:
                sirad_sat += 1
    toplam_yuk = yuk_sirad + yuk_hizip
    return {
        "satis_toplam": (sirad_sat + hizip_sat) / n,
        "satis_sirad": sirad_sat / max(sirad_n, 1),
        "satis_hizip": hizip_sat / max(hizip_n, 1),
        "yil": sum(yillar) / len(yillar) if yillar else None,
        "yuk_sirad": yuk_sirad / toplam_yuk if toplam_yuk else 0.0,
    }


# Onlemler: hangi kapiyi ne kadar kapatir. Carpan 0,1 = kapinin %90'i kapanir. Varsayim.
def metin(o: Okuma) -> Okuma:
    """Kapatma gerekcesi kapali liste, 'usulune uygun' gerekce uretme alani daralir."""
    return replace(o, l=o.l * 0.1)


def otomatik(o: Okuma) -> Okuma:
    """Bedel veri eslesmesiyle tahakkuk eder, takdir yok. Takdir kalmayinca siyasi durdurma ve gerekce daralir.
    Bedel: tahakkuk muafiyet beyanina bagli kaldigi icin yeni kapi (m) acilir."""
    return replace(o, b=o.b * 0.1, l=o.l * 0.5, m=0.15)


def dis_veri(o: Okuma) -> Okuma:
    """Tapu ile elektrik/su abonelik verisini denetim hattinin disindaki kurum eslestirir. Kayda girmeme daralir.
    Bedel: veriyi ureten kurum yeni filtredir, m yine acilir ve b kismen kalir."""
    return replace(o, c=o.c * 0.1, b=o.b * 0.7, m=0.15)


def hepsi(o: Okuma) -> Okuma:
    return dis_veri(otomatik(metin(o)))


ONLEMLER = [("yok", lambda o: o), ("metin", metin), ("otomatik tahakkuk", otomatik),
            ("dis veri", dis_veri), ("hepsi", hepsi)]


def rapor() -> str:
    f, d = 0.30, 0.90
    kapanma = 0.40
    okumalar = [
        Okuma("1 yasal bosluk", l=kapanma),
        Okuma("2 siyasi hat", b=kapanma),
        Okuma("3 ele gecirilmis organ", c=kapanma),
    ]
    out = []
    out.append(f"Esenyurt ortalama {PIYASA:,} TL, havuz {HAVUZ:.0%}, bedel {ORAN:.0%}, gecis ilk yil yari.".replace(",", "."))
    out.append(f"Hizip baglantili pay f={f:.0%}, yillik tespit d={d:.0%}. Hepsi varsayim.")
    y_owner = years_to_sell(PIYASA, PIYASA * HAVUZ, PIYASA * ORAN)   # owner.py: gecissiz, sizintisiz
    y0 = yil_sayisi(1.0)
    y1 = yil_sayisi(d)
    out.append(f"Sifir sizinti: {y0:.1f} yil (gecis dahil, owner.py {y_owner:.1f}). Tespit {d:.0%} ise ortalama yolda {y1:.1f} yil.")
    out.append("Yani yuzde 4 esigi zaten sifir payla kurulmus. Kucuk bir sizinti bile bes yil hedefini kacirir.")
    out.append("")
    base = kos(f, d, Okuma("sizintisiz"))
    out.append(f"Referans (kapanma yok): {UFUK} yilda stok cikisi {base['satis_toplam']:.0%}, ort. {base['yil']:.1f} yil.")
    out.append("")
    out.append(f"Kapanma {kapanma:.0%} (hizip baglantili dosyalarin), uc okuma ayni cikti verir:")
    out.append("okuma | stok cikisi | siradan | hizip | siradan yuk payi")
    for ok in okumalar:
        r = kos(f, d, ok)
        out.append(f"{ok.ad} | {r['satis_toplam']:.0%} | {r['satis_sirad']:.0%} | {r['satis_hizip']:.0%} | {r['yuk_sirad']:.0%}")
    out.append("(Ayni toplam kapanma, ayni sayi. Cikti kapiyi ayirt etmez. Kapiyi ayirt eden gozlem KANUN_TASLAGI.md'de.)")
    out.append("")
    out.append(f"Beklenti yolu yaniltir: hizip icin ortalama {yil_sayisi(d * (1 - kapanma)):.1f} yil gorunur.")
    out.append("Gercekte iki mod var: dosya acik ise normal yil, kapali ise hic. Ortalama bunu saklar.")
    out.append("")
    out.append("Onlem x okuma: stok cikisi (7 yil). Onlemin hangi kapiya baktigi varsayim.")
    ad = [o.ad for o in okumalar]
    out.append("onlem | " + " | ".join(ad))
    for isim, fn in ONLEMLER:
        hucre = []
        for ok in okumalar:
            r = kos(f, d, fn(ok))
            hucre.append(f"{r['satis_toplam']:.0%} (kapanma {fn(ok).kapanma:.0%})")
        out.append(f"{isim} | " + " | ".join(hucre))
    out.append("")
    out.append("Okuma: metin yalniz yasal boslukta ise yarar. Otomatik tahakkuk siyasi hatta ise yarar, ama muafiyet kapisi (m) acar.")
    out.append("Dis veri organ ele gecirilmisse ise yarar, veriyi ureten kurum yeni filtre olur (m).")
    out.append("Yanlis teshis yalniz bosa gitmez: otomatik tahakkuk organ ele gecirilmisse, dis veri yasal bosluktaysa m kapisi yuzunden stok cikisi duser.")
    out.append("Hepsi birlikte uc okumada da ayni tabana iner: kalan sizinti m'dir. Teshis bilinmiyorsa tek garanti paket, ama paket bile sifir sizinti degil.")
    return "\n".join(out)


if __name__ == "__main__":
    print(rapor())
