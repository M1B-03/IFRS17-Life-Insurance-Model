
"""
Core actuarial engine for the IFRS 17 GMM.
 
project_remaining() -- projects policies/cashflows forward under a given
                        assumptions dict, from any starting year.
run_model()         -- runs the full projection with CSM/RA/LC roll-forward,
                        including any scheduled reassessment events.
"""
import pandas as pd
import numpy as np

def gamma_shock(cv):
    shape = 1 / cv**2
    scale = cv**2
    return np.random.gamma(shape, scale)

def lognormal_shock(cv):
    sigma = np.sqrt(np.log(1 + cv**2))
    mu = -sigma**2 / 2
    return np.random.lognormal(mu, sigma)

def draw_shock(distribution, cv):
    if distribution == "gamma":
        return gamma_shock(cv)
    elif distribution == "lognormal":
        return lognormal_shock(cv)
    else:
        raise ValueError(f"Unknown distribution: {distribution}")
 
def project_remaining(start_year, opening_policies, assumptions, TERM, ENTRY_AGE,
                       MORTALITY, ANNUAL_PREMIUM, SUM_INSURED, ACQUISITION_EXPENSE,
                       INTEREST_RATE):
    rows = []
    policies = opening_policies
    for year in range(start_year, TERM + 1):
        age = ENTRY_AGE + year - 1
        qx = MORTALITY[age] * assumptions["mortality_multiplier"]
        opening = policies
        deaths = opening * qx
        lapses = opening * assumptions["lapse_rate"]
        closing = opening - deaths - lapses
 
        premiums = opening * ANNUAL_PREMIUM
        claims = deaths * SUM_INSURED
        expenses = opening * assumptions["annual_expense"]
        acquisition_cf = premiums * ACQUISITION_EXPENSE if year == 1 else 0
 
        df_rel = 1 / (1 + INTEREST_RATE) ** (year - (start_year - 1))
        coverage_units = opening * SUM_INSURED
 
        rows.append({
            "Year": year, "Opening Policies": opening, "Closing Policies": closing,
            "Premiums": premiums, "Claims": claims, "Expenses": expenses,
            "Acquisition CF": acquisition_cf,
            "PV Premiums": premiums * df_rel,
            "PV Outflows": (claims + expenses + acquisition_cf) * df_rel,
            "Risk Adjustment": (claims + expenses) * df_rel * assumptions["risk_adjustment_rate"],
            "Coverage Units": coverage_units
        })
        policies = closing
    return pd.DataFrame(rows)
 
 
