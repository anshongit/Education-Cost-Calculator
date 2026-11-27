"""Education cost & loan calculation logic (pure Python, no UI code).

Assumptions:
- Loan is disbursed at the start of each academic year.
- During the moratorium (course period + grace months) simple interest accrues
  on every disbursed amount, and is added to the principal when repayment starts.
- After the moratorium, the loan is repaid in equal monthly instalments (EMI).
"""

from dataclasses import dataclass


def emi(principal: float, annual_rate_pct: float, months: int) -> float:
    """Standard EMI formula: P*r*(1+r)^n / ((1+r)^n - 1). Handles 0% interest."""
    if months <= 0:
        raise ValueError("Tenure must be at least 1 month")
    r = annual_rate_pct / 12 / 100
    if r == 0:
        return principal / months
    factor = (1 + r) ** months
    return principal * r * factor / (factor - 1)


def emi_salary_percentage(monthly_emi: float, annual_salary: float) -> float:
    """Return monthly EMI as a percentage of gross monthly salary."""
    if monthly_emi < 0:
        raise ValueError("EMI cannot be negative")
    if annual_salary <= 0:
        raise ValueError("Annual salary must be positive")
    return monthly_emi / (annual_salary / 12) * 100


def moratorium_interest(yearly_disbursement: float, years: int,
                        annual_rate_pct: float, moratorium_months: int) -> float:
    """Simple interest accrued before repayment starts.

    Year k's disbursement (k = 0, 1, ...) is made at month 12*k and accrues
    interest until the moratorium ends.
    """
    r = annual_rate_pct / 12 / 100
    total = 0.0
    for k in range(years):
        months_accruing = max(moratorium_months - 12 * k, 0)
        total += yearly_disbursement * r * months_accruing
    return total


@dataclass
class LoanResult:
    total_course_cost: float
    own_contribution: float
    loan_amount: float
    interest_during_moratorium: float
    principal_at_repayment_start: float
    emi: float
    total_repayment: float
    total_interest: float
    total_cost_of_education: float
    schedule: list  # list of dicts: month, opening, interest, principal, closing


def calculate(yearly_cost: float, years: int, loan_pct: float,
              annual_rate_pct: float, moratorium_months: int,
              repayment_years: int) -> LoanResult:
    """Run the full calculation and build the month-by-month schedule."""
    if years <= 0 or repayment_years <= 0:
        raise ValueError("Years must be positive")
    if not 0 <= loan_pct <= 100:
        raise ValueError("Loan percentage must be between 0 and 100")
    if annual_rate_pct < 0 or moratorium_months < 0 or yearly_cost < 0:
        raise ValueError("Values cannot be negative")

    total_cost = yearly_cost * years
    loan_amount = total_cost * loan_pct / 100
    own = total_cost - loan_amount

    yearly_disbursement = loan_amount / years
    accrued = moratorium_interest(yearly_disbursement, years,
                                  annual_rate_pct, moratorium_months)
    start_principal = loan_amount + accrued

    n = repayment_years * 12
    monthly = emi(start_principal, annual_rate_pct, n) if start_principal > 0 else 0.0

    r = annual_rate_pct / 12 / 100
    balance = start_principal
    schedule = []
    for m in range(1, n + 1):
        interest = balance * r
        principal_part = monthly - interest
        closing = max(balance - principal_part, 0.0)
        schedule.append({
            "month": m,
            "opening": balance,
            "interest": interest,
            "principal": principal_part,
            "closing": closing,
        })
        balance = closing

    total_repayment = monthly * n
    total_interest = total_repayment - loan_amount  # includes moratorium interest
    return LoanResult(
        total_course_cost=total_cost,
        own_contribution=own,
        loan_amount=loan_amount,
        interest_during_moratorium=accrued,
        principal_at_repayment_start=start_principal,
        emi=monthly,
        total_repayment=total_repayment,
        total_interest=total_interest,
        total_cost_of_education=own + total_repayment,
        schedule=schedule,
    )


def inr(x: float) -> str:
    """Format a number in Indian grouping, e.g. 1250000 -> ₹12,50,000."""
    s = str(int(round(abs(x))))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-₹" if x < 0 else "₹") + s