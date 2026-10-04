"""HEKIS stok-akim modeli.

Hedef Endeksli Kapali Ic Senet. Uc defter ayri tutulur:
mulkiyet (anapara), oturan (fiili kira), senet (havuz nakdi).
Bu ucu esitlemek cifte yazimdir.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class UnitType:
    name: str
    count: int
    price: float
    rent: float
    aidat: float
    tenant_pay: float


@dataclass
class Params:
    vacancy: float = 0.05
    collection: float = 0.98
    real_coupon: float = 0.0
    premium_alpha: float = 0.04
    premium_cap: float = 0.10
    index_threshold: float = 1.0
    quota_cut: float = 0.5
    production_share: float = 0.0
    settle_in_hekis: bool = True
    leakage_rate: float = 0.70
    horizon: int = 20
    rent_index: str = "none"

    def validate(self) -> None:
        if not 0 <= self.vacancy < 1:
            raise ValueError("vacancy 0 ile 1 arasinda olmali")
        if not 0 < self.collection <= 1:
            raise ValueError("collection 0 ile 1 arasinda olmali")
        if self.premium_cap < 0:
            raise ValueError("premium_cap negatif olamaz")
        if not 0 <= self.production_share <= 1:
            raise ValueError("production_share 0 ile 1 arasinda olmali")
        if not 0 <= self.leakage_rate <= 1:
            raise ValueError("leakage_rate 0 ile 1 arasinda olmali")
        if self.horizon < 1:
            raise ValueError("horizon en az 1")
        if self.rent_index not in ("none", "tufe"):
            raise ValueError("rent_index none veya tufe olmali")


@dataclass
class YearRow:
    year: int
    inflation: float
    cpi: float
    physical_index: float
    principal_nominal: float
    principal_real: float
    pool_net: float
    subsidy: float
    premium: float
    fiscal_gap: float
    production_transfer: float
    quota: float
    real_principal_change: float


@dataclass
class Result:
    name: str
    entry_value: float
    wealth_locked: float
    wealth_leaked: float
    static_payback_years: float
    rows: list[YearRow] = field(default_factory=list)

    @property
    def end_real_principal(self) -> float:
        return self.rows[-1].principal_real if self.rows else 0.0

    @property
    def total_subsidy(self) -> float:
        return sum(r.subsidy for r in self.rows)

    @property
    def total_premium(self) -> float:
        return sum(r.premium for r in self.rows)

    @property
    def total_fiscal(self) -> float:
        return sum(r.subsidy + r.premium + r.fiscal_gap for r in self.rows)

    @property
    def real_eroded(self) -> float:
        if not self.rows or self.wealth_locked <= 0:
            return 0.0
        return 1 - self.end_real_principal / self.wealth_locked


def _load_units(raw: Iterable[dict]) -> list[UnitType]:
    return [UnitType(**item) for item in raw]


def static_payback(units: list[UnitType], params: Params) -> float:
    """Fiyat / yillik net havuz. Aidat borc servisine girmez."""
    value = sum(u.count * u.price for u in units)
    net = 0.0
    for u in units:
        net += (u.rent - u.aidat) * 12 * u.count * (1 - params.vacancy) * params.collection
    if net <= 0:
        return float("inf")
    return value / net


def pool_and_subsidy(units: list[UnitType], params: Params) -> tuple[float, float]:
    pool = 0.0
    subsidy = 0.0
    occupied = 1 - params.vacancy
    for u in units:
        pool += (u.rent - u.aidat) * 12 * u.count * occupied * params.collection
        gap = max(0.0, u.rent - u.tenant_pay)
        subsidy += gap * 12 * u.count * occupied
    return pool, subsidy


def simulate(
    units: list[UnitType],
    inflation: list[float],
    physical_index: list[float],
    params: Params,
    name: str = "baseline",
) -> Result:
    params.validate()
    n = params.horizon
    if len(inflation) < n or len(physical_index) < n:
        raise ValueError("enflasyon ve fiziki endeks serisi horizon kadar olmali")

    entry = sum(u.count * u.price for u in units)
    if params.settle_in_hekis:
        locked, leaked = entry, 0.0
        real_principal = entry
    else:
        locked = entry * (1 - params.leakage_rate)
        leaked = entry * params.leakage_rate
        real_principal = locked

    cpi = 1.0
    quota = 1.0
    rows: list[YearRow] = []
    pool0, subsidy0 = pool_and_subsidy(units, params)

    for year in range(1, n + 1):
        pi = inflation[year - 1]
        cpi *= 1 + pi
        x = physical_index[year - 1]
        scale = cpi if params.rent_index == "tufe" else 1.0
        pool = pool0 * scale
        subsidy = subsidy0 * scale

        production = quota * params.production_share * pool
        service_cash = pool - production
        real_service = service_cash / cpi
        coupon_due = params.real_coupon * real_principal
        real_available = real_service - coupon_due

        if real_available >= 0:
            paid_down = min(real_principal, real_available)
            real_principal -= paid_down
            fiscal_gap = 0.0
            change = -paid_down
        else:
            fiscal_gap = -real_available * cpi
            change = 0.0

        if x >= params.index_threshold:
            raw = params.premium_alpha * (x - params.index_threshold) * real_principal * cpi
            premium = min(raw, params.premium_cap * real_principal * cpi)
            quota = min(1.0, quota * 1.25)
        else:
            premium = 0.0
            quota *= params.quota_cut

        rows.append(
            YearRow(
                year=year,
                inflation=pi,
                cpi=cpi,
                physical_index=x,
                principal_nominal=real_principal * cpi,
                principal_real=real_principal,
                pool_net=pool,
                subsidy=subsidy,
                premium=premium,
                fiscal_gap=fiscal_gap,
                production_transfer=production,
                quota=quota,
                real_principal_change=change,
            )
        )

    return Result(
        name=name,
        entry_value=entry,
        wealth_locked=locked,
        wealth_leaked=leaked,
        static_payback_years=static_payback(units, params),
        rows=rows,
    )


def load_scenario(path: str | Path) -> tuple[list[UnitType], list[float], list[float], Params, str]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    units = _load_units(data["units"])
    params = Params(**data.get("params", {}))
    return units, data["inflation"], data["physical_index"], params, data.get("name", Path(path).stem)


def result_to_dict(result: Result) -> dict:
    return {
        "name": result.name,
        "entry_value": result.entry_value,
        "wealth_locked": result.wealth_locked,
        "wealth_leaked": result.wealth_leaked,
        "static_payback_years": result.static_payback_years,
        "end_real_principal": result.end_real_principal,
        "real_eroded": result.real_eroded,
        "total_subsidy": result.total_subsidy,
        "total_premium": result.total_premium,
        "total_fiscal": result.total_fiscal,
        "rows": [asdict(r) for r in result.rows],
    }


def format_report(result: Result) -> str:
    tl = lambda v: f"{v:,.0f}".replace(",", ".")
    lines = [
        f"senaryo: {result.name}",
        f"giris degeri: {tl(result.entry_value)} TL",
        f"HEKIS'e kilitlenen servet: {tl(result.wealth_locked)} TL",
        f"nakit kacisi: {tl(result.wealth_leaked)} TL",
        f"statik geri donus: {result.static_payback_years:.1f} yil",
        f"20. yil reel anapara: {tl(result.end_real_principal)} TL",
        f"reel anapara erimesi: {result.real_eroded:.1%}",
        f"toplam butce transferi (kira farki): {tl(result.total_subsidy)} TL",
        f"toplam hedef primi: {tl(result.total_premium)} TL",
        f"toplam mali acik (fark + prim + kupon acigi): {tl(result.total_fiscal)} TL",
        "",
        "yil  enflasyon  fiziki  reel anapara   havuz neti    subvansiyon      prim     kota",
    ]
    for r in result.rows:
        if r.year in (1, 5, 10, 15, 20) or r.year == len(result.rows):
            lines.append(
                f"{r.year:3d}  {r.inflation:8.1%}  {r.physical_index:6.2f}  "
                f"{tl(r.principal_real):>14}  {tl(r.pool_net):>12}  {tl(r.subsidy):>12}  "
                f"{tl(r.premium):>10}  {r.quota:5.2f}"
            )
    return "\n".join(lines)
