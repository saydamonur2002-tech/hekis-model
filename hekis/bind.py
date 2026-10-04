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
    return {"hold_last": hold, "disinflation_varsayim": disinflation, "realized_2021_2025": realized}


def build_units(obs: dict, rent_mode: str, vacancy_key: str = "elektrik") -> tuple[list[UnitType], float]:
    price = prices_from_m2(obs)
    if rent_mode == "piyasa":
        rent = market_rents(obs)
        tenant = rent
    elif rent_mode == "esenyurt":
        rent = esenyurt_rents(obs)
        tenant = rent
        price = prices_from_m2(obs, "esenyurt_m2_tl")
    elif rent_mode == "esenyurt_sub20":
        rent = esenyurt_rents(obs)
        tenant = {name: rent[name] * 0.80 for name in SIZES}
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
    aidat = obs["policy_rent"]["aidat"]
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


def run_bound(obs: dict | None = None) -> list[str]:
    obs = obs or load_obs()
    paths = inflation_paths(obs)
    index = [1.0] * 20
    index[2] = 0.9
    reports = []
    specs = [
        ("piyasa_tufe", "piyasa", "tufe", "hold_last", "elektrik"),
        ("piyasa_sabit_kira", "piyasa", "none", "hold_last", "elektrik"),
        ("hekis_tufe", "hekis", "tufe", "hold_last", "elektrik"),
        ("hekis_sabit_kira", "hekis", "none", "hold_last", "elektrik"),
        ("sosyal_tufe", "sosyal", "tufe", "hold_last", "elektrik"),
        ("esenyurt_tufe", "esenyurt", "tufe", "hold_last", "elektrik"),
        ("esenyurt_sub20_tufe", "esenyurt_sub20", "tufe", "hold_last", "elektrik"),
        ("hekis_bos_stok", "hekis", "tufe", "hold_last", "bos_stok"),
    ]
    for name, mode, rent_index, path_name, vacancy_key in specs:
        units, vacancy = build_units(obs, mode, vacancy_key)
        params = Params(
            vacancy=vacancy,
            collection=0.98,
            rent_index=rent_index,
            settle_in_hekis=True,
            horizon=20,
        )
        result = simulate(units, paths[path_name], index, params, name=name)
        reports.append(format_report(result))
    return reports
