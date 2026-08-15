"""
The Polite Scraper — entry point.

FlyRank Internship, Backend Track, Week 5, Assignment A9.

Current status: all seven stages are implemented.
    Stage 0 - target classification (see README.md)
    Stage 1 - fetch + cache (fetcher.py)
    Stage 2 - discover 3 catalogue pages / 60 book URLs (extractor.py)
    Stage 3 - extract the 8 raw fields per book (extractor.py)
    Stage 4 - normalize + validate + store (normalizer.py, schema.py)
    Stage 5 - survive a broken page, report the run (this file, reporter.py)
    Stage 6 - publish the evidence (README.md, public repo)

Usage:
    python src/main.py                    # normal run
    python src/main.py --inject-fake-url  # Stage 5 proof: adds one
                                           # made-up book URL so you
                                           # can watch the run survive
                                           # it and report failed_pages=1
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from extractor import extract_book_record, parse_catalogue_page
from fetcher import FetchError, polite_get
from normalizer import normalize_record
from reporter import build_run_report
from schema import validate_record
import json

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
MAX_CATALOGUE_PAGES = 3

# A URL that will never exist on the real site — used only when
# --inject-fake-url is passed, to prove Stage 5 resilience by hand.
FAKE_BOOK_URL = "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html"


def _new_stats() -> dict:
    return {"pages_fetched": 0, "cache_hits": 0, "failed_pages": []}


def safe_polite_get(url: str, cache_dir: Path, filename: str, stats: dict):
    """
    Wrap fetcher.polite_get so one broken page never crashes the run:
    on success, tallies pages_fetched/cache_hits and returns the
    FetchResult; on FetchError, logs the failure into stats and
    returns None so the caller can skip this page and keep going.
    """
    try:
        result = polite_get(url, cache_dir, filename)
    except FetchError as exc:
        print(f"SKIP       {url}  ({exc.reason})")
        stats["failed_pages"].append({"url": url, "reason": exc.reason})
        return None

    if result.from_cache:
        stats["cache_hits"] += 1
    else:
        stats["pages_fetched"] += 1
    return result


def discover_book_urls(
    start_url: str, cache_dir: Path, stats: dict, max_pages: int = MAX_CATALOGUE_PAGES
):
    """
    Walk the catalogue's own "next" links starting at `start_url`,
    stopping after `max_pages` pages (or sooner if there is no next
    link, or if a catalogue page itself can't be fetched).

    Returns (catalogue_pages_visited, all_pairs, unique_pairs) where
    each pair is (book_url, source_page).
    """
    page_url = start_url
    page_num = 1
    all_pairs: list[tuple[str, str]] = []

    while page_url and page_num <= max_pages:
        filename = f"catalogue-page-{page_num}.html"
        result = safe_polite_get(page_url, cache_dir, filename, stats)
        if result is None:
            # A broken catalogue page ends discovery early, but does
            # not crash the run — whatever books were already found
            # still get processed.
            break

        book_urls, next_url = parse_catalogue_page(result.html, page_url)
        for book_url in book_urls:
            all_pairs.append((book_url, page_url))

        page_url = next_url
        page_num += 1

    catalogue_pages_visited = page_num - 1

    seen: set[str] = set()
    unique_pairs: list[tuple[str, str]] = []
    for book_url, source_page in all_pairs:
        if book_url not in seen:
            seen.add(book_url)
            unique_pairs.append((book_url, source_page))

    return catalogue_pages_visited, all_pairs, unique_pairs


def _book_cache_filename(product_url: str) -> str:
    path_parts = [p for p in urlparse(product_url).path.split("/") if p]
    slug = path_parts[-2] if len(path_parts) >= 2 else path_parts[-1]
    return f"book-{slug}.html"


def extract_all_records(
    unique_pairs: list[tuple[str, str]], cache_dir: Path, stats: dict
) -> list[dict]:
    """
    Fetch (politely, with caching + retry) every book detail page and
    extract its raw 8-field record. A page that fails to fetch is
    logged into stats["failed_pages"] and skipped — it simply does
    not produce a record, and every other page is unaffected.
    """
    records: list[dict] = []
    for product_url, source_page in unique_pairs:
        filename = _book_cache_filename(product_url)
        result = safe_polite_get(product_url, cache_dir, filename, stats)
        if result is None:
            continue
        record = extract_book_record(result.html, product_url, source_page)
        records.append(record)
    return records


def build_clean_dataset(raw_records: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Normalize + validate every raw record.

    Returns (valid_records, errors):
        - valid_records: cleaned, schema-validated records, deduped by
          canonical product_url, so re-running never doubles the count
        - errors: [{"product_url": ..., "reason": ...}, ...] for every
          record that fetched fine but failed to normalize or validate
          (distinct from a page that failed to fetch at all)
    """
    valid_by_url: dict[str, dict] = {}
    errors: list[dict] = []

    for raw in raw_records:
        product_url = raw.get("product_url")

        try:
            cleaned = normalize_record(raw)
        except ValueError as exc:
            errors.append({"product_url": product_url, "reason": str(exc)})
            continue

        record, error_reason = validate_record(cleaned)
        if error_reason is not None:
            errors.append({"product_url": product_url, "reason": error_reason})
            continue

        valid_by_url[record.product_url] = record.model_dump()

    valid_records = list(valid_by_url.values())
    return valid_records, errors


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    start_time = datetime.now(timezone.utc)
    stats = _new_stats()

    catalogue_pages, all_pairs, unique_pairs = discover_book_urls(START_URL, CACHE_DIR, stats)

    if "--inject-fake-url" in sys.argv:
        print(f"INJECT     {FAKE_BOOK_URL}  (deliberately broken, Stage 5 proof)")
        unique_pairs = list(unique_pairs) + [(FAKE_BOOK_URL, START_URL)]

    print(
        f"catalogue_pages={catalogue_pages} "
        f"discovered={len(all_pairs)} "
        f"unique_urls={len(unique_pairs)}"
    )

    raw_records = extract_all_records(unique_pairs, CACHE_DIR, stats)
    print(f"detail_pages={len(raw_records)}")

    valid_records, errors = build_clean_dataset(raw_records)

    write_json(OUTPUT_DIR / "books.json", valid_records)
    write_json(OUTPUT_DIR / "errors.json", errors)

    report = build_run_report(
        start_time=start_time,
        pages_fetched=stats["pages_fetched"],
        cache_hits=stats["cache_hits"],
        valid_records=len(valid_records),
        invalid_records=len(errors),
        failed_pages=stats["failed_pages"],
    )
    write_json(OUTPUT_DIR / "run-report.json", report)

    print(
        f"valid_records={len(valid_records)} "
        f"invalid_records={len(errors)} "
        f"failed_pages={report['failed_pages']}"
    )
    if valid_records:
        print(json.dumps(valid_records[0], indent=2))


if __name__ == "__main__":
    main()