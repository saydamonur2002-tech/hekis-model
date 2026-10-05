import math
import unittest

from hekis import activation
from hekis.bind import SPECS, build_units, inflation_paths, load_obs, run_one
from hekis.model import Params, UnitType, holding_cost, simulate, static_payback

OBS = load_obs()


def unit(rent=30000.0, aidat=0.0, price=3_000_000.0, count=100, tenant=None):
    return UnitType("t", count, price, rent, aidat, rent if tenant is None else tenant)


class ModelTests(unittest.TestCase):
    def test_principal_conserved(self):
        units = [unit()]
        r = simulate(units, [0.3] * 20, [1.0] * 20, Params(rent_index="tufe_ort12", opex_rate=0.01))
        paid = -sum(x.real_principal_change for x in r.rows)
        self.assertAlmostEqual(paid + r.end_real_principal, r.entry_value, places=2)

    def test_principal_never_negative(self):
        r = simulate([unit(rent=200000)], [0.3] * 20, [1.0] * 20, Params(rent_index="tufe"))
        self.assertTrue(all(x.principal_real >= -1e-6 for x in r.rows))

    def test_zero_rent_repays_nothing(self):
        r = simulate([unit(rent=0.0)], [0.3] * 20, [1.0] * 20, Params())
        self.assertAlmostEqual(r.end_real_principal, r.entry_value)

    def test_payback_monotone_in_rent(self):
        lo = static_payback([unit(rent=20000)], Params())
        hi = static_payback([unit(rent=40000)], Params())
        self.assertGreater(lo, hi)

    def test_costs_reduce_repayment(self):
        u = [unit(rent=12000)]
        a = simulate(u, [0.3] * 20, [1.0] * 20, Params(rent_index="tufe"))
        b = simulate(u, [0.3] * 20, [1.0] * 20, Params(rent_index="tufe", opex_rate=0.02, tax_rate=0.002))
        self.assertLess(a.real_eroded, 1.0)
        self.assertGreater(a.real_eroded, b.real_eroded)

    def test_vacant_aidat_counts_only_vacancy(self):
        u = [unit(aidat=3000)]
        base = holding_cost(u, Params(vacancy=0.1))
        with_v = holding_cost(u, Params(vacancy=0.1, vacant_aidat=True))
        self.assertAlmostEqual(with_v - base, 3000 * 12 * 100 * 0.1)

    def test_subsidy_is_gap_only(self):
        r = simulate([unit(rent=30000, tenant=30000)], [0.3] * 20, [1.0] * 20, Params())
        self.assertEqual(r.total_subsidy, 0.0)

    def test_ovp_path_matches_source(self):
        p = inflation_paths(OBS)["ovp"]
        self.assertEqual(p[:4], [0.284, 0.21, 0.135, 0.09])
        self.assertEqual(len(p), 20)

    def test_all_specs_run_and_are_finite(self):
        for spec in SPECS:
            for path in ("hold_last", "ovp"):
                for realistic in (False, True):
                    r = run_one(OBS, spec, path, realistic)
                    self.assertTrue(math.isfinite(r.end_real_principal))
                    self.assertGreaterEqual(r.real_eroded, -1e-9)
                    self.assertLessEqual(r.real_eroded, 1.0 + 1e-9)

    def test_realistic_costs_never_help(self):
        # Ayni enflasyon yolunda gider ve kira gecikmesi geri odemeyi artirmaz.
        for spec in SPECS:
            a = run_one(OBS, spec, "hold_last", False).real_eroded
            b = run_one(OBS, spec, "hold_last", True).real_eroded
            self.assertLessEqual(b, a + 1e-9, spec[0])


class ParticipationTests(unittest.TestCase):
    def test_bounds(self):
        for g in (-0.5, 0, 0.5):
            p = activation.participation(g, 0.01)
            self.assertGreaterEqual(p, 0.0)
            self.assertLessEqual(p, 0.40)

    def test_monotone_in_expected_growth(self):
        ps = [activation.participation(g, 0.01) for g in (-0.1, 0.0, 0.1, 0.4)]
        self.assertEqual(ps, sorted(ps, reverse=True))

    def test_monotone_in_fee(self):
        ps = [activation.participation(0.05, 0.01, f) for f in (0.0, 0.01, 0.05)]
        self.assertEqual(ps, sorted(ps))

    def test_boom_blocks_participation(self):
        self.assertLess(activation.participation(0.37, 0.01), 0.001)

    def test_scale_linear_in_units(self):
        a = activation.run(OBS, {"orta": 0.5, "ucuz": 0.5}, 1000)
        b = activation.run(OBS, {"orta": 0.5, "ucuz": 0.5}, 2000)
        self.assertAlmostEqual(b.entry_value / a.entry_value, 2.0, places=2)
        self.assertAlmostEqual(b.real_eroded, a.real_eroded, places=3)


