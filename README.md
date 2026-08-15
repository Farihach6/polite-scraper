# The Polite Scraper

FlyRank Internship · Backend Track · Week 5 · Assignment A9

A small, polite scraping pipeline that downloads the first three catalogue
pages of [Books to Scrape](https://books.toscrape.com), visits all 60 book
pages, turns messy HTML into clean, checked JSON, survives a broken page
without crashing, and ends every run with an honest report.

## Target classification (Stage 0)

- **Site:** `books.toscrape.com` — the "Books" sandbox listed on
  [toscrape.com](https://toscrape.com). Its own description states it is
  *"a fictional bookstore that desperately wants to be scraped... a safe
  place for beginners learning web scraping and for developers validating
  their scraping technologies."*
- **Why this target:** it is a public practice sandbox built specifically
  for this purpose — no real business, no personal data, no paywall, no
  login required for the pages we touch.
- **Scope:** the first 3 catalogue pages only (`catalogue/page-1.html`
  through `page-3.html`), plus the 60 individual book detail pages linked
  from them. Nothing outside that scope is requested.
- **robots.txt result:** `GET https://books.toscrape.com/robots.txt` →
  **404 Not Found**. No robots file found. (A missing file is not
  permission on its own — it is just a missing file — but combined with
  the site's explicit self-description as a scraping sandbox, scraping
  this limited scope is appropriate.)
- **Data collected:** for each book — title, product URL, price, stock
  availability, star rating, description, plus provenance
  (`source_page`, `fetched_at`). No personal data of any kind exists on
  this site.

**I will not reuse this code on another site without checking its rules
and terms first.**

## Status

- [x] Stage 0 — Check before you collect
- [x] Stage 1 — Fetch once, cache once
- [ ] Stage 2 — Find all three pages
- [ ] Stage 3 — Extract the raw records
- [ ] Stage 4 — Clean it, check it, store it
- [ ] Stage 5 — One bad page must not kill the run
- [ ] Stage 6 — Publish the evidence
- [ ] Bonus — The AI rematch

## Lane

Python 3.10+ — `requests`, `beautifulsoup4`, `pydantic` (to be added in
later stages as each is needed).

## Run (partial — Stage 1 only, full pipeline arrives by Stage 6)

```bash
pip install -r requirements.txt
python src/main.py     # first run  -> prints FETCH, creates cache/catalogue-page-1.html
python src/main.py     # second run -> prints CACHE HIT, reads the saved copy
```

### Politeness rules implemented so far

- **User-Agent:** `FlyRankInternshipA9/1.0 (+https://github.com/your-username/scraper)`
- **Timeout:** 10 seconds — a request never hangs forever
- **Status check:** only HTTP 200 is treated as a successful fetch
- **Cache:** every fetched page is saved under `cache/`; later runs read
  the saved copy instead of re-requesting the live site
- **Delay:** 0.5s minimum between real (non-cached) requests

### Tests

`tests/test_fetcher_smoke.py` is a network-free smoke test that mocks
the HTTP layer to prove the fetch → cache → cache-hit logic is correct
independent of network access:

```bash
python tests/test_fetcher_smoke.py
```