def run_model(base_assumptions, reassessments, NUM_POLICIES, TERM, ENTRY_AGE,
              MORTALITY, ANNUAL_PREMIUM, SUM_INSURED, ACQUISITION_EXPENSE,
              INTEREST_RATE,experience_distribution, experience_volatility):
    """Runs the full unified GMM projection for one scenario."""
    def _proj(start_year, opening_policies, assumptions):
        return project_remaining(start_year, opening_policies, assumptions, TERM,
                                  ENTRY_AGE, MORTALITY, ANNUAL_PREMIUM, SUM_INSURED,
                                  ACQUISITION_EXPENSE, INTEREST_RATE)
 
    policies = NUM_POLICIES
    current_assumptions = dict(base_assumptions)
    csm_opening = ra_opening = None
    lc_opening = 0.0
    initial_csm_0 = initial_ra_0 = None
    results = []
 
    for year in range(1, TERM + 1):
 
        if year in reassessments:
            old_future = _proj(year, policies, current_assumptions)
            new_assumptions = dict(current_assumptions)
            new_assumptions.update(reassessments[year])
            new_future = _proj(year, policies, new_assumptions)
 
            bel_old = old_future["PV Outflows"].sum() - old_future["PV Premiums"].sum()
            ra_old = old_future["Risk Adjustment"].sum()
            bel_new = new_future["PV Outflows"].sum() - new_future["PV Premiums"].sum()
            ra_new = new_future["Risk Adjustment"].sum()
            delta_fcf = (bel_new + ra_new) - (bel_old + ra_old)
 
            csm_after = max(0, csm_opening - delta_fcf)
            lc_created = max(0, delta_fcf - csm_opening)
 
            csm_opening = csm_after
            ra_opening = ra_new
            lc_opening = lc_opening + lc_created
            current_assumptions = new_assumptions
 
        if year == 1:
            full_future = _proj(1, NUM_POLICIES, base_assumptions)
            bel_0 = full_future["PV Outflows"].sum() - full_future["PV Premiums"].sum()
            ra_0 = full_future["Risk Adjustment"].sum()
            fcf_0 = bel_0 + ra_0
            csm_opening = max(0, -fcf_0)
            ra_opening = ra_0
            lc_opening = max(0, fcf_0)
            initial_csm_0 = csm_opening
            initial_ra_0 = ra_opening
 
        age = ENTRY_AGE + year - 1
        qx = MORTALITY[age] * current_assumptions["mortality_multiplier"]


        age = ENTRY_AGE + year - 1
        qx_expected = MORTALITY[age] * current_assumptions["mortality_multiplier"]
        opening_policies = policies

        shock = draw_shock(experience_distribution, experience_volatility)
        qx_actual = qx_expected * shock
        
        expected_deaths = opening_policies * qx_expected
        actual_deaths = opening_policies * qx_actual


        lapses = opening_policies * current_assumptions["lapse_rate"]
        closing_policies = opening_policies - actual_deaths - lapses
        premiums = opening_policies * ANNUAL_PREMIUM
        claims_actual = actual_deaths * SUM_INSURED
        claims_expected = expected_deaths * SUM_INSURED
        expenses = opening_policies * current_assumptions["annual_expense"]
        coverage_units = opening_policies * SUM_INSURED
 
        remaining_future = _proj(year, opening_policies, current_assumptions)
        remaining_coverage_units = remaining_future["Coverage Units"].sum()
        release_ratio = coverage_units / remaining_coverage_units
 
        csm_interest = csm_opening * INTEREST_RATE
        csm_release = (csm_opening + csm_interest) * release_ratio
        csm_closing = (csm_opening + csm_interest) - csm_release
 
        ra_interest = ra_opening * INTEREST_RATE
        ra_release = (ra_opening + ra_interest) * release_ratio
        ra_closing = (ra_opening + ra_interest) - ra_release
 
        lc_interest = lc_opening * INTEREST_RATE
        lc_release = (lc_opening + lc_interest) * release_ratio
        lc_closing = (lc_opening + lc_interest) - lc_release
 
        acquisition_amort = premiums * ACQUISITION_EXPENSE if year == 1 else 0
        insurance_revenue_claims = claims_expected      # revenue uses EXPECTED
        insurance_expense_claims = claims_actual         # expense uses ACTUAL

        isr = csm_release + ra_release + (insurance_revenue_claims - insurance_expense_claims)
        finance_expense = csm_interest + ra_interest + lc_interest
        total_profit = isr - finance_expense
 
        results.append({
            "Year": year, "Mortality Mult.": current_assumptions["mortality_multiplier"],
            "Lapse Rate": current_assumptions["lapse_rate"],
            "Opening Policies": opening_policies, "Closing Policies": closing_policies,
            "Premiums": premiums, "Claims (Actual)": claims_actual, "Claims (Expected)": claims_expected,
            "Expenses": expenses, "Acquisition CF": acquisition_amort,
            "Closing CSM": csm_closing, "Closing RA": ra_closing, "Closing LC": lc_closing,
            "Insurance Service Result": isr, "Finance Expense": finance_expense,
            "Total Profit": total_profit, "Experience Gain/Loss": insurance_revenue_claims - insurance_expense_claims
        })
 
        policies = closing_policies
        csm_opening, ra_opening, lc_opening = csm_closing, ra_closing, lc_closing
 
    return pd.DataFrame(results), initial_csm_0, initial_ra_0
