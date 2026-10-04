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


if __name__ == "__main__":
    unittest.main()
