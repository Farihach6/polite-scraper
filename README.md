
# The Polite Scraper

**FlyRank Internship · Backend Track · Week 5 · Assignment A9**

The Polite Scraper is a small, ethical, end-to-end web scraping pipeline built with Python.

It targets the public practice sandbox **Books to Scrape**, downloads the first three catalogue pages, discovers 60 book URLs, fetches and extracts book details, normalizes and validates the data, stores valid records locally, survives failed pages without crashing, and generates an honest run report.

The project demonstrates the complete pipeline:

```text
Classify
    ↓
Fetch
    ↓
Cache
    ↓
Discover
    ↓
Extract
    ↓
Normalize
    ↓
Validate
    ↓
Store
    ↓
Handle Failures
    ↓
Report
````

---

# Target Classification

## Target

**Site:** `https://books.toscrape.com`

Books to Scrape is a fictional bookstore created as a safe practice environment for learning and testing web scraping.

## Why this target was selected

This project uses a public scraping practice sandbox:

* no login is required
* no paywall is involved
* no personal data is collected
* no real customer or business data is processed
* the site is designed for practicing scraping technologies

## Scope

The scraper intentionally processes only:

```text
Catalogue pages:
page-1.html
page-2.html
page-3.html
```

and the individual book detail pages discovered from those three catalogue pages.

Expected scope:

```text
3 catalogue pages
60 unique book URLs
60 book detail pages
```

Nothing outside this scope is intentionally requested.

## robots.txt

The following endpoint was checked:

```text
https://books.toscrape.com/robots.txt
```

Result:

```text
404 Not Found
```

A missing `robots.txt` file is not treated as automatic permission. The project is limited to a website explicitly designed as a scraping practice sandbox.

## Data collected

For each book, the pipeline collects:

```text
title
product_url
price_text
price_gbp
availability_text
rating_text
description
source_page
fetched_at
```

No personal or sensitive data is collected.

**I will not reuse this code on another site without checking its rules and terms first.**

---

# Features

## Polite Fetching

The scraper:

* sends a custom User-Agent
* uses a request timeout
* checks HTTP status codes
* applies a delay between real requests
* avoids unnecessary requests through caching

## Local Caching

Fetched HTML is stored locally.

On the first request:

```text
FETCH
```

On later runs:

```text
CACHE HIT
```

Cached pages prevent repeatedly requesting the same content from the target website.

---

# Pagination and Discovery

The scraper:

1. starts at catalogue page 1
2. parses book links
3. follows the website's own `next` link
4. stops after a maximum of 3 catalogue pages
5. converts relative URLs into absolute URLs
6. deduplicates discovered book URLs
7. preserves the catalogue page where each book was discovered

Discovery preserves provenance using:

```text
(book_url, source_page)
```

Expected result:

```text
catalogue_pages=3
discovered=60
unique_urls=60
```

---

# Raw Data Extraction

Every discovered book detail page is processed individually.

The scraper extracts:

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

Missing descriptions are stored as:

```text
None
```

The scraper does not invent missing data.

Expected result:

```text
detail_pages=60
```

---

# Normalization

Raw scraped data is cleaned before validation.

For example:

```text
"£51.77"
```

is converted into:

```text
51.77
```

and stored as:

```text
price_gbp
```

The normalizer also handles encoding artifacts such as:

```text
"Â£51.77"
```

which is normalized into the correct numeric price.

Both the original and normalized values are preserved:

```text
price_text
price_gbp
```

---

# Validation

All cleaned records are validated using **Pydantic**.

Validation checks include:

* title must not be blank
* price text must not be blank
* availability text must not be blank
* product URL must be an absolute HTTPS URL
* source page must be an absolute HTTPS URL
* normalized price must not be negative

Records that fail normalization or validation are separated from valid records.

---

# Failure Resilience

One failed page must not terminate the entire scraping run.

Each page fetch is isolated.

The scraper:

* catches `FetchError` per page
* logs the failed page
* skips the failed page
* continues processing the remaining pages

## Retry policy

The scraper retries once for:

```text
Timeout
HTTP 5xx server errors
```

The scraper does not retry:

```text
HTTP 404
HTTP 403
```

This prevents unnecessary or impolite repeated requests.

---

# Stage 5 Resilience Demo

A deliberately broken URL can be injected to verify that the pipeline survives a failed page.

Run:

```bash
python src/main.py --inject-fake-url
```

The expected behavior is:

```text
60 valid records
1 failed page
Pipeline completes successfully
```

Example:

```text
valid_records=60 invalid_records=0 failed_pages=1
```

The run report records the failed page instead of allowing the program to crash.

---

# Output

The pipeline writes its results to:

```text
output/
├── books.json
├── errors.json
└── run-report.json
```

## `books.json`

Contains valid, normalized, schema-validated book records.

Example:

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

## `errors.json`

Contains records that could not be normalized or validated.

A successful run currently produces:

```text
[]
```

## `run-report.json`

Contains an honest summary of the run.

Example:

```json
{
  "start_time": "2026-08-15T04:55:59.803285+00:00",
  "end_time": "2026-08-15T04:56:03.416762+00:00",
  "duration_seconds": 3.613,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1,
  "failed_page_details": [
    {
      "url": "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html",
      "reason": "HTTP 404 - not retrying"
    }
  ]
}
```

