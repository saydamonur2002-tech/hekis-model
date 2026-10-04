"""Gozlem dosyasindan senaryo uret."""

from __future__ import annotations

import json
from pathlib import Path

from hekis.model import Params, UnitType, format_report, simulate


SIZES = {"1+0": 40, "1+1": 60, "2+1": 95}
COUNTS = {"2+1": 1000, "1+1": 1000, "1+0": 500}


def load_obs(path: str | Path | None = None) -> dict:
    root = Path(__file__).resolve().parents[1]
    target = Path(path) if path else root / "data" / "istanbul_2026.json"
    return json.loads(target.read_text(encoding="utf-8"))


def prices_from_m2(obs: dict, key: str = "istanbul_m2_tl") -> dict[str, float]:
    m2 = obs["sale"][key]
    return {name: m2 * size for name, size in SIZES.items()}


def market_rents(obs: dict) -> dict[str, float]:
    m2 = obs["rent"]["istanbul_m2_tl"]
    return {name: m2 * size for name, size in SIZES.items()}


def esenyurt_rents(obs: dict) -> dict[str, float]:
    rent = obs["rent"]
    return {"2+1": rent["esenyurt_2_1_tl"], "1+1": rent["esenyurt_1_1_tl"], "1+0": rent["esenyurt_1_0_tl"]}


def inflation_paths(obs: dict, horizon: int = 20) -> dict[str, list[float]]:
    hist = obs["inflation_annual"]
    realized = [hist["2021"], hist["2022"], hist["2023"], hist["2024"], hist["2025"]]
    last = hist["2026_agustos_yoy"]
    hold = [last] * horizon
    disinflation = [last + (0.15 - last) * i / (horizon - 1) for i in range(horizon)]
    ovp = obs["ovp_2027_2029"]
    ovp_path = [ovp["2026"], ovp["2027"], ovp["2028"]] + [ovp["2029"]] * (horizon - 3)
    return {"hold_last": hold, "disinflation_varsayim": disinflation, "ovp": ovp_path, "realized_2021_2025": realized}


def build_units(obs: dict, rent_mode: str, vacancy_key: str = "elektrik", aidat: float | None = None,
                rent_mult: float = 1.0) -> tuple[list[UnitType], float]:
    """rent_mult: yalniz esenyurt ailesinde havuzun aldigi kirayi carpar (sahibin senede karsilik kabul ettigi kira).
    Oturan payi ayri: esenyurt modunda oturan havuz kirasini oder, sub20 %80'ini, sosyal modda sosyal kirayi."""
    price = prices_from_m2(obs)
    if rent_mode == "piyasa":
        rent = market_rents(obs)
        tenant = rent
    elif rent_mode == "esenyurt":
        rent = {k: v * rent_mult for k, v in esenyurt_rents(obs).items()}
        tenant = rent
        price = prices_from_m2(obs, "esenyurt_m2_tl")
    elif rent_mode == "esenyurt_sub20":
        rent = {k: v * rent_mult for k, v in esenyurt_rents(obs).items()}
        tenant = {name: rent[name] * 0.80 for name in SIZES}
        price = prices_from_m2(obs, "esenyurt_m2_tl")
    elif rent_mode == "esenyurt_sosyal":
        rent = {k: v * rent_mult for k, v in esenyurt_rents(obs).items()}
        social = obs["social_rent"]
        tenant = {"2+1": social["2+1"], "1+1": social["1+1"], "1+0": social["1+1"] * 0.8}
        price = prices_from_m2(obs, "esenyurt_m2_tl")
    elif rent_mode == "hekis":
        rent = obs["policy_rent"]
        social = obs["social_rent"]
        tenant = {"2+1": social["2+1"], "1+1": social["1+1"], "1+0": social["1+1"] * 0.8}
    elif rent_mode == "sosyal":
        social = obs["social_rent"]
        rent = {"2+1": social["2+1"], "1+1": social["1+1"], "1+0": social["1+1"] * 0.8}
        tenant = rent
    else:
        raise ValueError(rent_mode)
    aidat = obs["aidat"]["istanbul_ortalama_tl_ay"] if aidat is None else aidat
    vacancy = obs["vacancy"]["elektrik_abonelik_avrupa_yakasi" if vacancy_key == "elektrik" else "ulusal_bos_stok_iddiasi"]
    units = []
    for name in ("2+1", "1+1", "1+0"):
        units.append(
            UnitType(
                name=name,
                count=COUNTS[name],
                price=price[name],
                rent=rent[name],
                aidat=aidat,
                tenant_pay=tenant[name],
            )
        )
    return units, vacancy