class PoliticsTests(unittest.TestCase):
    def test_income_model_matches_top_quintile(self):
        from hekis import politics
        top, bottom = politics.share_check()
        self.assertAlmostEqual(top, 0.48, delta=0.01)
        self.assertAlmostEqual(bottom, 0.064, delta=0.02)

    def test_subsidy_falls_with_alpha_and_cut(self):
        from hekis import politics
        base = politics.graduated(16825.0, 0.30, 0.4)[1]
        self.assertLess(politics.graduated(16825.0, 0.40, 0.4)[1], base)
        self.assertLess(politics.graduated(16825.0, 0.30, 0.6)[1], base)

    def test_pay_plus_subsidy_is_rent(self):
        from hekis import politics
        pay, sub = politics.graduated(16825.0, 0.30, 0.4)
        self.assertAlmostEqual(pay + sub, 16825.0)


class PropertyTests(unittest.TestCase):
    """Rastgele girdilerle degismez testleri. Tohum sabit, tekrarlanabilir."""

    def test_random_units_conserve_principal(self):
        import random
        rng = random.Random(7)
        for _ in range(200):
            u = unit(rent=rng.uniform(0, 80000), aidat=rng.uniform(0, 8000), price=rng.uniform(1e6, 1e7),
                     count=rng.randint(1, 500), tenant=rng.uniform(0, 80000))
            r = simulate([u], [rng.uniform(0, 0.8)] * 20, [1.0] * 20,
                         Params(rent_index=rng.choice(["none", "tufe", "tufe_ort12"]), opex_rate=rng.uniform(0, 0.03),
                                vacancy=rng.uniform(0, 0.3), collection=rng.uniform(0.5, 1.0)))
            paid = -sum(x.real_principal_change for x in r.rows)
            self.assertAlmostEqual(paid + r.end_real_principal, r.entry_value, delta=1e-6 * r.entry_value)
            self.assertTrue(all(x.principal_real >= -1e-6 for x in r.rows))

    def test_rent_doubling_doubles_pool(self):
        a = simulate([unit(rent=20000)], [0.3] * 20, [1.0] * 20, Params(rent_index="tufe"))
        b = simulate([unit(rent=40000)], [0.3] * 20, [1.0] * 20, Params(rent_index="tufe"))
        self.assertAlmostEqual(b.rows[0].pool_net / a.rows[0].pool_net, 2.0, places=6)

    def test_luxury_response_monotone_and_bounded(self):
        from hekis import final
        fees = [i / 100 for i in range(0, 30)]
        rs = [final.lux_response(f) for f in fees]
        self.assertEqual(rs, sorted(rs))
        self.assertLessEqual(max(rs), final.LUX_CAP + 1e-12)
        self.assertEqual(rs[0], 0.0)

    def test_effective_collection_nonincreasing_with_floor(self):
        from hekis import final
        cs = [final.effective_collection(i / 100, 0.6) for i in range(0, 40)]
        self.assertEqual(cs, sorted(cs, reverse=True))
        self.assertGreaterEqual(min(cs), final.AVOID_FLOOR)

    def test_luxury_revenue_has_interior_peak(self):
        from hekis import final
        revs = [final.lux_economics(OBS, 0.6, 0.2, i / 1000, 0.6)[2] for i in range(1, 151)]
        peak = revs.index(max(revs))
        self.assertGreater(peak, 5)
        self.assertLess(peak, 149)
        self.assertTrue(all(r >= 0 for r in revs))

    def test_evaluate_finite_on_random_draws(self):
        import random
        from hekis import evaluate as E
        rng = random.Random(11)
        for _ in range(150):
            P = {k: rng.triangular(lo, hi, mode) for k, (lo, mode, hi) in E.SPACE.items()}
            o = E.evaluate(P)
            for k in ("p", "N", "sub1", "yuk", "odenen", "rev", "ratio"):
                self.assertTrue(math.isfinite(o[k]), (k, o[k]))
            self.assertGreaterEqual(o["p"], 0.0)
            self.assertLessEqual(o["p"], 0.60 + 1e-9)
            self.assertGreaterEqual(o["odenen"], -1e-9)
            self.assertLessEqual(o["odenen"], 1.0 + 1e-9)

    def test_ratio_invariant_to_stock_size(self):
        # Hem yerlesen hem bedel tabani stokla dogrusal: oran stoktan bagimsiz olmali.
        from hekis import evaluate as E
        a = E.evaluate({"stok": 225_000})["ratio"]
        b = E.evaluate({"stok": 750_000})["ratio"]
        self.assertAlmostEqual(a, b, delta=0.02)

    def test_more_fee_more_participation_less_or_equal_base(self):
        from hekis import evaluate as E
        lo = E.evaluate({"fee": 0.005})
        hi = E.evaluate({"fee": 0.05})
        self.assertGreaterEqual(hi["N"], lo["N"] - 1)

    def test_zero_expected_growth_boom_kills_participation(self):
        from hekis import evaluate as E
        self.assertLess(E.evaluate({"g_e": 0.40})["N"], 1000)

    def test_monte_carlo_reproducible(self):
        from hekis import evaluate as E
        _, a = E.monte_carlo(30, seed=5)
        _, b = E.monte_carlo(30, seed=5)
        self.assertEqual([x["ratio"] for x in a], [x["ratio"] for x in b])

    def test_scale_bin_erosion_holds(self):
        # Olcek buyudukce kendini finanse etme azalir: Spearman(daire, oran) belirgin negatif.
        from hekis import evaluate as E
        _, outs = E.monte_carlo(400, seed=3)
        rho = E.spearman([o["N"] for o in outs], [o["ratio"] for o in outs])
        self.assertLess(rho, -0.5)


