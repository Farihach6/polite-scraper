"""
The Polite Scraper — entry point.

FlyRank Internship, Backend Track, Week 5, Assignment A9.

Stages implemented:

    Stage 0 — Target classification
    Stage 1 — Fetch + cache
    Stage 2 — Discovery + pagination + deduplication
    Stage 3 — Raw record extraction
    Stage 4 — Normalize + validate + store
"""

import json

from pathlib import Path
from urllib.parse import urlparse

from extractor import (
    extract_book_record,
    parse_catalogue_page,
)

from fetcher import polite_get

from normalizer import normalize_record

from schema import validate_record


START_URL = (
    "https://books.toscrape.com/catalogue/page-1.html"
)

CACHE_DIR = (
    Path(__file__).resolve().parent.parent
    / "cache"
)

OUTPUT_DIR = (
    Path(__file__).resolve().parent.parent
    / "output"
)

MAX_CATALOGUE_PAGES = 3


def discover_book_urls(
    start_url: str,
    cache_dir: Path,
    max_pages: int = MAX_CATALOGUE_PAGES,
):
    """
    Discover books while preserving the catalogue
    page where each book was found.
    """

    page_url = start_url

    page_num = 1

    all_pairs: list[
        tuple[str, str]
    ] = []

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

    # Deduplicate while preserving the
    # first source page.

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
    Fetch every unique book detail page
    and extract its raw record.
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


def build_clean_dataset(
    raw_records: list[dict],
) -> tuple[
    list[dict],
    list[dict],
]:
    """
    Normalize and validate all raw records.

    Valid records are deduplicated by
    canonical product URL.

    Invalid records are returned as:

        {
            "product_url": "...",
            "reason": "..."
        }
    """

    valid_by_url: dict[
        str,
        dict,
    ] = {}

    errors: list[dict] = []

    for raw in raw_records:

        product_url = raw.get(
            "product_url"
        )

        # ---------- NORMALIZE ----------

        try:

            cleaned = normalize_record(
                raw
            )

        except ValueError as exc:

            errors.append(
                {
                    "product_url": product_url,
                    "reason": str(exc),
                }
            )

            continue

        # ---------- VALIDATE ----------

        record, error_reason = (
            validate_record(
                cleaned
            )
        )

        if error_reason is not None:

            errors.append(
                {
                    "product_url": product_url,
                    "reason": error_reason,
                }
            )

            continue

        # ---------- DEDUPLICATE ----------

        valid_by_url[
            record.product_url
        ] = record.model_dump()

    valid_records = list(
        valid_by_url.values()
    )

    return (
        valid_records,
        errors,
    )


def write_json(
    path: Path,
    data,
) -> None:
    """
    Write JSON safely using UTF-8.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def main() -> None:

    # ---------- DISCOVERY ----------

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

    # ---------- EXTRACTION ----------

    raw_records = extract_all_records(
        unique_pairs,
        CACHE_DIR,
    )

    print(
        f"detail_pages={len(raw_records)}"
    )

    # ---------- CLEAN + VALIDATE ----------

    valid_records, errors = (
        build_clean_dataset(
            raw_records
        )
    )

    # ---------- STORE ----------

    write_json(
        OUTPUT_DIR / "books.json",
        valid_records,
    )

    write_json(
        OUTPUT_DIR / "errors.json",
        errors,
    )

    # ---------- SUMMARY ----------

    print(
        f"valid_records={len(valid_records)} "
        f"invalid_records={len(errors)}"
    )

    if valid_records:

        print(
            json.dumps(
                valid_records[0],
                indent=2,
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()