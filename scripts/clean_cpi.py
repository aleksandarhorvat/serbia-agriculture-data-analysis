"""
clean_cpi.py
------------
Clean the SORS consumer price index (CPI) export into a tidy monthly series.

Input:
    data/raw/cpi_raw.xls
    (SORS "Индекси потрошачких цена", COICOP "Укупно", base index 2006=100,
     Republic of Serbia. The .xls is actually an HTML pivot table, as exported
     by data.stat.gov.rs.)

Output:
    data/processed/cpi_clean.csv
    (Year, Month, CPI index (2006=100))
"""

import re

import pandas as pd

from paths import CPI_RAW, CPI_CLEAN

# SORS exports month names in Serbian Cyrillic.
MONTH_MAP = {
    "јануар": 1, "фебруар": 2, "март": 3, "април": 4,
    "мај": 5, "јун": 6, "јул": 7, "август": 8,
    "септембар": 9, "октобар": 10, "новембар": 11, "децембар": 12,
}


def main():
    html = CPI_RAW.read_text(encoding="utf-8")

    # Each data row is a period label (YYYY/<serbian month>) followed by a
    # cell carrying the numeric index in its data-value attribute.
    rows = re.findall(
        r'pvtRowLabel[^>]*>\s*(\d{4})/([^\s<]+)\s*</th>.*?data-value="([-\d.,]+)"',
        html,
    )

    cpi = pd.DataFrame(rows, columns=["Year", "MonthName", "CPI index (2006=100)"])
    cpi["Year"] = cpi["Year"].astype(int)
    cpi["Month"] = cpi["MonthName"].map(MONTH_MAP)
    cpi["CPI index (2006=100)"] = cpi["CPI index (2006=100)"].str.replace(",", ".", regex=False).astype(float)

    unmapped = cpi[cpi["Month"].isna()]["MonthName"].unique()
    if len(unmapped):
        raise ValueError(f"Unrecognized month name(s): {list(unmapped)}")

    cpi = (
        cpi[["Year", "Month", "CPI index (2006=100)"]]
        .sort_values(["Year", "Month"])
        .reset_index(drop=True)
    )

    CPI_CLEAN.parent.mkdir(parents=True, exist_ok=True)
    cpi.to_csv(CPI_CLEAN, index=False)

    print(f"Rows: {len(cpi)}")
    print(f"Year range: {cpi['Year'].min()}-{cpi['Year'].max()}")
    print(cpi.head(6).to_string(index=False))
    print(f"\nSaved: {CPI_CLEAN}")


if __name__ == "__main__":
    main()
