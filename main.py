import pandas as pd
from mortality import load_mortality_table
from model import run_model
from assumptions import (
    NUM_POLICIES, TERM, ENTRY_AGE, SEX, LAPSE_RATE, ANNUAL_PREMIUM,
    SUM_INSURED, ANNUAL_EXPENSE, ACQUISITION_EXPENSE, INTEREST_RATE,
    RISK_ADJUSTMENT_RATE, EXPERIENCE_DISTRIBUTION, EXPERIENCE_VOLATILITY
)

MORTALITY = load_mortality_table(SEX, filepath="data/mortality_table.csv")

if __name__ == "__main__":
    BASE_ASSUMPTIONS = {
        "mortality_multiplier": 1.0, "lapse_rate": LAPSE_RATE,
        "annual_expense": ANNUAL_EXPENSE, "risk_adjustment_rate": RISK_ADJUSTMENT_RATE
    }

    REASSESSMENTS = {5: {"mortality_multiplier": 1.3}, 8: {"lapse_rate": 0.09}} # MANUALLY CHANGING ASSUMPTIONS

    df_out, day1_csm, day1_ra = run_model(
        BASE_ASSUMPTIONS, REASSESSMENTS, NUM_POLICIES, TERM, ENTRY_AGE,
        MORTALITY, ANNUAL_PREMIUM, SUM_INSURED, ACQUISITION_EXPENSE, INTEREST_RATE,
        EXPERIENCE_DISTRIBUTION,EXPERIENCE_VOLATILITY
    )
    print(df_out)
    print("\nDay-1 CSM:", round(day1_csm), "| Day-1 RA:", round(day1_ra))
    print("Sum of Total Profit:", round(df_out["Total Profit"].sum()))
    print(df_out.iloc[-1].to_string())