class RealityTests(unittest.TestCase):
    def test_gini_unchanged_without_benefit(self):
        from hekis import reality
        g0, g1, p0, p1 = reality.gini_with_benefit(0, 50000)
        self.assertAlmostEqual(g0, g1, places=9)
        self.assertAlmostEqual(p0, p1, places=9)

    def test_benefit_to_poor_reduces_gini_and_poverty(self):
        from hekis import reality
        g0, g1, p0, p1 = reality.gini_with_benefit(500_000, 80000)
        self.assertLess(g1, g0)
        self.assertLessEqual(p1, p0)

    def test_ols_recovers_line(self):
        from hekis import reality
        a, b, r2 = reality.ols([0, 1, 2, 3], [1, 3, 5, 7])
        self.assertAlmostEqual(a, 1.0)
        self.assertAlmostEqual(b, 2.0)
        self.assertAlmostEqual(r2, 1.0)

    def test_interest_channel_slope_negative(self):
        from hekis import reality
        xs = [reality.RR_HIST[y] for y in sorted(reality.RR_HIST)]
        ys = [reality.G_HIST[y] for y in sorted(reality.RR_HIST)]
        self.assertLess(reality.ols(xs, ys)[1], 0)


class CityTests(unittest.TestCase):
    def test_istanbul_factors_are_identity(self):
        from hekis import cities
        ci = cities.city_inputs(OBS, "istanbul")
        self.assertAlmostEqual(ci["fp"], 1.0)
        self.assertAlmostEqual(ci["fr"], 1.0)

    def test_istanbul_run_matches_plain_evaluate(self):
        from hekis import cities, evaluate as E
        ci = cities.city_inputs(OBS, "istanbul")
        a = cities.run_city(OBS, "istanbul")
        P = {**cities.LIKELY, "stok": ci["stok"], "g_e": ci["g_e"]}
        b = E.evaluate(P)
        self.assertAlmostEqual(a["N"], b["N"], places=6)
        self.assertAlmostEqual(a["ratio"], b["ratio"], places=9)

    def test_all_cities_finite_and_population_shares(self):
        from hekis import cities
        tot_pop = 0
        for c in cities.CITIES:
            o = cities.run_city(OBS, c)
            for k in ("N", "sub1", "rev", "yuk", "ratio"):
                self.assertTrue(math.isfinite(o[k]), (c, k))
            tot_pop += o["pop"]
        self.assertGreater(tot_pop / 86_092_168, 0.40)
        self.assertLess(tot_pop / 86_092_168, 0.50)

    def test_vacant_stock_scales_with_population(self):
        from hekis import cities
        a = cities.city_inputs(OBS, "ankara")
        i = cities.city_inputs(OBS, "istanbul")
        self.assertAlmostEqual(a["stok"] / i["stok"], a["pop"] / i["pop"], places=9)
        self.assertAlmostEqual(i["stok"], 450_000, delta=500)


