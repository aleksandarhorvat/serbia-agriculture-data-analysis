"""
clean_sors_crop_production.py
-----------------------------
Convert raw SORS (RZS) crop production export into a tidy dataset.

Input:  data/raw/Result-130102-300726.csv
Output: data/processed/sors_crop_production_clean.csv
        (Year, Crop, Region, Area (ha), Total production (t), Yield (t/ha))
"""

import pandas as pd

from paths import SORS_RAW_PATH, SORS_CROP_PRODUCTION_CLEAN

METRIC_NAME_MAP = {
    "požnjevena površina, ha / rodna površina, ha": "Area (ha)",
    "ukupan prinos, t": "Total production (t)",
    "prinos, t/ha": "Yield (t/ha)",
}

REGION_NAME_MAP = {
    "Beogradski region": "Belgrade Region",
    "Region Vojvodine": "Vojvodina Region",
    "Region Šumadije i Zapadne Srbije": "Sumadija and Western Serbia Region",
    "Region Južne i Istočne Srbije": "Southern and Eastern Serbia Region",
}

CROP_NAME_MAP = {
    "Pšenica": "Wheat",
    "Ječam": "Barley",
    "Kukuruz": "Corn",
}


def load_raw(path) -> pd.DataFrame:
    data = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    data.columns = [column.strip() for column in data.columns]
    return data


def transform(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()

    data["Year"] = data["God+Mes"].astype(str).str[:4].astype(int)
    data["Region"] = data["nTer"].str.strip().map(REGION_NAME_MAP)
    data["Crop"] = data["nProizvod"].str.strip().map(CROP_NAME_MAP)

    data["Value"] = data["Vrednost"].astype(str).str.replace(",", ".", regex=False)
    data["Value"] = pd.to_numeric(data["Value"], errors="coerce")
    data["Metric"] = data["nVrPod"].str.strip().map(METRIC_NAME_MAP)

    tidy = data.pivot_table(
        index=["Year", "Crop", "Region"],
        columns="Metric",
        values="Value",
        aggfunc="first",
    ).reset_index()

    metric_columns = list(METRIC_NAME_MAP.values())
    tidy = tidy[["Year", "Crop", "Region"] + metric_columns]
    tidy = tidy.sort_values(["Year", "Crop", "Region"]).reset_index(drop=True)
    return tidy


def main():
    raw_data = load_raw(SORS_RAW_PATH)
    result = transform(raw_data)

    print(f"Rows: {len(result)}")
    print(result.head(15).to_string(index=False))

    result.to_csv(SORS_CROP_PRODUCTION_CLEAN, index=False)
    print(f"\nSaved: {SORS_CROP_PRODUCTION_CLEAN}")


if __name__ == "__main__":
    main()
