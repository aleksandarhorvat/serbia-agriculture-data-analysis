"""Shared filesystem paths for the full data pipeline."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # agriculture_data_analysis/

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DOWNLOADED_XLS_DIR = RAW_DIR / "downloaded_xls"
SORS_RAW_PATH = RAW_DIR / "Result-130102-300726.csv"

STIPS_SELLING_PRICES_RAW = RAW_DIR / "stips_selling_prices_raw.csv"
STIPS_SELLING_PRICES_CLEAN = PROCESSED_DIR / "stips_selling_prices_clean.csv"
STIPS_SEED_PRICES_CLEAN = PROCESSED_DIR / "stips_seed_prices_clean.csv"
SORS_CROP_PRODUCTION_CLEAN = PROCESSED_DIR / "sors_crop_production_clean.csv"

DATASET_PATH = BASE_DIR / "data" / "dataset.csv"

# Ensure folders exist before writing files.
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADED_XLS_DIR.mkdir(parents=True, exist_ok=True)
