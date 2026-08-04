"""
clean_stips_selling_prices.py
-----------------------------
Parse raw STIPS selling prices into a normalized table.

Input:  data/raw/stips_selling_prices_raw.csv
Output: data/processed/stips_selling_prices_clean.csv
        (date, crop, packaging, city, price_type, price_rsd)
"""

import re
import unicodedata

import pandas as pd

from paths import STIPS_SELLING_PRICES_RAW, STIPS_SELLING_PRICES_CLEAN

PRODUCT_RE = re.compile(r"^(?P<crop>.+?)\s*(?:\([^)]+\))?\s*p:(?P<packaging>.+)$")

CROP_MAP = {
    "kukuruz": "Corn",
    "psenica": "Wheat",
    "jecam": "Barley",
    "stocni jecam": "Barley",
}

PRICE_TYPE_MAP = {
    "gazdinstvo": "farm_gate",
    "maloprodaja": "retail",
    "pijaca": "market",
    "silos": "silo",
}

PACKAGING_MAP = {
    "džak 50kg": "bag 50kg",
    "rinfuz": "bulk",
}


def _normalize_ascii(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    return "".join(ch for ch in text if not unicodedata.combining(ch)).lower().strip()


def parse_product(text: str) -> pd.Series:
    match = PRODUCT_RE.match(str(text).strip())
    if not match:
        return pd.Series([None, None])
    return pd.Series([match.group("crop").strip(), match.group("packaging").strip()])


def normalize_crop(raw_crop: str):
    key = _normalize_ascii(raw_crop)
    return CROP_MAP.get(key)


def main():
    data = pd.read_csv(STIPS_SELLING_PRICES_RAW)

    data[["raw_crop", "packaging"]] = data["proizvod"].apply(parse_product)
    data["crop"] = data["raw_crop"].apply(normalize_crop)

    unparsable_rows = data[data["raw_crop"].isna()]
    if len(unparsable_rows):
        print(f"WARNING: {len(unparsable_rows)} rows could not be parsed.")
        print(unparsable_rows["proizvod"].unique())

    unknown_crop_rows = data[data["crop"].isna()]
    if len(unknown_crop_rows):
        print(f"WARNING: {len(unknown_crop_rows)} rows have unknown crop values.")
        print(sorted(unknown_crop_rows["raw_crop"].dropna().unique()))

    place_split = data["mesto_id"].astype(str).str.rsplit("-", n=1)
    data["city"] = place_split.str[0]
    data["price_type"] = place_split.str[1].replace(PRICE_TYPE_MAP)
    data["packaging"] = data["packaging"].replace(PACKAGING_MAP)

    result = data[["datum", "crop", "packaging", "city", "price_type", "cena"]].rename(
        columns={"datum": "date", "cena": "price_rsd"}
    )

    print(f"Rows: {len(result)}")
    print(f"Unique crops: {sorted(result['crop'].dropna().unique())}")
    print(f"Unique packaging: {sorted(result['packaging'].dropna().unique())}")
    print(f"Unique price_type: {sorted(result['price_type'].dropna().unique())}")

    result.to_csv(STIPS_SELLING_PRICES_CLEAN, index=False)
    print(f"\nSaved: {STIPS_SELLING_PRICES_CLEAN}")


if __name__ == "__main__":
    main()