class ZoneTests(unittest.TestCase):
    def test_band_factors_average_to_one(self):
        from hekis import zones
        qs = [0.0, 0.41, 0.80, 1.0]
        total = sum((qs[i + 1] - qs[i]) * zones.band_factor(qs[i], qs[i + 1], 0.6) for i in range(3))
        self.assertAlmostEqual(total, 1.0, places=9)

    def test_zone_stock_partitions_and_outputs_finite(self):
        from hekis import zones
        z = zones.run_three_zone()
        self.assertAlmostEqual(sum(z["S"]), 450_000, delta=1)
        for k in ("N", "sub1", "yuk", "rev", "ratio", "coverage"):
            self.assertTrue(math.isfinite(z[k]), k)
        self.assertLess(z["V"][0], z["V"][1])
        self.assertLess(z["V"][1], z["V"][2])

    def test_wider_pool_band_houses_more(self):
        from hekis import zones
        self.assertLess(zones.run_three_zone(q_h=0.30)["N"], zones.run_three_zone(q_h=0.65)["N"])


class StalledTests(unittest.TestCase):
    def test_base_is_30k_and_below_claim(self):
        from hekis import stalled
        self.assertEqual(stalled.N_STALLED, 30_000)
        self.assertLess(stalled.N_STALLED, stalled.N_CLAIM)

    def test_unit_economics_positive_and_cheaper_capital_than_stock(self):
        from hekis import stalled
        ue = stalled.unit_economics(OBS)
        self.assertGreater(ue["net"], 0)
        c = 0.20 * stalled.COST_MID * stalled.AREA
        self.assertLess(c, ue["value"])
        self.assertLess(c / ue["net"], 10)  # geri odeme 10 yildan kisa


class PoolRentTests(unittest.TestCase):
    def test_mult_one_is_identity(self):
        from hekis import zones
        a = zones.run_three_zone()
        b = zones.run_three_zone(pool_rent_mult=1.0, senet_coupling=True)
        self.assertAlmostEqual(a["N"], b["N"], places=6)
        self.assertAlmostEqual(a["sub1"], b["sub1"], places=6)

    def test_lower_pool_rent_lowers_subsidy_and_repayment(self):
        from hekis import zones
        a = zones.run_three_zone(pool_rent_mult=1.0)
        b = zones.run_three_zone(pool_rent_mult=0.7, senet_coupling=False)
        self.assertLess(b["sub1"], a["sub1"])
        self.assertLess(b["paid"], a["paid"] + 1e-9)
        self.assertAlmostEqual(a["N"], b["N"], places=6)  # baglanti kapaliyken katilim ayni

    def test_coupling_lowers_participation(self):
        from hekis import zones
        off = zones.run_three_zone(pool_rent_mult=0.7, senet_coupling=False)
        on = zones.run_three_zone(pool_rent_mult=0.7, senet_coupling=True)
        self.assertLess(on["N"], off["N"])

    def test_bind_esenyurt_modes_scale_pool_rent_not_social(self):
        from hekis.bind import build_units
        base, _ = build_units(OBS, "esenyurt_sosyal")
        scaled, _ = build_units(OBS, "esenyurt_sosyal", rent_mult=0.8)
        self.assertAlmostEqual(scaled[0].rent, base[0].rent * 0.8)
        self.assertAlmostEqual(scaled[0].tenant_pay, base[0].tenant_pay)  # oturan payi ayri


