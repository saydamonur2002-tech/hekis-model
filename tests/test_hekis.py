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


if __name__ == "__main__":
    unittest.main()
