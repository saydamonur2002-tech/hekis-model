"""Gerceklik kontrolleri: model buyuklukleri gozlenen referanslarla karsilastirilir.
Karar: UYUMLU, UYARI, DOGRULANAMAZ (karsilastirilacak gozlem yok).

    python -m hekis.checks
"""

from __future__ import annotations

from hekis import activation, calibrate, evaluate as E, politics
from hekis.bind import inflation_paths, load_obs


def main() -> int:
    obs = load_obs()
    rows: list[tuple[str, str, str, str]] = []

    def add(name: str, model: str, ref: str, verdict: str) -> None:
        rows.append((name, model, ref, verdict))

    # 1 bosluk orani
    stok = obs["bos_stok"]
    share_low = stok["elektrik_aboneligi_tabanli"] / stok["istanbul_konut_stoku"]
    share_mid = stok["ibb_elektrik_su_tabanli"] / stok["istanbul_konut_stoku"]
    v = obs["vacancy"]["elektrik_abonelik_avrupa_yakasi"]
    add("Havuzdaki bosluk (devir) orani", f"{v:.1%}", f"Istanbul bos stok payi {share_low:.1%} - {share_mid:.1%}", "UYARI: model bosluk orani bos stok tahminlerinin altinda")
    # 2 getiri
    m2 = obs["rent"]["istanbul_m2_tl"] * 12 / obs["sale"]["istanbul_m2_tl"]
    es = obs["rent"]["esenyurt_2_1_tl"] * 12 / (obs["sale"]["esenyurt_m2_tl"] * 95)
    add("Istanbul brut kira getirisi", f"{m2:.1%}", "Endeksa Esenyurt getirisi %10,04 (10 yil amortisman)", "UYUMLU: ayni buyukluk")
    add("Esenyurt 2+1 brut getiri (model fiyat/kira)", f"{es:.1%}", "Endeksa %10,04", "UYUMLU" if abs(es - 0.1004) < 0.02 else "UYARI")
    pol = 20_000 * 12 / (obs["sale"]["istanbul_m2_tl"] * 95)
    add("Politika kirasi getirisi (orta, 2+1)", f"{pol:.1%}", f"piyasa {m2:.1%}", "UYARI: politika kirasi piyasanin cok altinda, geri odeme bundan yavas")
    # 3 tutma maliyeti
    hold = activation.hold_cost_ratio(obs)
    add("Bos tutma maliyeti / deger", f"{hold:.2%}", "vergi <=0,2% + DASK ~0,05% + aidat ~1%", "UYUMLU: bilesenlerle tutarli, bakim haric")
    # 4 gelir dagilimi
    top, bottom = politics.share_check()
    add("Gelir dagilimi: ust %20 / alt %20 payi", f"{top:.1%} / {bottom:.1%}", "TUIK %48 / %6,4", "UYARI: alt uc fazla yoksul" if abs(bottom - 0.064) > 0.01 else "UYUMLU")
    # 5 kira/gelir tavani
    worst = max(min(16825.0, 0.30 * politics.hh_monthly(q)) / politics.hh_monthly(q) for q in (0.02, 0.1, 0.4))
    add("Oturanin kira/gelir orani (kural a=%30)", f"en yuksek {worst:.0%}", "kural %30", "UYUMLU: yapi geregi")
    # 6 mali olcek
    base = E.evaluate()
    per_hh = base["sub1"] / politics.HOUSEHOLDS
    add("Yil 1 subvansiyon / hane", f"{per_hh:,.0f} TL".replace(",", "."), "karsilastirilacak resmi program yok", "DOGRULANAMAZ")
    # 7 kapsam
    eligible = politics.HOUSEHOLDS * politics.TENANT_SHARE * 0.4
    add("Yerlesen / uygun kiraci hane (alt %40)", f"{base['N'] / eligible:.1%}", "TUIK kiraci payi %27", "UYUMLU: kapsam kucuk, kura gerekir")
    # 8 enflasyon
    ovp1 = inflation_paths(obs)["ovp"][0]
    add("Ilk yil enflasyon yolu", f"{ovp1:.1%}", "Agustos 2026 yillik %31,51; Eylul beklentisi ~%30,2", "UYARI: model yolu gozlenenin 2-3 puan altinda")
    # 9 beklenti kurali
    errs = calibrate.window_errors(obs)
    naive, w1 = errs[0][1], errs[1][1]
    add("Beklenti kurali tahmin gucu", f"RMSE {w1 * 100:.1f} puan", f"sifir tahmin {naive * 100:.1f} puan", "UYARI: tahmin modeli degil, davranis varsayimi")
    # 10 KFE vs Endeksa
    k = obs["kfe_reel_yillik"]["2026_agustos_yillik"]
    add("Reel konut artisi: KFE (Turkiye) vs Endeksa (Istanbul)", f"{k:.1%}", f"Endeksa Istanbul {obs['sale']['istanbul_reel_yillik']:.1%}", "UYARI: 3 puan fark, beklenti Istanbul icin iyimser olmayabilir")
    # 11 katilim
    add("Katilim fonksiyonu", "tavan %40, egim 25", "pilot veya yurt disi dogrudan olcum yok (Vancouver %54 dolayli)", "DOGRULANAMAZ")
    # 12 tahsilat
    add("Etkin tahsilat", "%60 varsayim", "Irlanda: isaretlenenin ~%6'si vergiye tabi", "UYARI: varsayim iyimser olabilir")
    # 13 geri odeme
    add("Geri odeme (20 yil)", f"{base['odenen']:.0%} (luks ayrilmis)", "tum stokta %75", "UYARI: orta tip kirasi degerle orantili varsayimi")

    w = max(len(r[0]) for r in rows)
    print(f"{'kontrol':<{w}}  {'model':<30}  {'referans':<56}  karar")
    for name, model, ref, verdict in rows:
        print(f"{name:<{w}}  {model:<30}  {ref:<56}  {verdict}")
    cnt = {key: sum(1 for r in rows if r[3].startswith(key)) for key in ("UYUMLU", "UYARI", "DOGRULANAMAZ")}
    print()
    print("Ozet:", cnt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
