"""
Network-free smoke test for fetcher.py.

This sandbox's outbound network only allows a fixed set of domains
(pypi, github, etc.) — books.toscrape.com is not reachable from here,
so live requests return a 403 from the *sandbox's* proxy, not the
real site. This test mocks `requests.get` to prove the fetch/cache
logic itself (User-Agent, timeout, status check, caching, CACHE HIT
on the second call) is correct. On a machine with normal internet
access, `python src/main.py` run twice will show the same behavior
against the real site.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fetcher import USER_AGENT, polite_get  # noqa: E402


def test_fetch_then_cache_hit():
    fake_html = "<html><body>Fake catalogue page</body></html>"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = fake_html

    with tempfile.TemporaryDirectory() as tmp:
        cache_dir = Path(tmp)

        with patch("fetcher.requests.get", return_value=mock_response) as mock_get, \
             patch("fetcher.time.sleep"):  # skip the real 0.5s delay in tests
            # First call: should hit the network and write the cache file.
            first = polite_get("https://example.test/page-1.html", cache_dir, "page-1.html")
            assert first.from_cache is False
            assert first.status_code == 200
            assert first.html == fake_html
            mock_get.assert_called_once()
            called_headers = mock_get.call_args.kwargs["headers"]
            assert called_headers["User-Agent"] == USER_AGENT
            assert mock_get.call_args.kwargs["timeout"] == 10

            cached_file = cache_dir / "page-1.html"
            assert cached_file.exists()
            assert cached_file.read_text(encoding="utf-8") == fake_html

            # Second call: should read from cache and NOT call requests.get again.
            second = polite_get("https://example.test/page-1.html", cache_dir, "page-1.html")
            assert second.from_cache is True
            assert second.html == fake_html
            mock_get.assert_called_once()  # still only called once total

    print("test_fetch_then_cache_hit: PASSED")


if __name__ == "__main__":
    test_fetch_then_cache_hit()
