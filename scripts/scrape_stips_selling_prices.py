"""
scrape_stips_selling_prices.py
------------------------------
Download weekly STIPS selling prices for wheat, barley and corn across cities
from 2010 to today.

Manual one-time step: intentionally not part of run_pipeline.py because it is
network-bound and can take time.

Output: data/raw/stips_selling_prices_raw.csv
        (kept in original Serbian field names)
"""

import csv
import time
from datetime import datetime

import requests

from paths import STIPS_SELLING_PRICES_RAW

BASE_URL = "https://www.stips.minpolj.gov.rs/stips/ajax/cene"
START_DATE = "01.01.2010"
END_DATE = datetime.now().strftime("%d.%m.%Y")
CATEGORY_ID = 4

# All place IDs are queried in groups of 4 to match API behavior.
PLACE_IDS = [
    78,
    79,
    80,
    76,
    83,
    82,
    81,
    71,
    114,
    113,
    112,
    61,
    86,
    85,
    84,
    69,
    90,
    89,
    87,
    72,
    163,
    166,
    168,
    169,
    93,
    92,
    91,
    66,
    96,
    95,
    94,
    73,
    117,
    116,
    115,
    64,
    121,
    120,
    118,
    62,
    99,
    98,
    97,
    74,
    102,
    101,
    100,
    68,
    172,
    175,
    177,
    178,
    105,
    104,
    103,
    67,
    124,
    123,
    122,
    63,
    127,
    126,
    125,
    65,
    130,
    129,
    128,
    59,
    154,
    157,
    159,
    160,
    108,
    107,
    106,
    75,
    111,
    110,
    109,
    70,
    133,
    132,
    131,
    60,
]

# Product groups (wheat/barley/corn variants).
PRODUCT_ID_GROUPS = [
    [339, 352, 353, 370, 354, 340],
    [350, 351, 369],
    [348, 349],
]


def fetch(place_group, product_group):
    params = [
        ("kategorija", CATEGORY_ID),
        ("datum_od", START_DATE),
        ("datum_do", END_DATE),
    ]
    for product_id in product_group:
        params.append(("proizvodi", product_id))
    for place_id in place_group:
        params.append(("mesta", place_id))

    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def main():
    place_groups = [PLACE_IDS[idx : idx + 4] for idx in range(0, len(PLACE_IDS), 4)]
    total_requests = len(place_groups) * len(PRODUCT_ID_GROUPS)
    done = 0

    with open(STIPS_SELLING_PRICES_RAW, "w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["proizvod", "poreklo", "datum", "mesto_id", "cena"])

        for place_group in place_groups:
            for product_group in PRODUCT_ID_GROUPS:
                done += 1
                print(f"[{done}/{total_requests}] places={place_group}  products={product_group}")
                try:
                    payload = fetch(place_group, product_group)
                    place_name_map = {}
                    col_model = payload.get("conf", {}).get("colModel", [])
                    col_names = payload.get("conf", {}).get("colNames", [])
                    first = payload.get("mesta_col_first", 0)
                    last = payload.get("mesta_col_last", len(col_model) - 1)

                    for idx in range(first, last + 1):
                        if idx < len(col_model) and idx < len(col_names):
                            key = col_model[idx].get("name", "")
                            if key.startswith("mesto_"):
                                place_id = int(key.split("_", 1)[1])
                                place_name_map[place_id] = col_names[idx]

                    for row in payload.get("data", []):
                        product = row.get("proizvod", "")
                        origin = row.get("poreklo", "")
                        date = row.get("datum", "")
                        for place_id in place_group:
                            price = row.get(f"mesto_{place_id}")
                            if price is not None:
                                place_name = place_name_map.get(place_id, str(place_id))
                                writer.writerow([product, origin, date, place_name, price])
                except requests.RequestException as exc:
                    print(f"  Request error: {exc}")
                except Exception as exc:
                    print(f"  Unexpected error: {exc}")
                time.sleep(0.3)

    print(f"\nDone. Results saved to {STIPS_SELLING_PRICES_RAW}")


if __name__ == "__main__":
    main()
