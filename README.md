
# The Polite Scraper

FlyRank Internship · Backend Track · Week 5 · Assignment A9

A small, polite scraping pipeline that downloads the first three catalogue pages of Books to Scrape, discovers all 60 book URLs, visits every book detail page, extracts raw records, normalizes the data, validates it, and stores the results locally.

The pipeline uses caching to avoid repeatedly requesting the same pages and separates valid records from invalid ones.

## Target classification (Stage 0)

* **Site:** `books.toscrape.com` — the "Books" sandbox listed on `toscrape.com`. Its description identifies it as a fictional bookstore designed as a safe practice environment for web scraping.
* **Why this target:** it is a public practice sandbox — no real business, no personal data, no paywall, and no login required for the pages used in this project.
* **Scope:** the first 3 catalogue pages only (`catalogue/page-1.html` through `page-3.html`), plus the 60 individual book detail pages linked from them.
* **robots.txt result:** `GET https://books.toscrape.com/robots.txt` → **404 Not Found**. A missing robots file is not permission by itself, but this project is limited to a site explicitly designed as a scraping practice sandbox.
* **Data collected:** title, product URL, raw price, normalized price, stock availability, star rating, description, and provenance fields (`source_page`, `fetched_at`). No personal data is collected.

**I will not reuse this code on another site without checking its rules and terms first.**

## Status

* [x] Stage 0 — Check before you collect
* [x] Stage 1 — Fetch once, cache once
* [x] Stage 2 — Find all three pages
* [x] Stage 3 — Extract the raw records
* [x] Stage 4 — Clean it, check it, store it
* [ ] Stage 5 — One bad page must not kill the run
* [ ] Stage 6 — Publish the evidence
* [ ] Bonus — The AI rematch

# What is implemented

## Stage 1 — Fetch and cache

The scraper:

* sends a custom User-Agent
* uses a request timeout
* accepts HTTP 200 as a successful response
* saves fetched HTML in the local `cache/` directory
* uses cached files on later runs
* waits between real, non-cached requests

## Stage 2 — Discovery, pagination, and deduplication

The scraper:

* starts from `catalogue/page-1.html`
* follows the catalogue's own `next` links
* stops after a maximum of 3 catalogue pages
* extracts every book URL from each page
* resolves relative URLs using `urljoin`
* preserves the catalogue page where each book was discovered
* deduplicates book URLs while preserving first-seen order

Discovery stores provenance as:

```text
(book_url, source_page)
```

This allows every extracted record to retain information about where the book was discovered.

## Stage 3 — Raw record extraction

After discovering the 60 unique book URLs, the scraper:

* fetches every book detail page
* uses the same polite fetch and cache system
* creates a unique cache filename for each book
* extracts data from the relevant product area
* keeps raw values before normalization
* stores missing descriptions as `None`
* records provenance and extraction time

Each raw record contains these 8 fields:

```text
title
product_url
price_text
availability_text
rating_text
description
source_page
fetched_at
```

Example raw record:

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "Book description...",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-08-15T00:00:00+00:00"
}
```

## Stage 4 — Normalize, validate, and store

Stage 4 processes every raw record through three steps:

```text
Raw Record
    ↓
Normalization
    ↓
Validation
    ↓
Valid / Invalid Separation
    ↓
JSON Storage
```

### Normalization

The raw price text is converted into a numeric value:

```text
"£51.77" → 51.77
```

The normalized field is:

```text
price_gbp
```

The normalizer also handles the encoding artifact encountered during extraction:

```text
"Â£51.77" → 51.77
```

The numeric part is extracted and converted into a Python `float`.

### Validation

The cleaned records are validated using **Pydantic**.

Validation checks include:

* title must not be blank
* price text must not be blank
* availability text must not be blank
* `product_url` must be an absolute HTTPS URL
* `source_page` must be an absolute HTTPS URL
* `price_gbp` must not be negative

Invalid records are not included in the valid dataset.

### Storage

After normalization and validation, records are separated into:

```text
output/
├── books.json
└── errors.json
```

* `books.json` contains valid, cleaned, validated records.
* `errors.json` contains records that could not be normalized or validated.

Valid records are deduplicated using their `product_url`.

### Current Stage 4 result

The current pipeline successfully produces:

```text
catalogue_pages=3 discovered=60 unique_urls=60
detail_pages=60
valid_records=60 invalid_records=0
```

This means:

* 60 book pages were extracted
* 60 records were normalized
* 60 records passed validation
* 0 records failed validation

Example cleaned record:

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "price_gbp": 51.77,
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "Book description...",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-08-15T00:00:00+00:00"
}
```

