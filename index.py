# Scraper Studio - Bright Data API
# Simple Python boilerplate
# Install: pip install -r requirements.txt
# Run:     python index.py

import json
import time
from datetime import datetime

import requests
from colorama import Fore, Style, init

init(autoreset=True)

# ========================================
# CONFIGURATION
# ========================================
API_TOKEN    = 'BRIGHT_DATA_API_KEY'   # Account Settings -> API Key
COLLECTOR_ID = 'YOUR_COLLECTOR_ID'     # From your Scraper Studio collector (c_xxxx)

API_BASE = 'https://api.brightdata.com'

# ========================================
# SAMPLE INPUT
# Each item must match the input schema defined in your collector.
# The default schema is a single field: `url`.
# ========================================
SAMPLE_URLS = [
    {"url": "https://ecommerce-shop-brd.vercel.app/product/echo-portable-speaker"},
    {"url": "https://ecommerce-shop-brd.vercel.app/product/nimbus-cloud-storage"},
    {"url": "https://ecommerce-shop-brd.vercel.app/product/pulse-fitness-tracker"},
]


# ========================================
# CORE: thin wrapper around requests
# ========================================
def api_request(method, path, body=None):
    """Send a request to the Bright Data API and return the raw response text."""
    url = f"{API_BASE}{path}"
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    response = requests.request(method, url, headers=headers, json=body, timeout=60)
    if response.status_code >= 400:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
    return response.text


# ========================================
# SCRAPER FLOW
# 1. POST /dca/trigger          -> { collection_id }
# 2. GET  /dca/dataset?id=<id>  -> poll until results are returned
# ========================================
def run_scraper(inputs):
    print(f"{Fore.CYAN}{Style.BRIGHT}Starting Scraper Studio collector...")
    print(f"{Fore.BLUE}Queueing {len(inputs)} input(s)")
    print(f"{Fore.LIGHTBLACK_EX}Request body:")
    print(f"{Fore.LIGHTBLACK_EX}{json.dumps(inputs, indent=2)}")

    # 1. Trigger
    trigger_path = f"/dca/trigger?collector={COLLECTOR_ID}&queue_next=1"
    trigger_response = api_request('POST', trigger_path, inputs)
    snapshot_id = json.loads(trigger_response).get('collection_id')
    if not snapshot_id:
        raise RuntimeError(f"Trigger returned no collection_id: {trigger_response}")
    print(f"{Fore.GREEN}Job queued. Snapshot ID: {snapshot_id}")

    # 2. Poll for results
    print(f"{Fore.YELLOW}Polling for results...")
    max_attempts = 60  # up to ~5 minutes at 5s intervals
    for attempt in range(1, max_attempts + 1):
        time.sleep(5)
        dataset_response = api_request('GET', f"/dca/dataset?id={snapshot_id}")
        ready = _is_ready(dataset_response)
        print(f"{Fore.LIGHTBLACK_EX}Attempt {attempt}/{max_attempts} - {'ready' if ready else 'building'}")
        if ready:
            print(f"{Fore.GREEN}{Style.BRIGHT}Results downloaded.")
            return dataset_response

    raise TimeoutError("Timed out waiting for collector to finish")


def _is_ready(body):
    """A finished snapshot is a non-empty JSON array; while building, the API returns a status object."""
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return False
    return isinstance(parsed, list) and len(parsed) > 0


# ========================================
# OUTPUT
# ========================================
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
        print(f"{Fore.RED}{Style.BRIGHT}Set API_TOKEN and COLLECTOR_ID in index.py before running.")
        print(f"{Fore.YELLOW}API token: https://brightdata.com/cp/setting")
        print(f"{Fore.YELLOW}Collector ID: open your collector in Scraper Studio - the ID starts with c_")
        return

    try:
        results = run_scraper(SAMPLE_URLS)
        save_results(results)
        print(f"{Fore.GREEN}{Style.BRIGHT}\nDone.")
    except Exception as err:
        print(f"{Fore.RED}{Style.BRIGHT}Failed: {Fore.RED}{err}")
        raise SystemExit(1)


if __name__ == '__main__':
    main()