The exact numbers may differ depending on whether pages are already cached.

---

# Project Structure

```text
polite-scraper/
│
├── cache/                     # Local cached HTML pages
│
├── output/
│   ├── books.json             # Valid normalized records
│   ├── errors.json            # Invalid records/errors
│   └── run-report.json        # Summary of each run
│
├── src/
│   ├── main.py                # Pipeline orchestration
│   ├── fetcher.py             # Polite HTTP fetching, cache and retry
│   ├── extractor.py           # HTML parsing and record extraction
│   ├── normalizer.py          # Data cleaning and normalization
│   ├── schema.py              # Pydantic validation
│   └── reporter.py            # Run report generation
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

# Tech Stack

* Python 3.10+
* Requests
* BeautifulSoup4
* Pydantic

---

# Installation

Clone the repository:

```bash
git clone https://github.com/Farihach6/polite-scraper.git
```

Move into the project:

```bash
cd polite-scraper
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Run the Scraper

From the project root:

```bash
python src/main.py
```

The pipeline will:

1. Fetch or load cached catalogue pages.
2. Follow pagination for up to 3 pages.
3. Discover book URLs.
4. Deduplicate URLs.
5. Preserve source page provenance.
6. Fetch or load cached book detail pages.
7. Extract raw records.
8. Normalize the data.
9. Validate records with Pydantic.
10. Separate valid and invalid records.
11. Write JSON output.
12. Generate a run report.

Expected checkpoint:

```text
catalogue_pages=3 discovered=60 unique_urls=60
detail_pages=60
valid_records=60 invalid_records=0 failed_pages=0
```

On later runs, most pages should display:

```text
CACHE HIT
```

because the HTML is loaded from the local cache.

---

# Run the Failure Resilience Demo

To deliberately inject one broken page:

```bash
python src/main.py --inject-fake-url
```

Expected result:

```text
60 valid records
0 invalid records
1 failed page
```

The scraper should complete without crashing.

Check the report:

```powershell
Get-Content output/run-report.json
```

Expected key result:

```json
"failed_pages": 1
```

---

# Current Pipeline

```text
START
  │
  ▼
Target Classification
  │
  ▼
Fetch Catalogue Page
  │
  ▼
Cache HTML
  │
  ▼
Parse Book URLs + Next Link
  │
  ▼
Follow Pagination
  │
  ├── Page 1
  ├── Page 2
  └── Page 3
  │
  ▼
Discover 60 URLs
  │
  ▼
Deduplicate
  │
  ▼
Preserve Provenance
  │
  ▼
Fetch Detail Pages
  │
  ▼
Extract Raw Records
  │
  ▼
Normalize Data
  │
  ▼
Validate with Pydantic
  │
  ├── Valid Records
  │
  └── Invalid Records
  │
  ▼
Store JSON Output
  │
  ▼
Handle Failed Pages
  │
  ▼
Generate Run Report
  │
  ▼
END
```

---

# Politeness Rules

The scraper follows these rules:

* **Identifying User-Agent** — requests identify the scraper.
* **Timeout** — requests do not wait forever.
* **Status checking** — HTTP responses are checked before processing.
* **Caching** — already fetched pages are reused locally.
* **Minimum delay** — real requests are spaced apart.
* **Limited retries** — only timeout and 5xx errors are retried once.
* **No retry for 404/403** — missing or forbidden pages are not repeatedly requested.
* **Limited scope** — only three catalogue pages and their discovered book pages are processed.
* **Failure isolation** — one failed page does not terminate the entire pipeline.

---

# Why No Browser Was Needed

This target serves the required catalogue and book information directly in the HTML returned by standard HTTP requests.

Because:

* no JavaScript rendering was required
* no login was required
* no browser interaction was required

the project uses:

```text
requests + BeautifulSoup
```

instead of browser automation.

Using a full browser would add unnecessary complexity and resource usage for this target.

---

# Limitation

This scraper is intentionally designed for a fixed, small practice scope.

Current limitations include:

* only the first 3 catalogue pages are processed
* data is stored locally as JSON
* caching is local and file-based
* the scraper is not intended to automatically scale to arbitrary websites
* changing HTML structure may require updating the extraction selectors

---

# Final Checkpoint

The completed project demonstrates:

```text
✓ Target classification
✓ Polite HTTP requests
✓ User-Agent
✓ Timeout
✓ Local caching
✓ Pagination
✓ URL discovery
✓ URL deduplication
✓ Provenance tracking
✓ Detail page extraction
✓ Missing value handling
✓ Data normalization
✓ Pydantic validation
✓ Valid/invalid record separation
✓ JSON storage
✓ Retry policy
✓ Per-page failure isolation
✓ Broken-page resilience
✓ Honest run reporting
✓ Public GitHub publication
```

Final resilience checkpoint:

```text
60 good pages + 1 deliberately broken URL
                ↓
Pipeline does not crash
                ↓
60 valid records
failed_pages = 1
```

---

# Responsible Scraping

This project is intentionally restricted to a public scraping practice sandbox.

The code should not be interpreted as permission to scrape arbitrary websites.

Before adapting this project to another target, check:

* the site's terms and usage rules
* `robots.txt` where applicable
* authentication and access restrictions
* rate limits
* whether personal or sensitive data is involved
* whether automated access is appropriate

**I will not reuse this code on another site without checking its rules and terms first.**

````

