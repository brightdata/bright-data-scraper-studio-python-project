# Scraper Studio - Bright Data API
# Simple Python boilerplate
# Install:   pip install -r requirements.txt
# Configure: cp .env.example .env  (then edit values)
# Run:       python index.py

import json
import os
import time
from datetime import datetime

import requests
from colorama import Fore, Style, init
from dotenv import load_dotenv

load_dotenv()
init(autoreset=True)

# ========================================
# CONFIGURATION
# Set via .env (recommended) or override the fallbacks here.
# ========================================
API_TOKEN    = os.environ.get('BRIGHT_DATA_API_TOKEN')    or 'BRIGHT_DATA_API_KEY'
COLLECTOR_ID = os.environ.get('BRIGHT_DATA_COLLECTOR_ID') or 'YOUR_COLLECTOR_ID'

API_BASE          = 'https://api.brightdata.com'
POLL_INTERVAL_S   = 5
MAX_POLL_ATTEMPTS = 60  # ~5 minutes total
MAX_RETRIES       = 3   # for transient HTTP failures

# ========================================
# SAMPLE INPUT
# Each item must match the input schema defined in your collector.
# The default assumes a single `url` field.
# ========================================
SAMPLE_URLS = [
    {"url": "https://ecommerce-shop-brd.vercel.app/product/echo-portable-speaker"},
    {"url": "https://ecommerce-shop-brd.vercel.app/product/nimbus-cloud-storage"},
    {"url": "https://ecommerce-shop-brd.vercel.app/product/pulse-fitness-tracker"},
]


# ========================================
# CORE: HTTP request + retry/backoff
# Retries transient errors (5xx, network) with exponential backoff (1s, 2s, 4s).
# 4xx errors fail fast - they signal a client mistake, not a transient issue.
# ========================================
def api_request(method, path, body=None):
    url = f"{API_BASE}{path}"
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.request(method, url, headers=headers, json=body, timeout=60)
            if 400 <= response.status_code < 500:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
            if response.status_code >= 500:
                last_err = RuntimeError(f"HTTP {response.status_code}: {response.text}")
            else:
                return response.text
        except (requests.RequestException, RuntimeError) as err:
            if isinstance(err, RuntimeError) and str(err).startswith("HTTP 4"):
                raise
            last_err = err
        if attempt < MAX_RETRIES - 1:
            backoff = 2 ** attempt
            print(f"{Fore.YELLOW}Retrying in {backoff}s...")
            time.sleep(backoff)
    raise last_err


# ========================================
# SCRAPER FLOW
# 1. POST /dca/trigger         -> { collection_id }
# 2. GET  /dca/dataset?id=<id> -> poll until results are returned
# ========================================
def run_scraper(inputs):
    print(f"{Fore.CYAN}{Style.BRIGHT}Starting Scraper Studio collector...")
    print(f"{Fore.BLUE}Queueing {len(inputs)} input(s)")

    trigger_path = f"/dca/trigger?collector={COLLECTOR_ID}&queue_next=1"
    trigger_response = api_request('POST', trigger_path, inputs)
    snapshot_id = json.loads(trigger_response).get('collection_id')
    if not snapshot_id:
        raise RuntimeError(f"Trigger returned no collection_id: {trigger_response}")
    print(f"{Fore.GREEN}Job queued. Snapshot ID: {snapshot_id}")

    print(f"{Fore.YELLOW}Polling for results...")
    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        time.sleep(POLL_INTERVAL_S)
        dataset_response = api_request('GET', f"/dca/dataset?id={snapshot_id}")
        if _is_ready(dataset_response):
            print(f"{Fore.GREEN}{Style.BRIGHT}Results downloaded.")
            return dataset_response
        print(f"{Fore.LIGHTBLACK_EX}Attempt {attempt}/{MAX_POLL_ATTEMPTS} - building")

    raise TimeoutError("Timed out waiting for collector to finish")


def _is_ready(body):
    """A finished snapshot is a non-empty JSON array; while building, the API returns a status object."""
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return False
    return isinstance(parsed, list) and len(parsed) > 0


# ========================================
# LIBRARY HELPERS
# ========================================
def trigger_with_url(url):
    return run_scraper([{"url": url}])


def trigger_with_urls(urls):
    return run_scraper([{"url": u} for u in urls])


def save_results(data, filename=None):
    if filename is None:
        ts = datetime.now().isoformat().replace(':', '-').replace('.', '-')
        filename = f"scraper_studio_results_{ts}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(data)
    print(f"{Fore.GREEN}Saved to {Style.BRIGHT}{filename}")


# ========================================
# MAIN
# ========================================
def main():
    print(f"{Fore.MAGENTA}{Style.BRIGHT}Bright Data Scraper Studio")
    print(f"{Fore.MAGENTA}==============================")

    if API_TOKEN == 'BRIGHT_DATA_API_KEY' or COLLECTOR_ID == 'YOUR_COLLECTOR_ID':
        print(f"{Fore.RED}{Style.BRIGHT}Missing config. Set BRIGHT_DATA_API_TOKEN and BRIGHT_DATA_COLLECTOR_ID:")
        print(f"{Fore.YELLOW}  - via .env file:  cp .env.example .env  then edit")
        print(f"{Fore.YELLOW}  - or via shell:   export BRIGHT_DATA_API_TOKEN=...")
        return

    try:
        data = run_scraper(SAMPLE_URLS)
        save_results(data)
        print(f"{Fore.GREEN}{Style.BRIGHT}\nDone.")
    except Exception as err:
        print(f"{Fore.RED}{Style.BRIGHT}Failed: {Fore.RED}{err}")
        raise SystemExit(1)


if __name__ == '__main__':
    main()
