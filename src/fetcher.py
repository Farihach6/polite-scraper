"""
fetcher.py — the polite HTTP layer.

Stage 1 responsibilities:
    - send an honest, identifying User-Agent
    - enforce a request timeout (never wait forever)
    - check the status code before returning anything
    - cache every fetched page to disk, and read from that cache on
      later calls instead of re-requesting the live site

Stage 5 responsibilities (implemented here):
    - retry once on a timeout or a 5xx server error, waiting a moment
      first
    - never retry a 404 (the page does not exist) or a 403 (the site
      said no) — asking again would either do nothing or be rude
    - raise `FetchError` (not a bare exception) on final failure, so
      the caller can catch exactly that and log-and-skip the page
      instead of crashing the whole run
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import requests

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/your-username/scraper)"
TIMEOUT_SECONDS = 10
MIN_DELAY_SECONDS = 0.5   # only applied between REAL (non-cached) requests
RETRY_DELAY_SECONDS = 2   # wait a moment before the one retry
MAX_RETRIES = 1           # one retry, only for timeouts / 5xx

NON_RETRYABLE_STATUS_CODES = {404, 403}


class FetchError(Exception):
    """
    Raised when a page could not be fetched — after the retry policy
    has already been applied. Carries enough context for the caller
    to log a clean, honest failure instead of crashing.
    """

    def __init__(self, url: str, status_code: int | None, reason: str):
        super().__init__(f"{url} -> {reason}")
        self.url = url
        self.status_code = status_code
        self.reason = reason


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
    Fetch `url`, politely, with on-disk caching and a bounded retry.

    First call for a given `filename`: sends a real HTTP GET with an
    honest User-Agent and a timeout. On success (200), saves the HTML
    to `cache_dir/filename` and prints FETCH. On a timeout or 5xx, it
    waits `RETRY_DELAY_SECONDS` and tries once more before giving up.
    A 404 or 403 fails immediately, with no retry.

    Every later call for the same `filename`: reads the saved copy
    from disk instead of hitting the network again, and prints
    CACHE HIT.

    Raises `FetchError` if the page could not be fetched after the
    retry policy has been applied — never a bare requests exception.
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

    attempt = 0
    while True:
        try:
            response = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT_SECONDS,
            )
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES:
                attempt += 1
                print(f"RETRY      {url}  (timeout, attempt {attempt + 1})")
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            raise FetchError(url, None, f"timed out after {attempt + 1} attempt(s)")
        except requests.exceptions.RequestException as exc:
            # Connection errors etc. are treated like any other
            # unretryable failure — the site isn't reachable, retrying
            # the same request immediately won't fix that.
            raise FetchError(url, None, f"request failed: {exc}")

        status = response.status_code

        if status == 200:
            html = response.text
            path.write_text(html, encoding="utf-8")
            result = FetchResult(
                url=url,
                html=html,
                status_code=status,
                from_cache=False,
                size_bytes=len(html.encode("utf-8")),
            )
            print(f"FETCH      {url}  status={status}  ({result.size_bytes} bytes)")
            # Be a polite guest: only real, live requests pay the delay.
            time.sleep(MIN_DELAY_SECONDS)
            return result

        if status in NON_RETRYABLE_STATUS_CODES:
            raise FetchError(url, status, f"HTTP {status} — not retrying")

        if 500 <= status < 600 and attempt < MAX_RETRIES:
            attempt += 1
            print(f"RETRY      {url}  (HTTP {status}, attempt {attempt + 1})")
            time.sleep(RETRY_DELAY_SECONDS)
            continue

        raise FetchError(url, status, f"unexpected HTTP {status}")