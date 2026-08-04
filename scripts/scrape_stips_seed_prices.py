"""
scrape_stips_seed_prices.py
---------------------------
Download seed-price XLS files from the STIPS archive page.

Manual one-time step: intentionally not part of run_pipeline.py.

Output: data/raw/downloaded_xls/semenski_<month>_<year>.xls
"""

import os
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from paths import DOWNLOADED_XLS_DIR

BASE_URL = "https://www.stips.minpolj.gov.rs"
INDEX_URL = "https://www.stips.minpolj.gov.rs/srl/strana/inputi"
ICON_SRCS = {"/sites/default/files/sm.jpg"}
DELAY_SECONDS = 1.0
MONTH_MAP = {
    "APR": "april",
    "OKT": "oktobar",
}

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (compatible; research-scraper/1.0)"})


def get_html(url, retries=3):
    for attempt in range(retries):
        try:
            response = SESSION.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            print(f"  [warn] attempt {attempt + 1} failed for {url}: {exc}")
            if attempt < retries - 1:
                time.sleep(3)
    return None


def collect_node_links(html):
    """Return unique (absolute_node_url, year, month) tuples for seed entries."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    headers = [cell.get_text(" ", strip=True).upper() for cell in table.find("thead").find_all("th")]
    month_headers = []
    for raw_header in headers[1:]:
        if not raw_header:
            continue
        month_headers.append(MONTH_MAP.get(raw_header, raw_header.lower()))

    links = []
    seen = set()
    for row in table.find("tbody").find_all("tr"):
        cells = row.find_all(["th", "td"])
        if not cells:
            continue

        year_text = cells[0].get_text(" ", strip=True)
        year_match = re.match(r"^(19\d{2}|20\d{2})$", year_text)
        if not year_match:
            continue

        year = year_match.group(1)
        for idx, cell in enumerate(cells[1:]):
            if idx >= len(month_headers):
                break
            month = month_headers[idx]
            for image in cell.find_all("img"):
                src = image.get("src", "")
                if src not in ICON_SRCS:
                    continue
                anchor = image.find_parent("a")
                if anchor and anchor.get("href"):
                    href = anchor["href"].strip()
                    absolute_url = urljoin(BASE_URL, href)
                    if absolute_url not in seen:
                        seen.add(absolute_url)
                        links.append((absolute_url, year, month))
    return links


def extract_xls_link(html):
    """Return absolute XLS/XLSX URL from a node page, or None."""
    soup = BeautifulSoup(html, "html.parser")
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if re.search(r"\.xlsx?$", href, re.IGNORECASE):
            return urljoin(BASE_URL, href)

    file_div = soup.find(class_=re.compile(r"field-name-upload|field--name-upload"))
    if file_div:
        for anchor in file_div.find_all("a", href=True):
            return urljoin(BASE_URL, anchor["href"].strip())
    return None


def download_file(url, destination_dir, year="", month=""):
    """Download a file and save it under destination_dir. Returns filename."""
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    if not filename:
        filename = "file_" + str(int(time.time()))

    destination_path = os.path.join(destination_dir, filename)
    if os.path.exists(destination_path):
        stem, extension = os.path.splitext(filename)
        filename = f"{stem}_{year}{extension}"
        destination_path = os.path.join(destination_dir, filename)
    if os.path.exists(destination_path):
        print(f"  [skip] already exists: {filename}")
        return filename

    try:
        response = SESSION.get(url, timeout=60, stream=True)
        response.raise_for_status()
        with open(destination_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=65536):
                file.write(chunk)
        print(f"  [ok]   {filename}")
        return filename
    except requests.RequestException as exc:
        print(f"  [err]  failed to download {url}: {exc}")
        return None


def rename_to_canonical(downloaded_name, destination_dir, year="", month=""):
    """Rename to semenski_month_year.ext when needed."""
    if not downloaded_name:
        return None

    safe_year = str(year or "unknown")
    safe_month = (month or "unknown").lower()
    _, extension = os.path.splitext(downloaded_name)
    if extension.lower() not in {".xls", ".xlsx"}:
        extension = ".xls"

    canonical_name = f"semenski_{safe_month}_{safe_year}{extension}"
    counter = 1
    target_name = canonical_name
    while os.path.exists(os.path.join(destination_dir, target_name)):
        target_name = f"semenski_{safe_month}_{safe_year}_{counter}{extension}"
        counter += 1

    source_path = os.path.join(destination_dir, downloaded_name)
    target_path = os.path.join(destination_dir, target_name)
    if os.path.exists(source_path) and source_path != target_path:
        os.replace(source_path, target_path)
        print(f"  [renamed] {downloaded_name} -> {target_name}")
        return target_name
    return downloaded_name


def main():
    print(f"[1] Fetching index page: {INDEX_URL}")
    index_html = get_html(INDEX_URL)
    if not index_html:
        print("ERROR: could not fetch index page.")
        return

    node_links = collect_node_links(index_html)
    print(f"[2] Found {len(node_links)} seed node links.\n")

    xls_urls = {}
    failed_nodes = []

    for idx, (node_url, year, month) in enumerate(node_links, 1):
        print(f"[{idx}/{len(node_links)}] {year}  {month}  {node_url}")
        time.sleep(DELAY_SECONDS)
        node_html = get_html(node_url)
        if not node_html:
            print("  [err]  could not fetch node page")
            failed_nodes.append(node_url)
            continue

        xls_url = extract_xls_link(node_html)
        if xls_url:
            xls_urls[node_url] = (xls_url, year, month)
            print(f"  [xls]  {xls_url}")
        else:
            print("  [warn] no XLS link found on this page")
            failed_nodes.append(node_url)

    print(f"\n[3] Downloading {len(xls_urls)} XLS files to '{DOWNLOADED_XLS_DIR}/'...\n")
    for _, (xls_url, year, month) in xls_urls.items():
        time.sleep(DELAY_SECONDS)
        downloaded_name = download_file(xls_url, DOWNLOADED_XLS_DIR, year, month)
        if downloaded_name:
            rename_to_canonical(downloaded_name, DOWNLOADED_XLS_DIR, year, month)

    print(f"\nDone. {len(xls_urls)} files processed.")
    if failed_nodes:
        print(f"\nNodes where no XLS was found ({len(failed_nodes)}):")
        for url in failed_nodes:
            print(f"  {url}")


if __name__ == "__main__":
    main()
