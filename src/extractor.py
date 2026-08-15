"""
extractor.py — HTML parsing.

Stage 2 responsibilities:
    - Parse a catalogue page
    - Extract absolute URLs of every book
    - Find the catalogue's own "next" link
"""

from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup


def parse_catalogue_page(
    html: str,
    page_url: str,
) -> tuple[list[str], str | None]:
    """
    Parse one catalogue page.

    Returns:
        book_urls: Absolute URLs of all books on the page.
        next_url: Absolute URL of the next catalogue page,
                  or None if there is no next page.
    """

    soup = BeautifulSoup(html, "html.parser")

    book_urls: list[str] = []

    for anchor in soup.select("article.product_pod h3 a"):
        href = anchor.get("href")

        if href:
            absolute_url = urljoin(page_url, href)
            book_urls.append(absolute_url)

    next_url: str | None = None

    next_anchor = soup.select_one("li.next a")

    if next_anchor is not None:
        href = next_anchor.get("href")

        if href:
            next_url = urljoin(page_url, href)

    return book_urls, next_url