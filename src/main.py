"""
The Polite Scraper — entry point.

Current status:
    Stage 0: Target classification
    Stage 1: Fetch + Cache
    Stage 2: Discovery + Pagination + Deduplication
    Stage 3: Extract raw records
"""

import json

from pathlib import Path
from urllib.parse import urlparse

from extractor import (
    extract_book_record,
    parse_catalogue_page,
)

from fetcher import polite_get


START_URL = (
    "https://books.toscrape.com/catalogue/page-1.html"
)

CACHE_DIR = (
    Path(__file__).resolve().parent.parent / "cache"
)

MAX_CATALOGUE_PAGES = 3


def discover_book_urls(
    start_url: str,
    cache_dir: Path,
    max_pages: int = MAX_CATALOGUE_PAGES,
):
    """
    Discover books while preserving their source catalogue page.

    Returns:

        catalogue_pages_visited

        all_pairs:
            [(book_url, source_page), ...]

        unique_pairs:
            Deduplicated while preserving first appearance.
    """

    page_url = start_url

    page_num = 1

    all_pairs: list[tuple[str, str]] = []

    while (
        page_url
        and page_num <= max_pages
    ):

        filename = (
            f"catalogue-page-{page_num}.html"
        )

        result = polite_get(
            page_url,
            cache_dir,
            filename,
        )

        book_urls, next_url = (
            parse_catalogue_page(
                result.html,
                page_url,
            )
        )

        for book_url in book_urls:

            all_pairs.append(
                (
                    book_url,
                    page_url,
                )
            )

        page_url = next_url

        page_num += 1

    catalogue_pages_visited = (
        page_num - 1
    )

    # Dedupe by book URL while preserving
    # the first source page.

    seen: set[str] = set()

    unique_pairs: list[
        tuple[str, str]
    ] = []

    for book_url, source_page in all_pairs:

        if book_url not in seen:

            seen.add(book_url)

            unique_pairs.append(
                (
                    book_url,
                    source_page,
                )
            )

    return (
        catalogue_pages_visited,
        all_pairs,
        unique_pairs,
    )


def _book_cache_filename(
    product_url: str,
) -> str:
    """
    Convert a product URL into a unique,
    flat cache filename.
    """

    path_parts = [
        part
        for part in urlparse(
            product_url
        ).path.split("/")
        if part
    ]

    slug = (
        path_parts[-2]
        if len(path_parts) >= 2
        else path_parts[-1]
    )

    return f"book-{slug}.html"


def extract_all_records(
    unique_pairs: list[
        tuple[str, str]
    ],
    cache_dir: Path,
) -> list[dict]:
    """
    Fetch every unique book page and
    extract its raw record.
    """

    records: list[dict] = []

    for product_url, source_page in unique_pairs:

        filename = _book_cache_filename(
            product_url
        )

        result = polite_get(
            product_url,
            cache_dir,
            filename,
        )

        record = extract_book_record(
            result.html,
            product_url,
            source_page,
        )

        records.append(record)

    return records


def main() -> None:

    (
        catalogue_pages,
        all_pairs,
        unique_pairs,
    ) = discover_book_urls(
        START_URL,
        CACHE_DIR,
    )

    print(
        f"catalogue_pages={catalogue_pages} "
        f"discovered={len(all_pairs)} "
        f"unique_urls={len(unique_pairs)}"
    )

    records = extract_all_records(
        unique_pairs,
        CACHE_DIR,
    )

    print(
        f"detail_pages={len(records)}"
    )

    # Show the first extracted record.
    if records:

        print(
            json.dumps(
                records[0],
                indent=2,
            )
        )


if __name__ == "__main__":
    main()