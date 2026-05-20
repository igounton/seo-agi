"""Tests for the Massive Web Render client (v1.9.0)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.massive import MassiveClient


# --- markdown parser ----------------------------------------------------------

def test_parse_markdown_extracts_headings_with_levels():
    md = """# Page Title

Some intro paragraph.

## First Section

Content one.

### Subsection A

More content.

## Second Section

Content two.
"""
    out = MassiveClient._parse_markdown(md)
    assert out["title"] == "Page Title"
    assert "H1: Page Title" in out["headings"]
    assert "H2: First Section" in out["headings"]
    assert "H3: Subsection A" in out["headings"]
    assert "H2: Second Section" in out["headings"]
    # Word count is rough but should be in a reasonable range
    assert 10 <= out["word_count"] <= 30
    assert out["plain_text_size"] == len(md)


def test_parse_markdown_no_h1_leaves_title_empty():
    md = "## Only H2 here\n\nSome text body content."
    out = MassiveClient._parse_markdown(md)
    assert out["title"] == ""
    assert "H2: Only H2 here" in out["headings"]


def test_parse_markdown_empty():
    out = MassiveClient._parse_markdown("")
    assert out["title"] == ""
    assert out["headings"] == []
    assert out["word_count"] == 0
    assert out["plain_text_size"] == 0


def test_parse_markdown_ignores_hash_in_body():
    """A `#` mid-line is not a heading -- only line-start `#` counts."""
    md = "Some text with # symbol in body\n\n## Real Heading\n"
    out = MassiveClient._parse_markdown(md)
    assert "H2: Real Heading" in out["headings"]
    # The body `#` should not become an H1
    assert out["title"] == ""
    assert len(out["headings"]) == 1


def test_parse_markdown_all_six_levels():
    md = """# H1
## H2
### H3
#### H4
##### H5
###### H6
"""
    out = MassiveClient._parse_markdown(md)
    for level in range(1, 7):
        assert f"H{level}: H{level}" in out["headings"]
    assert out["title"] == "H1"


# --- contract with DataForSEOClient ------------------------------------------

def test_output_shape_matches_dataforseo():
    """MassiveClient.content_parse() must return the same keys as
    DataForSEOClient._extract_content() so it's a drop-in replacement
    in research.py."""
    out = MassiveClient._parse_markdown("# Title\n## Section\nbody words here")
    required_keys = {"title", "word_count", "headings", "plain_text_size"}
    assert required_keys.issubset(out.keys())
    assert isinstance(out["title"], str)
    assert isinstance(out["word_count"], int)
    assert isinstance(out["headings"], list)
    assert isinstance(out["plain_text_size"], int)


# --- client init --------------------------------------------------------------

def test_client_constructs_with_token():
    c = MassiveClient("test-token")
    assert c.api_token == "test-token"
    assert c.default_country == "US"
    assert c._headers()["Authorization"] == "Bearer test-token"


def test_client_custom_country():
    c = MassiveClient("test-token", default_country="GB")
    assert c.default_country == "GB"


if __name__ == "__main__":
    test_parse_markdown_extracts_headings_with_levels()
    test_parse_markdown_no_h1_leaves_title_empty()
    test_parse_markdown_empty()
    test_parse_markdown_ignores_hash_in_body()
    test_parse_markdown_all_six_levels()
    test_output_shape_matches_dataforseo()
    test_client_constructs_with_token()
    test_client_custom_country()
    print("All tests passed.")
