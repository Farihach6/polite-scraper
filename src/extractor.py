"""
extractor.py — HTML parsing.

Stage 2:
    - Parse catalogue pages
    - Extract book URLs
    - Find the next catalogue page

Stage 3:
    - Extract raw data from a single book detail page
"""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def parse_catalogue_page(
    html: str,
    page_url: str,
) -> tuple[list[str], str | None]:
    """
    Parse one catalogue page.
    """

    soup = BeautifulSoup(html, "html.parser")

    book_urls: list[str] = []

    for anchor in soup.select("article.product_pod h3 a"):
        href = anchor.get("href")

        if href:
            book_urls.append(
                urljoin(page_url, href)
            )

    next_url: str | None = None

    next_anchor = soup.select_one("li.next a")

    if next_anchor is not None:
        href = next_anchor.get("href")

        if href:
            next_url = urljoin(page_url, href)

    return book_urls, next_url


def extract_book_record(
    html: str,
    product_url: str,
    source_page: str,
) -> dict:
    """
    Extract a single book detail page into 8 raw fields.
    """

    soup = BeautifulSoup(html, "html.parser")

    # Scope extraction to the actual product section.
    product_main = soup.select_one("div.product_main")

    # ---------------- TITLE ----------------

    title = None

    if product_main is not None:
        title_el = product_main.select_one("h1")

        if title_el is not None:
            title = title_el.get_text(strip=True)

    # ---------------- PRICE ----------------

    price_text = None

    if product_main is not None:
        price_el = product_main.select_one("p.price_color")

        if price_el is not None:
            price_text = price_el.get_text(strip=True)

    # ---------------- AVAILABILITY ----------------

    availability_text = None

    if product_main is not None:
        availability_el = product_main.select_one(
            "p.availability"
        )

        if availability_el is not None:
            availability_text = " ".join(
                availability_el.get_text().split()
            )

    # ---------------- RATING ----------------

    rating_text = None

    if product_main is not None:
        rating_el = product_main.select_one(
            "p.star-rating"
        )

        if rating_el is not None:

            classes = rating_el.get("class", [])

            rating_words = [
                c
                for c in classes
                if c != "star-rating"
            ]

            if rating_words:
                rating_text = rating_words[0]

    # ---------------- DESCRIPTION ----------------

    description = None

    description_heading = soup.select_one(
        "#product_description"
    )

    if description_heading is not None:

        description_p = (
            description_heading.find_next_sibling("p")
        )

        if description_p is not None:
            description = description_p.get_text(
                strip=True
            )

    # ---------------- RETURN RAW RECORD ----------------

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }