"""ALT MODEL: secici yaptirim tekeli altinda sembolik merkezilesme.

    python -m hekis.blokaj

Birim dosyadir: bir ihale, bir bagis kanali, bir belediye karari, bir olay. Aktor degisir, dongu degismez.
Bes oyuncu, her biri tek sey tutar:
  M merkez       imza ve yaptirim anahtari
  H hizip        faaliyet ve kazanc
  D denetim      bilgi (manometre, vana degil)
  A alt kademe   gorunur kusur
  K kamu bilancosu artik risk
Dosya yedi durumdan gecer: yerlesim, kayit, blokaj, gerekceleme, patlama, yuk kaymasi, yeniden yerlesim.

Formal cekirdek (kurum k icin):
  E = I (1 - B)                       denetimin yaptirima cevirdigi. I bilinen, B blokaj.
  B = B0 + delta C                    delta > 0: blokaj merkezilesmenin kendisinden uretiliyor.
  alpha* = a0 + C (beta B - omega (1-B))
  K = tau G_H                         devlete yikilan pay.

DUZELTME: ilk yazimdaki alpha = a0 + beta C B, B = 0 iken saha daralir demiyordu, a0'da sabit kaliyordu.
Weber daralmasi ayri terim (omega) olarak eklendi; omega = 0 verilirse ilk yazim aynen geri gelir.
Isaret donusu: d alpha / dC = beta B - omega (1-B) + C (beta + omega) delta. Delta = 0 icin kritik blokaj
B* = omega / (beta + omega): bunun altinda merkezilesme sahayi daraltir, ustunde buyutur.

Iki arac: alpha* kapali form, alpha_dongu ise yedi durumu dosya dosya calistirip alpha'yi cezasiz kapanis
arttirir / bedel azaltir kuraliyla yurutur. SEVIYELER KIYASLANAMAZ (dongu seviyesi ETA ve phi'ye bagli).
Yalniz yon kiyaslanir. Dongude Weber daralmasi YOK: C yalniz B uzerinden girer. Bu yuzden delta = 0 ve
B < B* olan kurumlarda formul 'saha daralir' derken dongu duz kalir. omega bir cikti degil varsayimdir.
Model E'yi I(1-B) olarak uretir, bu yuzden tezi kendi icinde test EDEMEZ; test gercek dosya verisindedir.

Bu bir tanimlama degil, senaryo araci. data/kurumlar.json ornek parametrelerle gelir, olculmemistir.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, replace
from pathlib import Path

VERI = Path(__file__).resolve().parent.parent / "data" / "kurumlar.json"
DONEM = 40
SON = 10          # alpha_dongu: son SON donemin ortalamasi
ETA = 0.3         # dongu ogrenme hizi
ALT, UST = 0.02, 1.0


@dataclass(frozen=True)
class Kurum:
    ad: str
    I: float        # D dosyayi bastan biliyor
    B0: float       # temel blokaj
    delta: float    # B'nin C'ye duyarliligi
    alpha0: float
    beta: float     # blokajli merkezilesmenin saha buyutmesi
    omega: float    # Weber daralmasi
    N0: float       # alpha=1'de donem basina dosya
    g: float        # dosya basina ortalama kazanc
    tau: float      # zarar K'ya ne kadar yazilir
    r: float        # gerekceleme olasiligi
    p_pat: float    # patlama olasiligi (gerekcelenmis blokajda x0,3)
    a: float        # gorunur kusurun A'ya dusen payi
    q_rival: float  # blokajli dosyada rakip hattin vanayi acma olasiligi
    phi: float      # yaptirimda H'nin ceza orani (kazancin kaci)

    def B(self, C: float) -> float:
        return min(1.0, max(0.0, self.B0 + self.delta * C))

    def alpha_formul(self, C: float) -> float:
        b = self.B(C)
        return min(UST, max(0.0, self.alpha0 + C * (self.beta * b - self.omega * (1 - b))))

    def b_kritik(self) -> float:
        return self.omega / (self.beta + self.omega) if (self.beta + self.omega) > 0 else float("nan")

    def E(self, C: float) -> float:
        return self.I * (1 - self.B(C))


def yukle(yol: Path = VERI) -> tuple[float, list[Kurum]]:
    d = json.loads(yol.read_text())
    ks = [Kurum(**{k: v for k, v in x.items()}) for x in d["kurumlar"]]
    return d["C"], ks


def _yuvarla(x: float, rng: random.Random) -> int:
    n = int(x)
    return n + (1 if rng.random() < x - n else 0)


def kos(k: Kurum, C: float, seed: int = 11) -> dict:
    """Dosya dosya dongu. Yedi durum, her dosya icin."""
    rng = random.Random(seed)
    B = k.B(C)
    alpha = min(UST, max(ALT, k.alpha0))
    yol = []
    s = dict(n=0, G=0.0, yaptirim_devlet=0, yaptirim_rakip=0, yaptirim_gec=0, bilinmeyen=0, gec_bilgi=0,
             bastan_kapali=0, patlama=0, K=0.0, A=0.0, M=0.0, H_net=0.0)
    for _ in range(DONEM):
        n = _yuvarla(k.N0 * alpha, rng)
        cezasiz = cezali = 0
        for _ in range(n):                                   # 1 yerlesim
            G = rng.expovariate(1 / k.g)
            s["n"] += 1
            s["G"] += G
            bilinen = rng.random() < k.I                     # 2 kayit
            yaptirim = None
            gerekceli = False
            patladi = False
            if bilinen:
                if rng.random() < B:                         # 3 blokaj
                    s["bastan_kapali"] += 1
                    if rng.random() < k.q_rival:             # baska hat vanayi acti
                        yaptirim = "rakip"
                    else:
                        gerekceli = rng.random() < k.r       # 4 gerekceleme
                        patladi = rng.random() < k.p_pat * (0.3 if gerekceli else 1.0)
                else:
                    yaptirim = "devlet"
            else:
                s["bilinmeyen"] += 1
                if rng.random() < k.p_pat:                   # kor dosya disari sizar, D gec ogrenir
                    patladi = True
                    s["gec_bilgi"] += 1
                    if rng.random() >= B:
                        yaptirim = "gec"
            if patladi:                                      # 5 patlama
                s["patlama"] += 1
            if yaptirim:
                s["yaptirim_" + yaptirim] += 1
                s["H_net"] += G * (1 - k.phi)
                cezali += 1
            else:                                            # 6 yuk kaymasi
                s["H_net"] += G
                s["K"] += k.tau * G
                if patladi:
                    s["A"] += k.a * G
                    s["M"] += (1 - k.a) * G * (0.1 if gerekceli else 1.0)
                cezasiz += 1
        toplam = cezasiz + cezali                            # 7 yeniden yerlesim
        if toplam:
            c = cezasiz / toplam
            sz = cezali / toplam
            alpha += ETA * ((UST - alpha) * c - alpha * sz * k.phi)
            alpha = min(UST, max(ALT, alpha))
        yol.append(alpha)
    s["alpha_dongu"] = sum(yol[-SON:]) / SON
    n = max(s["n"], 1)
    s["E_amp"] = (s["yaptirim_devlet"] + s["yaptirim_gec"]) / n
    s["E_rakipli"] = s["E_amp"] + s["yaptirim_rakip"] / n
    return s


def teshis(k: Kurum, C: float) -> tuple[float, float]:
    """Yaptirimsiz kalma 1-E = (1-I) + I B. Korluk payi ile blokaj payi ayri kovadir."""
    e = k.E(C)
    kayip = 1 - e
    return (1 - k.I) / kayip, k.I * k.B(C) / kayip


def rapor() -> str:
    C, ks = yukle()
    o = []
    o.append("Secici yaptirim tekeli altinda sembolik merkezilesme. Birim dosya. Parametreler ornek, olculmedi.")
    o.append(f"Formal merkezilesme C={C}. {DONEM} donem, alpha_dongu son {SON} donemin ortalamasi.")
    o.append("")
    o.append("kurum | B | E=I(1-B) | alpha* | alpha_dongu | B* | korluk/blokaj payi | K/G | A/G | M/G | H net/dosya")
    for i, k in enumerate(ks):
        s = kos(k, C, seed=11 + i)
        kor, blk = teshis(k, C)
        o.append(
            f"{k.ad} | {k.B(C):.2f} | {k.E(C):.2f} | {k.alpha_formul(C):.2f} | {s['alpha_dongu']:.2f} | "
            f"{k.b_kritik():.2f} | {kor:.0%}/{blk:.0%} | {s['K'] / s['G']:.2f} | {s['A'] / s['G']:.2f} | "
            f"{s['M'] / s['G']:.2f} | {s['H_net'] / s['n']:.2f}"
        )
    o.append("")
    o.append("Merkezilesme C arttikca saha (alpha_dongu): delta ayarli vs delta=0 (Weber, blokaj sabit).")
    o.append("kurum | " + " | ".join(f"C={c:.2f}" for c in (0.0, 0.25, 0.5, 0.75, 1.0)))
    for i, k in enumerate(ks):
        satir = []
        for c in (0.0, 0.25, 0.5, 0.75, 1.0):
            a1 = kos(k, c, seed=21 + i)["alpha_dongu"]
            a0 = kos(replace(k, delta=0.0), c, seed=21 + i)["alpha_dongu"]
            satir.append(f"{a1:.2f}/{a0:.2f}")
        o.append(f"{k.ad} | " + " | ".join(satir))
    o.append("(her hucre: delta ayarli / delta=0)")
    o.append("")
    o.append("alpha* formul yonu (d alpha/dC isareti) ve kritik blokaj B*:")
    for k in ks:
        d = k.beta * k.B(C) - k.omega * (1 - k.B(C)) + C * (k.beta + k.omega) * k.delta
        yon = "saha BUYUR" if d > 0 else "saha daralir"
        o.append(f"{k.ad}: d alpha/dC = {d:+.2f} ({yon}); B*={k.b_kritik():.2f}, B(C)={k.B(C):.2f}")
    o.append("")
    o.append("Yaptirim kaynaklari (tum donemler, dosya sayisina oran):")
    o.append("kurum | devlet | rakip hat | gec bilgi | E_amp | E rakipli | rakipli payi")
    for i, k in enumerate(ks):
        s = kos(k, C, seed=11 + i)
        n = max(s["n"], 1)
        top = s["yaptirim_devlet"] + s["yaptirim_gec"] + s["yaptirim_rakip"]
        rp = s["yaptirim_rakip"] / top if top else 0.0
        o.append(f"{k.ad} | {s['yaptirim_devlet'] / n:.2f} | {s['yaptirim_rakip'] / n:.2f} | {s['yaptirim_gec'] / n:.2f} | "
                 f"{s['E_amp']:.2f} | {s['E_rakipli']:.2f} | {rp:.0%}")
    o.append("Rakip hat vanayi actiginda E yukselir ama bu 'devlet denetledi' degil, 'baska hizip vanayi acti'dir.")
    o.append("")
    o.append("Yon uyumu (C: 0 -> 1). Seviyeler kiyaslanmaz, yalniz isaret. Esik 0,05 altinda 'duz'.")
    o.append("kurum | formul alpha*(1)-alpha*(0) | dongu alpha(1)-alpha(0) | uyum")
    for i, k in enumerate(ks):
        f = k.alpha_formul(1.0) - k.alpha_formul(0.0)
        d = kos(k, 1.0, seed=21 + i)["alpha_dongu"] - kos(k, 0.0, seed=21 + i)["alpha_dongu"]
        def isaret(x):
            return 0 if abs(x) < 0.05 else (1 if x > 0 else -1)
        uyum = "uyumlu" if isaret(f) == isaret(d) else "UYUSMUYOR (omega varsayimi dongude yok)"
        o.append(f"{k.ad} | {f:+.2f} | {d:+.2f} | {uyum}")
    o.append("")
    o.append("Okuma ve sinir:")
    o.append("- Korluk ile blokaj ayri kova: 1-E = (1-I) + I B. Korluk payi yuksekse sorun blokaj degil, bilgi eksigi.")
    o.append("  Test gercek veride: dosya sonradan tam mi cikti (gec bilgi), en basindan kapali mi tutuldu (bastan kapali).")
    o.append("- Model E'yi B'den uretir, bu yuzden devlet sutununun dolu olmasi tezi curutmez ya da dogrulamaz. Curutme veride:")
    o.append("  yuksek olculmus B altinda H'nin gercekten bedel odedigi acik dosyalar, ya da C artarken B'nin dusmesi (delta < 0).")
    o.append("- Rakip hat sutunu: E yukselse bile secici anahtar sorusu cevaplanmaz, hangi hattin tuttugu degisir.")
    o.append("- K'ya yazilan zarar ile H'nin mevziine yazilan sadakat bu modelde ayni sayidir. Edilgenlik mi, satin alma mi")
    o.append("  ayrimi bu parametrelerle yapilamaz.")
    o.append("- A saf gunah kecisi varsayilir (a payi gorunur kusur). A'nin rantin ortagi olmasi disarida.")
    o.append("- K/G yuksek, A/G ve M/G dusuk: zarar defterde, gorunur kusur ve imza maliyeti kucuk. Bu parametrelerin")
    o.append("  (tau, a, r) varsayimindan geliyor, bulgu degil.")
    o.append("- Sonuclar delta ve B0'a duyarli. Parametreler olculmedi: kesin sayi degil, yon ve esik sorusu.")
    return "\n".join(o)


if __name__ == "__main__":
    print(rapor())