class AnadoluTests(unittest.TestCase):
    def test_all_cities_run_and_finite(self):
        from hekis import anadolu
        for c in anadolu.ANADOLU:
            o = anadolu.run(OBS, c)
            for k in ("N", "sub1", "rev", "yuk", "ratio", "coverage"):
                self.assertTrue(math.isfinite(o[k]), (c, k))
            self.assertGreater(o["N"], 0)

    def test_lower_tariff_lower_revenue_and_freed_units(self):
        from hekis import anadolu
        hi = anadolu.run(OBS, "ankara", fee=0.01, lux_fee=0.05)
        lo = anadolu.run(OBS, "ankara", fee=0.005, lux_fee=0.03)
        self.assertLess(lo["rev"], hi["rev"])
        self.assertLess(lo["freed_buf"] + lo["freed_lux"], hi["freed_buf"] + hi["freed_lux"])

    def test_poorer_city_has_wider_hekis_band(self):
        from hekis import anadolu
        # memur maasi ulusal sabit: geliri dusuk sehirde ayni maas daha yuksek yuzdelige denk gelir
        self.assertGreater(anadolu.city_setup(OBS, "konya")["q_h"], anadolu.city_setup(OBS, "ankara")["q_h"])

    def test_data_complete(self):
        for c in ("ankara", "izmir", "bursa", "antalya", "konya", "adana", "kocaeli"):
            d = OBS["sehirler"][c]
            for k in ("nufus", "satis", "kira", "hane_buyuklugu", "gelir_orani"):
                self.assertIn(k, d)


if __name__ == "__main__":
    unittest.main()


class PilotTests(unittest.TestCase):
    def test_scale_invariance_and_stages(self):
        from hekis import pilot
        rows = dict(pilot.ladder())
        self.assertEqual(rows["K0 yalniz havuz"]["oran"], 0.0)
        self.assertGreater(rows["K2 + luks %5 (uc bolge)"]["oran"], rows["K1 + genel bedel %1"]["oran"])
        self.assertGreaterEqual(rows["K3 + hedef primi"]["daire"], rows["K2 + luks %5 (uc bolge)"]["daire"])

    def test_reality_checks_pass(self):
        from hekis import pilot
        self.assertTrue(all(ok for _, ok, _ in pilot.tests()))

class AnchorTests(unittest.TestCase):
    def test_anchor_scale(self):
        from hekis import anchor
        r = anchor.report()
        self.assertTrue(0.001 < r["senet_mevduat"] < 0.01)
        self.assertTrue(0.5 < r["senet_aktif"] < 2.0)


class GateTests(unittest.TestCase):
    def test_gates_frontier_monotone_and_floor_restored(self):
        from hekis import final, pilot
        before = final.AVOID_FLOOR
        g = pilot.gates()
        self.assertEqual(final.AVOID_FLOOR, before)
        lux = [l for _, l in g["frontier"]]
        self.assertEqual(lux, sorted(lux))  # genel tahsilat dustukce luks esigi yukselir
        self.assertLess(g["p_max"], 0.5)

class LuxPilotTests(unittest.TestCase):
    def test_lux_pilot_size_precision(self):
        from hekis import pilot
        n = pilot.lux_pilot_size(0.05)
        self.assertGreater(n, pilot.PILOT_STOK)
        self.assertLessEqual(pilot.gates(n)["se_lux"], 0.05 + 1e-9)

class HorizonTests(unittest.TestCase):
    def test_perfect_path_expands_and_mc_reasonable(self):
        from hekis import horizon
        det = horizon.one_path({}, None)
        sizes = [r["stok"] for r in det]
        self.assertEqual(sizes[0], 3800)
        self.assertTrue(all(b <= a * horizon.GROWTH_CAP + 1e-6 for a, b in zip(sizes, sizes[1:])))
        s = horizon.summarize(horizon.monte_carlo(60))
        self.assertGreater(s["N5"], 0)
        shocked = horizon.summarize(horizon.monte_carlo(60, shock=horizon.SHOCKS["fiyat rallisi (g_e +10 puan)"]))
        self.assertLessEqual(shocked["N5"], s["N5"])


class ShockExtraTests(unittest.TestCase):
    def test_annulment_hurts_and_freezes(self):
        from hekis import horizon
        base = horizon.summarize(horizon.monte_carlo(60))
        ann = horizon.summarize(horizon.monte_carlo(60, shock=horizon.SHOCKS["bedel iptali (hukuki)"]))
        self.assertLess(ann["net"], base["net"])
        self.assertLess(ann["size5"], base["size5"])