SPECS = [
    ("piyasa_tufe", "piyasa", "tufe", "elektrik"),
    ("piyasa_sabit_kira", "piyasa", "none", "elektrik"),
    ("hekis_tufe", "hekis", "tufe", "elektrik"),
    ("hekis_sabit_kira", "hekis", "none", "elektrik"),
    ("sosyal_tufe", "sosyal", "tufe", "elektrik"),
    ("esenyurt_tufe", "esenyurt", "tufe", "elektrik"),
    ("esenyurt_sub20_tufe", "esenyurt_sub20", "tufe", "elektrik"),
    ("hekis_bos_stok", "hekis", "tufe", "bos_stok"),
]


def run_one(obs: dict, spec: tuple, path_name: str, realistic: bool, aidat: float | None = None, bakim: float | None = None):
    """realistic: kira 12 aylik TUFE ortalamasiyla, bakim gideri ile. Degilse eski saf TUFE, gidersiz."""
    name, mode, rent_index, vacancy_key = spec
    paths = inflation_paths(obs)
    index = [1.0] * 20
    index[2] = 0.9
    if realistic and rent_index == "tufe":
        rent_index = "tufe_ort12"
    units, vacancy = build_units(obs, mode, vacancy_key, aidat)
    params = Params(
        vacancy=vacancy,
        collection=0.98,
        rent_index=rent_index,
        settle_in_hekis=True,
        horizon=20,
        opex_rate=(obs["opex"]["bakim_orani_giris_degeri"] if bakim is None else bakim) if realistic else 0.0,
        tax_rate=obs["opex"]["emlak_vergisi_orani"] if realistic else 0.0,
        unit_fixed=obs["opex"]["dask_tl_daire_yil"] if realistic else 0.0,
        vacant_aidat=realistic,
        prev_inflation=obs["inflation_annual"]["2026_agustos_yoy"],
    )
    return simulate(units, paths[path_name], index, params, name=name)


def run_bound(obs: dict | None = None, path_name: str = "ovp", realistic: bool = True) -> list[str]:
    obs = obs or load_obs()
    return [format_report(run_one(obs, spec, path_name, realistic)) for spec in SPECS]


def matrix(obs: dict | None = None) -> str:
    """Eski donuk-TUFE kosusu ile gerceklige uyarlanmis kosunun yan yana karsilastirmasi."""
    obs = obs or load_obs()
    tl = lambda v: f"{v / 1e9:,.1f}".replace(",", ".")
    cols = ("A) eski: donuk %31,5", "B) A + kira gecikmesi + gider", "C) B + OVP enflasyon yolu")
    lines = [f"{'kosu':<22}" + "".join(f"{c:>31}" for c in cols), f"{'':<22}" + f"{'odenen  yuk(mr TL, bugunku)':>31}" * 3]
    for spec in SPECS:
        cells = []
        for path_name, realistic in (("hold_last", False), ("hold_last", True), ("ovp", True)):
            r = run_one(obs, spec, path_name, realistic)
            cells.append(f"{r.real_eroded:5.0%}  {tl(r.total_fiscal_real):>8}")
        lines.append(f"{spec[0]:<22}" + "".join(f"{c:>31}" for c in cells))
    return "\n".join(lines)


def sensitivity(obs: dict | None = None) -> str:
    """Aidat (semt araligi) ve bakim orani duyarliligi. OVP yolu, gercekci kosu."""
    obs = obs or load_obs()
    a = obs["aidat"]
    aidats = (("TR ort.", a["turkiye_ortalama_tl_ay"]), ("Catalca", a["istanbul_en_ucuz_catalca_tl_ay"]),
              ("Ist. ort.", a["istanbul_ortalama_tl_ay"]), ("Besiktas", a["istanbul_en_pahali_besiktas_tl_ay"]))
    tl = lambda v: f"{v / 1e9:,.1f}".replace(",", ".")
    lines = []
    for spec in (SPECS[0], SPECS[2], SPECS[7]):
        lines.append(f"{spec[0]}  (odenen % / yuk mr TL; bakim %0,5 | %1 | %2)")
        for label, value in aidats:
            cells = []
            for bakim in (0.005, 0.01, 0.02):
                r = run_one(obs, spec, "ovp", True, value, bakim)
                cells.append(f"{r.real_eroded:4.0%}/{tl(r.total_fiscal_real):>5}")
            lines.append(f"  {label:<10}{value:>6} TL/ay  " + "   ".join(cells))
    return "\n".join(lines)
