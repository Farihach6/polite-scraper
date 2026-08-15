"""
The Polite Scraper — entry point.

Current status:
    Stage 0: Target classification
    Stage 1: Fetch + cache
    Stage 2: Discovery + pagination + deduplication
"""

from pathlib import Path

from extractor import parse_catalogue_page
from fetcher import polite_get


START_URL = "https://books.toscrape.com/catalogue/page-1.html"

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
    Walk catalogue pages using their own 'next' links.

    Stops when:
        - There is no next page, OR
        - max_pages is reached.

    Returns:
        catalogue_pages_visited,
        all_book_urls,
        unique_book_urls
    """

    page_url = start_url
    page_num = 1

    all_book_urls: list[str] = []

    while page_url and page_num <= max_pages:

        filename = f"catalogue-page-{page_num}.html"

        result = polite_get(
            page_url,
            cache_dir,
            filename,
        )

        book_urls, next_url = parse_catalogue_page(
            result.html,
            page_url,
        )

        all_book_urls.extend(book_urls)

        page_url = next_url
        page_num += 1

    catalogue_pages_visited = page_num - 1

    # Remove duplicates while preserving order.
    unique_book_urls = list(
        dict.fromkeys(all_book_urls)
    )

    return (
        catalogue_pages_visited,
        all_book_urls,
        unique_book_urls,
    )


def main() -> None:

    catalogue_pages, discovered, unique_urls = (
        discover_book_urls(
            START_URL,
            CACHE_DIR,
        )
    )

    print(
        f"catalogue_pages={catalogue_pages} "
        f"discovered={len(discovered)} "
        f"unique_urls={len(unique_urls)}"
    )


if __name__ == "__main__":
    main()