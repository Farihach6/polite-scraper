# The Polite Scraper

FlyRank Internship · Backend Track · Week 5 · Assignment A9

A small, polite scraping pipeline that downloads the first three catalogue pages of [Books to Scrape](https://books.toscrape.com), discovers all 60 book URLs, visits every book detail page, extracts the raw book records, and uses local caching to avoid repeatedly requesting the same pages.

Cleaning, validation, fault tolerance, storage, and final reporting are implemented in later stages.

## Target classification (Stage 0)

* **Site:** `books.toscrape.com` — the "Books" sandbox listed on [toscrape.com](https://toscrape.com). Its own description states it is *"a fictional bookstore that desperately wants to be scraped... a safe place for beginners learning web scraping and for developers validating their scraping technologies."*
* **Why this target:** it is a public practice sandbox built specifically for this purpose — no real business, no personal data, no paywall, and no login required for the pages we touch.
* **Scope:** the first 3 catalogue pages only (`catalogue/page-1.html` through `page-3.html`), plus the 60 individual book detail pages linked from them. Nothing outside that scope is requested.
* **robots.txt result:** `GET https://books.toscrape.com/robots.txt` → **404 Not Found**. No robots file was found. A missing file is not permission on its own, but combined with the site's explicit self-description as a scraping sandbox, this limited scope is appropriate.
* **Data collected:** for each book — title, product URL, raw price text, raw stock availability text, raw star rating text, description, plus provenance (`source_page`, `fetched_at`). No personal data is collected.

**I will not reuse this code on another site without checking its rules and terms first.**

## Status

* [x] Stage 0 — Check before you collect
* [x] Stage 1 — Fetch once, cache once
* [x] Stage 2 — Find all three pages
* [x] Stage 3 — Extract the raw records
* [ ] Stage 4 — Clean it, check it, store it
* [ ] Stage 5 — One bad page must not kill the run
* [ ] Stage 6 — Publish the evidence
* [ ] Bonus — The AI rematch

## What is implemented

### Stage 1 — Fetch and cache

The scraper:

* sends a custom User-Agent
* uses a request timeout
* accepts only HTTP 200 as a successful response
* saves fetched HTML in the local `cache/` directory
* uses cached files on later runs
* waits at least 0.5 seconds between real, non-cached requests

### Stage 2 — Discovery, pagination, and deduplication

The scraper:

* starts from `catalogue/page-1.html`
* follows the catalogue's own `next` links
* stops after a maximum of 3 catalogue pages
* extracts every book URL from each page
* resolves relative URLs using `urljoin`
* preserves the catalogue page where each book was discovered
* deduplicates book URLs while preserving first-seen order and provenance

For Stage 2, discovery returns book/source pairs:

```text
(book_url, source_page)
```

This allows the pipeline to retain provenance for every extracted record.

### Stage 3 — Raw record extraction

After discovering the 60 unique book URLs, the scraper:

* fetches every book detail page using the same polite fetch and cache system
* creates a unique cache filename for each book
* extracts data only from the relevant product area
* keeps values as raw strings for later normalization
* stores missing descriptions as `None`
* records provenance and extraction time

Each extracted record contains exactly these 8 raw fields:

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

Example record shape:

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

> `price_text`, availability, and rating are intentionally kept in their raw extracted form. Cleaning and conversion happen in Stage 4.

## Project structure

```text
polite-scraper/
│
├── cache/                     # Cached catalogue and book HTML pages
│
├── src/
│   ├── main.py                # Pipeline entry point
│   ├── fetcher.py             # Polite HTTP fetching and caching
│   ├── extractor.py           # Catalogue and book-detail HTML parsing
│   ├── normalizer.py          # Later stage
│   ├── schema.py              # Later stage
│   └── reporter.py            # Later stage
│
├── tests/
│   ├── test_fetcher_smoke.py
│   ├── test_extractor_smoke.py
│   └── test_stage3_extract_smoke.py
│
├── output/
├── ai-version/
├── requirements.txt
└── README.md
```

## Lane

Python 3.10+

Current dependencies:

* `requests`
* `beautifulsoup4`

Additional dependencies such as `pydantic` will be added only when required by later stages.

## Installation

Clone the repository:

```bash
git clone https://github.com/Farihach6/polite-scraper.git
cd polite-scraper
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the scraper

From the project root:

```bash
python src/main.py
```

### First complete run

The scraper will:

1. Fetch or read the first catalogue page.
2. Follow the `next` link to page 2.
3. Follow the `next` link to page 3.
4. Discover 60 book URLs.
5. Preserve each book's source catalogue page.
6. Fetch all 60 book detail pages.
7. Extract one raw record for every book.
8. Print the discovery and extraction totals.
9. Display the first extracted record.

Expected summary:

```text
catalogue_pages=3 discovered=60 unique_urls=60
detail_pages=60
```

### Later runs

Because catalogue pages and book detail pages are cached, later runs should mostly show:

```text
CACHE HIT
```

instead of making new network requests.

## Current pipeline

```text
START
  │
  ▼
Fetch catalogue page
  │
  ▼
Parse book URLs + next link
  │
  ▼
Follow next catalogue page
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
Fetch each book detail page
  │
  ▼
Extract 8 raw fields
  │
  ▼
60 raw records
```

## Politeness rules implemented

* **User-Agent:** identifies the scraper
* **Timeout:** requests do not wait forever
* **Status check:** only HTTP 200 is treated as a successful fetch
* **Cache:** fetched HTML is stored under `cache/`
* **Cache reuse:** later runs use saved HTML instead of repeatedly requesting the same page
* **Delay:** at least 0.5 seconds between real, non-cached requests
* **Limited scope:** only the first 3 catalogue pages and their linked book detail pages are processed

## Tests

The project includes network-free smoke tests so core logic can be verified without depending on the live website.

### Stage 1

`tests/test_fetcher_smoke.py`

Tests:

```text
fetch → cache → cache hit
```

The HTTP layer is mocked, proving that caching works independently of network availability.

### Stage 2

`tests/test_extractor_smoke.py`

Tests:

* catalogue page parsing
* absolute URL resolution
* pagination
* `max_pages=3` stopping condition
* URL deduplication
* source catalogue page preservation

### Stage 3

`tests/test_stage3_extract_smoke.py`

Tests:

* all 8 raw fields are extracted correctly
* provenance fields pass through correctly
* missing descriptions become `None`
* `fetched_at` is a valid ISO timestamp

Run all tests with:

```bash
python -m pytest -q
```

## Current progress

The pipeline currently completes:

```text
Stage 0 → Target classification
Stage 1 → Polite fetch + cache
Stage 2 → Discovery + pagination + deduplication
Stage 3 → Raw detail-page extraction
```

The next stage is:

```text
Stage 4 → Clean it, check it, store it
```

Stage 4 will normalize the raw values, validate the records, and prepare structured output for storage.

## Responsible scraping note

This project is intentionally limited to a public scraping practice sandbox. The code is not presented as permission to scrape arbitrary websites.

Before adapting this scraper to another target, check:

* the site's terms and usage rules
* `robots.txt` where applicable
* authentication and access restrictions
* rate limits
* whether personal or sensitive data is involved

**I will not reuse this code on another site without checking its rules and terms first.**