# Project structure

```text
polite-scraper/
│
├── cache/                     # Cached catalogue and book HTML pages
│
├── output/
│   ├── books.json             # Valid normalized records
│   └── errors.json            # Invalid records and errors
│
├── src/
│   ├── main.py                # Pipeline entry point
│   ├── fetcher.py             # Polite HTTP fetching and caching
│   ├── extractor.py           # HTML parsing and raw extraction
│   ├── normalizer.py          # Data normalization
│   ├── schema.py              # Pydantic validation schema
│   └── reporter.py            # Later reporting stage
│
├── tests/
│   ├── test_fetcher_smoke.py
│   ├── test_extractor_smoke.py
│   └── test_stage3_extract_smoke.py
│
├── ai-version/
├── requirements.txt
└── README.md
```

# Tech stack

Python 3.10+

Current dependencies:

* `requests`
* `beautifulsoup4`
* `pydantic`

# Installation

Clone the repository:

```bash
git clone https://github.com/Farihach6/polite-scraper.git
cd polite-scraper
```

Install dependencies:

```bash
pip install -r requirements.txt
```

# Run the scraper

From the project root:

```bash
python src/main.py
```

The pipeline will:

1. Read or fetch the first catalogue page.
2. Follow the catalogue pagination.
3. Stop after 3 catalogue pages.
4. Discover all book URLs.
5. Deduplicate the URLs.
6. Preserve each book's source catalogue page.
7. Fetch or read cached book detail pages.
8. Extract raw book records.
9. Normalize the records.
10. Validate the records using Pydantic.
11. Separate valid and invalid records.
12. Store the results in JSON files.

Expected summary:

```text
catalogue_pages=3 discovered=60 unique_urls=60
detail_pages=60
valid_records=60 invalid_records=0
```

# Current pipeline

```text
START
  │
  ▼
Fetch catalogue pages
  │
  ▼
Parse book URLs + next links
  │
  ▼
Follow pagination
  │
  ├── Page 1
  ├── Page 2
  └── Page 3
  │
  ▼
Discover 60 book URLs
  │
  ▼
Deduplicate URLs
  │
  ▼
Preserve (book_url, source_page)
  │
  ▼
Fetch each detail page
  │
  ▼
Extract 8 raw fields
  │
  ▼
Normalize price and record values
  │
  ▼
Validate with Pydantic
  │
  ├── Valid records
  │
  └── Invalid records
  │
  ▼
Store JSON output
```

# Politeness rules

* **User-Agent:** identifies the scraper
* **Timeout:** requests do not wait forever
* **Status check:** HTTP responses are checked
* **Cache:** fetched HTML is stored locally
* **Cache reuse:** later runs reuse cached pages
* **Delay:** a minimum delay is applied between real requests
* **Limited scope:** only 3 catalogue pages and their linked book detail pages are processed

# Tests

The project includes network-free smoke tests so core logic can be verified without depending on the live website.

## Stage 1

`tests/test_fetcher_smoke.py`

Tests:

```text
fetch → cache → cache hit
```

The HTTP layer is mocked to verify that the caching logic works independently of network access.

## Stage 2

`tests/test_extractor_smoke.py`

Tests:

* catalogue page parsing
* absolute URL resolution
* pagination
* `max_pages=3` stopping condition
* URL deduplication
* source catalogue page preservation

## Stage 3

`tests/test_stage3_extract_smoke.py`

Tests:

* all 8 raw fields are extracted
* provenance fields are preserved
* missing descriptions become `None`
* `fetched_at` is a valid ISO timestamp

Run all tests:

```bash
python -m pytest -q
```

# Current progress

The pipeline currently completes:

```text
Stage 0 → Target classification
Stage 1 → Fetch + cache
Stage 2 → Discovery + pagination + deduplication
Stage 3 → Raw detail-page extraction
Stage 4 → Normalize + validate + store
```

## Next stage

```text
Stage 5 → One bad page must not kill the run
```

Stage 5 will focus on fault tolerance so that a single failed or malformed page does not terminate the entire scraping pipeline.

# Responsible scraping note

This project is intentionally limited to a public scraping practice sandbox. The code is not presented as permission to scrape arbitrary websites.

Before adapting this scraper to another target, check:

* the site's terms and usage rules
* `robots.txt` where applicable
* authentication and access restrictions
* rate limits
* whether personal or sensitive data is involved

**I will not reuse this code on another site without checking its rules and terms first.**

