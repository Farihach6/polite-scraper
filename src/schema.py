"""
schema.py — record schema and validation.

Stage 4 responsibility:
    - Define the final record structure
    - Validate cleaned records before storage
"""

from __future__ import annotations

from typing import Optional

from pydantic import (
    BaseModel,
    ValidationError,
    field_validator,
)


class BookRecord(BaseModel):
    title: str
    product_url: str
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: Optional[str] = None
    description: Optional[str] = None
    source_page: str
    fetched_at: str

    @field_validator(
        "title",
        "price_text",
        "availability_text",
    )
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be blank")

        return value

    @field_validator(
        "product_url",
        "source_page",
    )
    @classmethod
    def must_be_absolute_https_url(
        cls,
        value: str,
    ) -> str:
        if not value.startswith("https://"):
            raise ValueError(
                f"must be an absolute https:// URL, got {value!r}"
            )

        return value

    @field_validator("price_gbp")
    @classmethod
    def price_must_be_non_negative(
        cls,
        value: float,
    ) -> float:
        if value < 0:
            raise ValueError(
                "price_gbp must not be negative"
            )

        return value


def validate_record(
    cleaned_record: dict,
) -> tuple[
    Optional[BookRecord],
    Optional[str],
]:
    """
    Validate a cleaned record.

    Returns:
        (record, None) if valid
        (None, error_reason) if invalid
    """

    try:
        record = BookRecord(**cleaned_record)
        return record, None

    except ValidationError as exc:
        return None, str(exc)