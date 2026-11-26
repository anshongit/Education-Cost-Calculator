import pandas as pd
import streamlit as st

from loan_calc import calculate, inr

st.set_page_config(page_title="Education Cost Calculator", page_icon="🎓", layout="wide")

st.title("🎓 Education Cost Calculator")
st.caption("Find out what your degree will really cost once loan interest is included.")

# Illustrative sample values only (per year, in rupees). Replace with real figures from your college.
PRESETS = {
    "Custom": dict(tuition=100000, hostel=60000, other=40000),
    "Govt. engineering college (sample)": dict(tuition=80000, hostel=50000, other=30000),
    "Private engineering college (sample)": dict(tuition=200000, hostel=90000, other=60000),
}

# ---------------- Sidebar inputs ----------------
with st.sidebar:
    st.header("Course costs (per year)")
    preset = st.selectbox("Preset (illustrative)", list(PRESETS.keys()))
    p = PRESETS[preset]
    tuition = st.number_input("Tuition fees (₹)", min_value=0, value=p["tuition"], step=5000)
    hostel = st.number_input("Hostel & food (₹)", min_value=0, value=p["hostel"], step=5000)
    other = st.number_input("Books, exam & other (₹)", min_value=0, value=p["other"], step=2000)
    years = st.slider("Course duration (years)", 1, 6, 4)

    st.header("Loan details")
    loan_pct = st.slider("Share of cost covered by loan (%)", 0, 100, 80)
    rate = st.number_input("Interest rate (% per year)", min_value=0.0, value=9.5, step=0.25)
    grace = st.number_input("Grace months after course", min_value=0, value=6, step=1)
    repay_years = st.slider("Repayment period (years)", 1, 20, 10)

yearly_cost = tuition + hostel + other
moratorium = years * 12 + grace

try:
    res = calculate(yearly_cost, years, loan_pct, rate, moratorium, repay_years)
except ValueError as e:
    st.error(str(e))
    st.stop()

# ---------------- Summary cards ----------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total course cost", inr(res.total_course_cost))
c2.metric("Loan amount", inr(res.loan_amount))
c3.metric("Monthly EMI", inr(res.emi))
c4.metric("Real total cost", inr(res.total_cost_of_education),
          delta=f"+{inr(res.total_interest)} interest", delta_color="inverse")

if res.total_course_cost > 0:
    extra_pct = res.total_interest / res.total_course_cost * 100
    st.info(
        f"Interest adds **{inr(res.total_interest)}** to your costs "
        f"(about **{extra_pct:.0f}%** on top of the course fees). "
        f"Interest that builds up during the course and grace period is "
        f"**{inr(res.interest_during_moratorium)}**."
    )

# ---------------- Charts ----------------
left, right = st.columns(2)

with left:
    st.subheader("Where your money goes")
    breakdown = pd.DataFrame({
        "Amount (₹)": [res.own_contribution, res.loan_amount,
                       res.total_interest],
    }, index=["Paid by you / family", "Loan principal", "Total interest"])
    st.bar_chart(breakdown)

with right:
    st.subheader("Loan balance over time")
    df = pd.DataFrame(res.schedule)
    if not df.empty:
        st.line_chart(df.set_index("month")["closing"])
        st.caption("Balance after each monthly EMI during repayment (months).")

# ---------------- Month-by-month table ----------------
st.subheader("Month-by-month payback")
if not df.empty:
    table = df.rename(columns={
        "month": "Month", "opening": "Opening balance", "interest": "Interest",
        "principal": "Principal paid", "closing": "Closing balance",
    }).round(0)
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.download_button("Download schedule (CSV)", table.to_csv(index=False),
                       file_name="payback_schedule.csv", mime="text/csv")

with st.expander("Assumptions & disclaimer"):
    st.write(
        "- Loan is paid out at the start of each academic year.\n"
        "- Simple interest accrues during the course + grace period and is added to the "
        "principal when repayment starts.\n"
        "- After that, equal monthly instalments (EMI) are paid.\n"
        "- Preset fee values are illustrative samples, not real college fees.\n"
        "- These are estimates only. Please check actual terms with your bank."
    )