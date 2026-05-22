# Bright Data Scraper Studio (Python)

[![Bright Data Promo](https://github.com/luminati-io/LinkedIn-Scraper/raw/main/Proxies%20and%20scrapers%20GitHub%20bonus%20banner.png)](https://brightdata.com/)

<a href="https://githubbox.com/brightdata/bright-data-scraper-studio-python-project?file=index.py" target="_blank">Open in CodeSandbox</a>, sign in with GitHub, then fork the repository to begin making changes.

This project provides a minimal Python boilerplate for running a [Bright Data Scraper Studio](https://brightdata.com/products/web-scraper/scraper-studio) collector via the Data Collection API (DCA): trigger a job with a list of URLs and download the results.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Examples](#examples)
- [Output](#output)
- [Support](#support)
- [License](#license)

---

## Overview

[Scraper Studio](https://brightdata.com/products/web-scraper/scraper-studio) is a low-code IDE for building your own web scraping collectors on the Bright Data platform. Once a collector is published it exposes two simple HTTP endpoints:

| Step | Endpoint | Purpose |
| --- | --- | --- |
| 1 | `POST /dca/trigger?collector=<id>` | Queue one or more inputs for the collector |
| 2 | `GET  /dca/dataset?id=<snapshot_id>` | Download the collected data when ready |

This repository wraps those two calls in roughly 150 lines of Python so you can copy, paste, and ship.

---

## Features

- Trigger a Scraper Studio collector via the `/dca/trigger` endpoint
- Poll `/dca/dataset` until results are ready
- **Env-var config** via `.env` (no secrets in code)
- **Retry with exponential backoff** for transient errors (5xx, network); fails fast on 4xx
- Library helpers: `trigger_with_url`, `trigger_with_urls`, `run_scraper`
- Save the raw JSON response to a timestamped file

---

## Prerequisites

- Python 3.8 or higher
- A Bright Data account with an [API token](https://brightdata.com/cp/setting)
- A published collector in [Scraper Studio](https://brightdata.com/cp/scrapers) - copy its **Collector ID** (starts with `c_`)

---

## Installation

```bash
git clone https://github.com/brightdata/bright-data-scraper-studio-python-project.git
cd bright-data-scraper-studio-python-project
pip install -r requirements.txt
cp .env.example .env       # then edit .env with your token and collector ID
```

### Dependencies

- `requests` - HTTP client for the Bright Data API
- `colorama` - colored terminal output
- `python-dotenv` - load `.env` files into `os.environ`

---

## Usage

```bash
python index.py
```

Results are written to a `scraper_studio_results_<timestamp>.json` file in the project directory.

---

## Configuration

Two environment variables are required - set them in `.env`, in your shell, or hardcode them in [`index.py`](index.py):

| Variable | Where to find it |
| --- | --- |
| `BRIGHT_DATA_API_TOKEN`    | Bright Data dashboard - Account Settings - [API Tokens](https://brightdata.com/cp/setting) |
| `BRIGHT_DATA_COLLECTOR_ID` | Scraper Studio - open your collector - the ID in the URL (starts with `c_`) |

You can also tune the polling and retry behavior at the top of `index.py`:

```python
POLL_INTERVAL_S   = 5    # delay between dataset checks (seconds)
MAX_POLL_ATTEMPTS = 60   # give up after ~5 minutes
MAX_RETRIES       = 3    # for transient HTTP failures
```

The shape of `SAMPLE_URLS` must match the **input schema** you defined in Scraper Studio. The default sample assumes a single `url` field - if your collector uses different inputs (for example, `keyword`, `zip_code`, `category`), update the dictionaries accordingly.

---

## How It Works

```text
       +-----------------+      POST /dca/trigger      +-------------------+
       |  Your script    | --------------------------> |  Scraper Studio   |
       |  (index.py)     | <-- { collection_id } ----- |  Collector        |
       +-----------------+                             +-------------------+
                |                                                |
                |  GET /dca/dataset?id=<snapshot_id>             |
                |  (poll every 5s, retry 5xx with backoff)       |
                |  <--- [ { ...record... }, ... ] -------------- |
                v
       scraper_studio_results_<timestamp>.json
```

The script polls `/dca/dataset` every 5 seconds for up to 5 minutes. A non-empty JSON array is treated as a finished snapshot. Transient errors (5xx, network) are retried with exponential backoff (1s, 2s, 4s); 4xx errors fail immediately so you fix the request rather than retry it.

---

## Examples

### Run with your own URLs

Replace `SAMPLE_URLS` in [`index.py`](index.py):

```python
SAMPLE_URLS = [
    {"url": "https://example.com/product/1"},
    {"url": "https://example.com/product/2"},
]
```

### Custom input schema

If your collector expects something other than `url`, pass whatever fields it defines:

```python
inputs = [
    {"keyword": "wireless headphones", "country": "US"},
    {"keyword": "standing desk",       "country": "DE"},
]
run_scraper(inputs)
```

### Use as a library

`run_scraper`, `trigger_with_url`, `trigger_with_urls`, and `save_results` are top-level functions:

```python
from index import trigger_with_urls, save_results

data = trigger_with_urls([
    "https://example.com/page-1",
    "https://example.com/page-2",
])
save_results(data, "my_run.json")
```

---

## Output

- Results are saved as JSON files named `scraper_studio_results_<ISO timestamp>.json`.
- The file contains the raw collector output - one record per input URL by default.

### Sample Console Output

```
Bright Data Scraper Studio
==============================
Starting Scraper Studio collector...
Queueing 3 input(s)
Job queued. Snapshot ID: j_abc123
Polling for results...
Attempt 1/60 - building
Attempt 2/60 - building
Attempt 3/60 - building
Results downloaded.
Saved to scraper_studio_results_2026-05-22T10-30-45-123456.json

Done.
```

---

## Support

- [Bright Data Help Center](https://brightdata.com/help)
- [Scraper Studio docs](https://docs.brightdata.com/scraping-automation/scraper-studio)
- [Contact Support](https://brightdata.com/contact-us)

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
