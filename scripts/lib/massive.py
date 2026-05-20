"""
Massive Web Render API client for seo-agi.

Massive (render.joinmassive.com) is used for COMPETITOR CONTENT PARSING --
fetching a URL and getting back clean rendered markdown that includes
JS-loaded content, which DataForSEO's content_parsing/live endpoint misses.

Scope intentionally narrow:
- Massive /browser endpoint: URL -> markdown (used here)
- Massive /search endpoint: NOT used. As of v1.9.0 it returns only
  'also-searched' query suggestions, not organic SERP results. SERP
  data continues to come from DataForSEO.

The client outputs the same shape as DataForSEOClient._extract_content
(`title`, `word_count`, `headings`, `plain_text_size`) so it is a
drop-in replacement for the content_parse() step in research.py.
"""

import json
import re
import urllib.parse
import urllib.request
import urllib.error
from typing import Optional


class MassiveClient:
    """Client for Massive Web Render API (render.joinmassive.com)."""

    BASE_URL = "https://render.joinmassive.com"

    def __init__(self, api_token: str, default_country: str = "US"):
        self.api_token = api_token
        self.default_country = default_country

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_token}"}

    def _get(self, path: str, params: dict, timeout: int = 60) -> str:
        """Make a GET request and return the raw response body as text."""
        qs = urllib.parse.urlencode(params)
        url = f"{self.BASE_URL}{path}?{qs}"
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore") if e.fp else ""
            raise RuntimeError(
                f"Massive API error {e.code}: {body[:300]}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Massive connection error: {e.reason}") from e

    def content_parse(
        self, url: str, country: Optional[str] = None
    ) -> Optional[dict]:
        """Fetch a URL via Massive's renderer and extract content structure.

        Returns the same shape as DataForSEOClient.content_parse():
            { "title": str, "word_count": int, "headings": [str],
              "plain_text_size": int }
        where each heading is formatted as "H{level}: {text}".

        Returns None if the fetch returns empty content.
        """
        try:
            markdown = self._get(
                "/browser",
                {
                    "url": url,
                    "format": "markdown",
                    "country": country or self.default_country,
                },
            )
        except RuntimeError:
            return None

        if not markdown or not markdown.strip():
            return None

        return self._parse_markdown(markdown)

    @staticmethod
    def _parse_markdown(md: str) -> dict:
        """Parse rendered markdown into the seo-agi content shape.

        Headings: lines starting with `#`, `##`, ..., `######` -> H1..H6.
        Title: first H1 found, otherwise empty.
        Word count: rough split of body text after stripping markdown
        syntax (consistent with how dataforseo.py counts).
        """
        headings: list[str] = []
        title = ""
        for line in md.splitlines():
            m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
            if not m:
                continue
            level = len(m.group(1))
            text = m.group(2).strip()
            if not text:
                continue
            if level == 1 and not title:
                title = text
            headings.append(f"H{level}: {text}")

        # Word count: strip markdown punctuation, split on whitespace.
        text = re.sub(r"[`*_#>\[\]()!|-]+", " ", md)
        word_count = len([w for w in text.split() if w.strip()])

        return {
            "title": title,
            "word_count": word_count,
            "headings": headings,
            "plain_text_size": len(md),
        }
