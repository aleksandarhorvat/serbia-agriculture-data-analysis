"""Run all cleaning and merge steps to produce data/dataset.csv.

This script does NOT run scraping scripts because scraping is network-bound and
intentionally manual. It expects the raw files to already exist:

    data/raw/stips_selling_prices_raw.csv      (from scrape_stips_selling_prices.py)
    data/raw/downloaded_xls/*.xls             (from scrape_stips_seed_prices.py)
    data/raw/Result-130102-300726.csv         (manual SORS export)
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

STEPS = [
    "clean_stips_seed_prices.py",
    "clean_stips_selling_prices.py",
    "clean_sors_crop_production.py",
    "merge_dataset.py",
]


def run_step(script_name):
    script_path = SCRIPTS_DIR / script_name
    print(f"\n{'='*60}\n>>> {script_name}\n{'='*60}")
    result = subprocess.run([sys.executable, str(script_path)], cwd=SCRIPTS_DIR)
    if result.returncode != 0:
        print(f"\nERROR: {script_name} failed, stopping pipeline.")
        sys.exit(1)


def main():
    for step in STEPS:
        run_step(step)
    print("\nPipeline finished. dataset.csv is ready.")


if __name__ == "__main__":
    main()
