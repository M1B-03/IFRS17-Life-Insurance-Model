"""
Mortality Data
Source: Australian Life Tables 2020-22, Australian Government Actuary,
released December 2024.
https://aga.gov.au/publications/life-tables/australian-life-tables-2020-22
"""
import csv


def load_mortality_table(sex: str, filepath: str = "data/mortality_table.csv") -> dict:
    """
    Loads the qx (mortality rate) table for the given sex from the CSV file.

    sex: "male" or "female"
    Returns: dict mapping {age: qx}
    """
    if sex not in ("male", "female"):
        raise ValueError(f"sex must be 'male' or 'female', got {sex!r}")

    column = f"qx_{sex}"
    table = {}
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            table[int(row["age"])] = float(row[column])
    return table


if __name__ == "__main__":
    # Quick sanity check when run directly
    male_table = load_mortality_table("male", "data/mortality_table.csv")
    female_table = load_mortality_table("female", "data/mortality_table.csv")
    print(f"Loaded {len(male_table)} male ages, {len(female_table)} female ages")
    print("Male age 45:", male_table[45])
    print("Female age 45:", female_table[45])