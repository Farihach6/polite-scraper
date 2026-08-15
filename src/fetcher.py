"""
fetcher.py — the polite HTTP layer.

Stage 1 responsibilities (implemented here):
    - send an honest, identifying User-Agent
    - enforce a request timeout (never wait forever)
    - check the status code before returning anything
    - cache every fetched page to disk, and read from that cache on
      later calls instead of re-requesting the live site

Stage 5 will extend `polite_get` with retry-on-5xx/timeout and a
`FetchResult.failed` path so one broken page can't kill a run. That
logic is stubbed here (see `retries` param) but not yet exercised.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import requests

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/your-username/scraper)"
TIMEOUT_SECONDS = 10
MIN_DELAY_SECONDS = 0.5  # only applied between REAL (non-cached) requests


@dataclass
class FetchResult:
    url: str
    html: str
    status_code: int
    from_cache: bool
    size_bytes: int


def _cache_path(cache_dir: Path, filename: str) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / filename


def polite_get(url: str, cache_dir: Path, filename: str) -> FetchResult:
    """
    Fetch `url`, politely, with on-disk caching.

    First call for a given `filename`: sends a real HTTP GET with an
    honest User-Agent and a timeout, checks the status code, saves the
    HTML to `cache_dir/filename`, and prints FETCH.

    Every later call for the same `filename`: reads the saved copy
    from disk instead of hitting the network again, and prints
    CACHE HIT.

    Raises `requests.HTTPError` if the live request does not return
    200 — a non-200 response is a failed fetch, not HTML to parse.
    """
    path = _cache_path(cache_dir, filename)

    if path.exists():
        html = path.read_text(encoding="utf-8")
        result = FetchResult(
            url=url,
            html=html,
            status_code=200,
            from_cache=True,
            size_bytes=len(html.encode("utf-8")),
        )
        print(f"CACHE HIT  {url}  ({result.size_bytes} bytes)")
        return result

    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT_SECONDS,
    )

    if response.status_code != 200:
        response.raise_for_status()

    html = response.text
    path.write_text(html, encoding="utf-8")

    result = FetchResult(
        url=url,
        html=html,
        status_code=response.status_code,
        from_cache=False,
        size_bytes=len(html.encode("utf-8")),
    )
    print(f"FETCH      {url}  status={result.status_code}  ({result.size_bytes} bytes)")

    # Be a polite guest: only real, live requests pay the delay.
    time.sleep(MIN_DELAY_SECONDS)

    return result
