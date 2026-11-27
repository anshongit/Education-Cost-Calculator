import itertools
import unittest

from loan_calc import calculate, emi_salary_percentage


class AffordabilityScenarioTests(unittest.TestCase):
    def test_all_input_boundary_combinations(self):
        loan_shares = (0, 50, 100)
        interest_rates = (0, 9.5, 20)
        grace_periods = (0, 6, 24)
        repayment_periods = (1, 10, 20)
        annual_salary = 600000

        for loan_pct, rate, grace, repayment_years in itertools.product(
            loan_shares, interest_rates, grace_periods, repayment_periods
        ):
            with self.subTest(
                loan_pct=loan_pct,
                rate=rate,
                grace=grace,
                repayment_years=repayment_years,
            ):
                result = calculate(
                    yearly_cost=180000,
                    years=4,
                    loan_pct=loan_pct,
                    annual_rate_pct=rate,
                    moratorium_months=4 * 12 + grace,
                    repayment_years=repayment_years,
                )
                percentage = emi_salary_percentage(result.emi, annual_salary)

                self.assertAlmostEqual(
                    result.loan_amount, 180000 * 4 * loan_pct / 100
                )
                self.assertEqual(len(result.schedule), repayment_years * 12)
                self.assertAlmostEqual(
                    percentage, result.emi / (annual_salary / 12) * 100
                )
                if loan_pct == 0:
                    self.assertEqual(result.emi, 0)
                    self.assertEqual(percentage, 0)
                else:
                    self.assertGreater(result.emi, 0)
                    self.assertAlmostEqual(result.schedule[-1]["closing"], 0)

    def test_loan_share_rate_grace_and_term_change_affordability(self):
        def result(loan_pct=50, rate=9.5, grace=6, repayment_years=10):
            return calculate(
                yearly_cost=180000,
                years=4,
                loan_pct=loan_pct,
                annual_rate_pct=rate,
                moratorium_months=4 * 12 + grace,
                repayment_years=repayment_years,
            )

        baseline = result()
        self.assertGreater(result(loan_pct=100).emi, baseline.emi)
        self.assertGreater(result(rate=15).emi, baseline.emi)
        self.assertGreater(result(grace=24).emi, baseline.emi)
        self.assertLess(result(repayment_years=20).emi, baseline.emi)
        self.assertGreater(result(repayment_years=20).total_interest, baseline.total_interest)

    def test_zero_rate_and_no_loan_have_no_interest_burden(self):
        zero_rate = calculate(180000, 4, 100, 0, 48, 10)
        no_loan = calculate(180000, 4, 0, 9.5, 54, 10)

        self.assertEqual(zero_rate.interest_during_moratorium, 0)
        self.assertEqual(zero_rate.total_interest, 0)
        self.assertEqual(no_loan.emi, 0)
        self.assertEqual(no_loan.total_interest, 0)

    def test_salary_burden_percentage_and_salary_validation(self):
        self.assertAlmostEqual(emi_salary_percentage(20000, 600000), 40)
        self.assertAlmostEqual(emi_salary_percentage(25000, 600000), 50)
        with self.assertRaises(ValueError):
            emi_salary_percentage(1000, 0)


if __name__ == "__main__":
    unittest.main()
