"""
reporter.py — run-report.json builder.

Stage 5 responsibility (implemented here): turn the stats collected
during a run into a few honest numbers — start time, duration, pages
fetched, cache hits, valid/invalid records, failed pages — so a run
that goes wrong is noticed instead of failing silently.
"""

from __future__ import annotations

from datetime import datetime, timezone


def build_run_report(
    start_time: datetime,
    pages_fetched: int,
    cache_hits: int,
    valid_records: int,
    invalid_records: int,
    failed_pages: list[dict],
) -> dict:
    """
    `failed_pages` is a list of {"url": ..., "reason": ...} dicts —
    one per page that could not be fetched at all (see fetcher.FetchError).
    This is distinct from `invalid_records`, which counts records that
    fetched fine but failed normalize/validate (see schema.py).
    """
    end_time = datetime.now(timezone.utc)
    duration_seconds = round((end_time - start_time).total_seconds(), 3)

    return {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": duration_seconds,
        "pages_fetched": pages_fetched,
        "cache_hits": cache_hits,
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "failed_pages": len(failed_pages),
        "failed_page_details": failed_pages,
    }