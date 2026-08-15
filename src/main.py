"""
The Polite Scraper — entry point.

FlyRank Internship, Backend Track, Week 5, Assignment A9.

Current status: Stage 0 (target classification) and Stage 1
(fetch + cache the first catalogue page) are implemented.
Extract / normalize / validate / store / report land in later stages.
"""

from pathlib import Path

from fetcher import polite_get

BASE_URL = "https://books.toscrape.com/catalogue/page-1.html"
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_FILE = "catalogue-page-1.html"


def main() -> None:
    result = polite_get(BASE_URL, CACHE_DIR, CACHE_FILE)
    print(
        f"Stage 1 checkpoint -> from_cache={result.from_cache} "
        f"status={result.status_code} size_bytes={result.size_bytes}"
    )


if __name__ == "__main__":
    main()
