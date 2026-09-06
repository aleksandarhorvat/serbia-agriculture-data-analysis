"""
merge_dataset.py
----------------
Merge cleaned STIPS and SORS datasets into one final analysis table.

Inputs:
    data/processed/stips_selling_prices_clean.csv
    data/processed/stips_seed_prices_clean.csv
    data/processed/sors_crop_production_clean.csv

Output:
    data/dataset.csv
    (Year, Crop, Region, Area (ha), Total production (t), Yield (t/ha),
     Selling price (RSD/kg), Seed price (RSD/kg))
"""

import numpy as np
import pandas as pd

from paths import (
    STIPS_SELLING_PRICES_CLEAN,
    STIPS_SEED_PRICES_CLEAN,
    SORS_CROP_PRODUCTION_CLEAN,
    DATASET_PATH,
)

CITY_TO_REGION = {
    "Beograd": "Belgrade Region",
    "Niš": "Southern and Eastern Serbia Region",
    "Leskovac": "Southern and Eastern Serbia Region",
    "Vranje": "Southern and Eastern Serbia Region",
    "Zaječar": "Southern and Eastern Serbia Region",
    "Pirot": "Southern and Eastern Serbia Region",
    "Požarevac": "Southern and Eastern Serbia Region",
    "Smederevo": "Southern and Eastern Serbia Region",
    "Novi Sad": "Vojvodina Region",
    "Subotica": "Vojvodina Region",
    "Sombor": "Vojvodina Region",
    "Zrenjanin": "Vojvodina Region",
    "Kikinda": "Vojvodina Region",
    "Pančevo": "Vojvodina Region",
    "Sremska Mitrovica": "Vojvodina Region",
    "Kragujevac": "Sumadija and Western Serbia Region",
    "Kraljevo": "Sumadija and Western Serbia Region",
    "Čačak": "Sumadija and Western Serbia Region",
    "Užice": "Sumadija and Western Serbia Region",
    "Šabac": "Sumadija and Western Serbia Region",
    "Loznica": "Sumadija and Western Serbia Region",
}

REGION_ORDER = [
    "Belgrade Region",
    "Southern and Eastern Serbia Region",
    "Vojvodina Region",
    "Sumadija and Western Serbia Region",
]

THOUSAND_KERNEL_WEIGHT_GRAMS = 400

CROP_MAP = {
    "corn": "Corn",
    "kukuruz": "Corn",
    "wheat": "Wheat",
    "pšenica": "Wheat",
    "psenica": "Wheat",
    "barley": "Barley",
    "ječam": "Barley",
    "jecam": "Barley",
    "stočni ječam": "Barley",
}


def normalize_crop(text):
    return CROP_MAP.get(str(text).strip().lower())


def load_selling_prices(path):
    """Cleaned STIPS selling prices, one row per observation; caller aggregates to region or city."""
    stips_selling = pd.read_csv(path)
    stips_selling["Year"] = pd.to_datetime(stips_selling["date"], format="%d.%m.%Y").dt.year
    stips_selling["Crop"] = stips_selling["crop"].apply(normalize_crop)
    stips_selling["Region"] = stips_selling["city"].map(CITY_TO_REGION)
    stips_selling = stips_selling.rename(columns={"city": "City"})
    return stips_selling.dropna(subset=["Crop", "Region"])[["Year", "Region", "City", "Crop", "price_rsd"]]


def load_seed_prices(path):
    """Cleaned STIPS seed prices in RSD/kg, one row per observation; caller aggregates."""
    seed_prices = pd.read_csv(path, encoding="utf-8-sig")
    seed_prices.columns = [column.strip() for column in seed_prices.columns]
    seed_prices["Crop"] = seed_prices["Crop"].apply(normalize_crop)
    seed_prices["Region"] = seed_prices["City"].map(CITY_TO_REGION)

    packaging = seed_prices["Packaging"].str.lower().str.replace(" ", "", regex=False)
    number_of_seeds = packaging.str.extract(r"(\d+)sj")[0].astype(float)
    number_of_kilograms = packaging.str.extract(r"(\d+)kg")[0].astype(float)
    is_seed_count_packaging = number_of_seeds.notna()

    seed_prices["seed_price_rsd_per_kg"] = np.where(
        is_seed_count_packaging,
        seed_prices["Seed price (RSD)"] / (number_of_seeds * THOUSAND_KERNEL_WEIGHT_GRAMS / 1_000_000),
        seed_prices["Seed price (RSD)"] / number_of_kilograms,
    )
    # Wheat/barley are sown in autumn -> shift to the following (harvest) year.
    seed_prices["Year"] = np.where(seed_prices["Crop"] == "Corn", seed_prices["Year"], seed_prices["Year"] + 1)
    return seed_prices.dropna(subset=["Crop", "Region"])[["Year", "Region", "City", "Crop", "seed_price_rsd_per_kg"]]


def main():
    # 1) STIPS selling prices -> Year, Region, Crop, Selling price (RSD/kg)
    average_selling_prices = (
        load_selling_prices(STIPS_SELLING_PRICES_CLEAN)
        .groupby(["Year", "Region", "Crop"])["price_rsd"]
        .mean()
        .round(2)
        .reset_index()
        .rename(columns={"price_rsd": "Selling price (RSD/kg)"})
    )

    # 2) STIPS seed prices -> Year, Region, Crop, Seed price (RSD/kg)
    average_seed_prices = (
        load_seed_prices(STIPS_SEED_PRICES_CLEAN)
        .groupby(["Year", "Region", "Crop"])["seed_price_rsd_per_kg"]
        .mean()
        .round(2)
        .reset_index()
        .rename(columns={"seed_price_rsd_per_kg": "Seed price (RSD/kg)"})
    )

    # 3) SORS crop production is already in target format.
    production = pd.read_csv(SORS_CROP_PRODUCTION_CLEAN)

    # 4) Merge into one row per Year/Crop/Region.
    merged = (
        production.merge(average_selling_prices, on=["Year", "Region", "Crop"], how="left")
        .merge(average_seed_prices, on=["Year", "Region", "Crop"], how="left")
    )

    merged["Region"] = pd.Categorical(merged["Region"], categories=REGION_ORDER, ordered=True)
    merged = merged.sort_values(["Year", "Region", "Crop"]).reset_index(drop=True)
    merged["Region"] = merged["Region"].astype(str)
    merged.to_csv(DATASET_PATH, index=False)

    print(f"Rows: {len(merged)}")
    print(f"Columns: {list(merged.columns)}")
    print()
    print(f"Coverage 'Selling price': {merged['Selling price (RSD/kg)'].notna().mean():.0%}")
    print(f"Coverage 'Seed price': {merged['Seed price (RSD/kg)'].notna().mean():.0%}")
    print()
    print(merged.head(15).to_string(index=False))
    print(f"\nSaved: {DATASET_PATH}")


if __name__ == '__main__':
    main()
