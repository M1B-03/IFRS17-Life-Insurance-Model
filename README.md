# IFRS17-Life-Insurance-Model

Built as a personal/educational tool to learn and demonstrate IFRS 17 mechanics, this project is a Python implementation of an IFRS 17 General Measurement Model (GMM) for a hypothetical life insurance portfolio, which demonstrates the core mechanics of fulfilment cash flow valuation, CSM/Risk Adjustment roll-forwards, onerous contract recognition and assumption re-measurement. This project also models experience variance (actual vs expected comparison), where the 'actual' data is simulated using a Gamma/Lognormal shock around the priced mortality rate.

## What this model does
* Projects policy movements (deaths, lapses) and cash flows (premiums, claims, expenses) for a cohort of life insurance policies.

* Calculates the fulfilment cash flows: Best Estimate Liability (BEL) + Risk Adjustment (RA).
Establishes and rolls forward the Contractual Service Margin (CSM) and Risk Adjustment using a coverage-unit release pattern, with interest accumulation at the locked-in rate.

* Derives the Insurance Service Result (ISR) and Insurance Finance Expense, and verifies the identity ISR = CSM release + RA release (absent experience variance) as a built-in consistency check.

* Supports mid-contract re-measurement of non-financial assumptions (mortality, lapse, expenses), correctly distinguishing changes that adjust the CSM from changes severe enough to create an onerous Loss Component.

* Models genuine year-to-year experience variance: actual mortality each year is drawn from a Gamma or Lognormal distribution around the priced (expected) rate, and the resulting gain/loss flows directly into profit for that period, with no effect on CSM -- distinct from the assumption re-measurement mechanism above, which only affects future expected cash flows.

## Data Sources

Mortality rates are sourced from the Australian Life Tables 2020-22, published by the Australian Government Actuary (December 2024): [https://aga.gov.au/publications/life-tables/australian-life-tables-2020-22](https://aga.gov.au/publications/life-tables/australian-life-tables-2020-22)

All other assumptions (policy count, premium, sum insured, lapse rate, expense loadings, discount rate, risk adjustment rate, experience volatility) are illustrative, set in ```assumptions.py```

## Current limitations/future improvements

* Single cohort, single portfolio, no IFRS 17 grouping (onerous / no-significant-possibility / other-profitable buckets, or annual cohorts) — the whole book is currently valued as one group.

* No reinsurance.

* Only mortality is stochastic; lapse and expense experience are currently deterministic.

* Locked-in discount rate only — no current-rate/OCI disaggregation for Insurance Finance Income or Expense.

* Single simulation path per run, not a full Monte Carlo distribution of outcomes.

## How to run

```bash
pip install -r requirements.txt
python main.py      # on Windows
python3 main.py      # on macOS/Linux
```
