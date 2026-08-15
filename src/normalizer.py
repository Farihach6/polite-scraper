"""
normalizer.py — turning raw strings into clean, typed values.

Stage 4 responsibilities:
    - Convert raw price text into a numeric price_gbp
    - Normalize the canonical product URL
"""

from __future__ import annotations

import re


_PRICE_PATTERN = re.compile(r"\d+\.?\d*")


def parse_price_gbp(price_text: str | None) -> float:
    """
    Extract a numeric price from text.

    Examples:
        "£51.77" -> 51.77
        "Â£51.77" -> 51.77

    Raises ValueError if no numeric price can be found.
    """

    if not price_text:
        raise ValueError(
            "price_text is missing, cannot derive price_gbp"
        )

    match = _PRICE_PATTERN.search(price_text)

    if not match:
        raise ValueError(
            f"could not parse a number out of "
            f"price_text={price_text!r}"
        )

    return float(match.group())


def normalize_record(raw_record: dict) -> dict:
    """
    Return a new cleaned dictionary.

    Does not modify the original raw record.
    """

    cleaned = dict(raw_record)

    cleaned["price_gbp"] = parse_price_gbp(
        raw_record.get("price_text")
    )

    product_url = raw_record.get("product_url")

    if product_url:
        cleaned["product_url"] = product_url.strip()

    return cleaned