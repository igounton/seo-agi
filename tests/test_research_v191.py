"""Tests for v1.9.1 research-pipeline additions:
differentiators parsing, missing_spokes extraction, link parsing in
both content parsers, generic-anchor filtering.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from research import (
    _parse_differentiators,
    _is_generic_anchor,
    _normalize_domain,
    extract_missing_spokes,
)
from lib.massive import MassiveClient
from lib.dataforseo import DataForSEOClient


# --- _parse_differentiators ---------------------------------------------------

def test_parse_differentiators_basic():
    out = _parse_differentiators("women-owned, 24/7 service, no hidden fees")
    assert out == ["women-owned", "24/7 service", "no hidden fees"]


def test_parse_differentiators_handles_whitespace_and_empty():
    assert _parse_differentiators("") == []
    assert _parse_differentiators(None) == []
    assert _parse_differentiators("  ,  ,  ") == []
    assert _parse_differentiators("  alpha  ,, beta ,  ") == ["alpha", "beta"]


# --- _normalize_domain --------------------------------------------------------

def test_normalize_domain_strips_scheme_www_path():
    assert _normalize_domain("https://www.example.com/foo/bar") == "example.com"
    assert _normalize_domain("http://example.com") == "example.com"
    assert _normalize_domain("https://sub.example.com/x") == "sub.example.com"
    assert _normalize_domain("WWW.EXAMPLE.COM/X") == "example.com"


def test_normalize_domain_relative_url_is_empty_host():
    # Relative URLs have no scheme + no host
    assert _normalize_domain("/some/path") == ""
    assert _normalize_domain("foo.html") == "foo.html"  # bare segment


# --- _is_generic_anchor -------------------------------------------------------

def test_generic_anchor_strips_obvious_nav():
    for nav in [
        "Home", "Contact Us", "Privacy Policy", "Terms",
        "Login", "Sign Up", "Read More", "Click Here",
        "Facebook", "Twitter", "LinkedIn", "FAQ",
        "Skip to content", "Next", "Back",
    ]:
        assert _is_generic_anchor(nav), f"should be generic: {nav}"


def test_generic_anchor_keeps_semantic_anchors():
    for semantic in [
        "JFK Long Term Parking",
        "Garage 1 to Terminal 4",
        "EV Charging Stations",
        "Cell Phone Lot",
        "Reserve Now for Holiday Weekend",
    ]:
        assert not _is_generic_anchor(semantic), f"should be semantic: {semantic}"


def test_generic_anchor_filters_pure_punctuation():
    assert _is_generic_anchor("→")
    assert _is_generic_anchor(">>>")
    assert _is_generic_anchor("...")
    assert _is_generic_anchor("")


def test_generic_anchor_filters_trailing_punctuation_variants():
    assert _is_generic_anchor("Contact Us!")
    assert _is_generic_anchor("Home.")
    assert _is_generic_anchor("FAQ?")


def test_generic_anchor_filters_nested_image_link_leakage():
    """Nested [![alt](img)](href) markdown sometimes leaks anchors that
    start with `!` or contain stray brackets. Those are not spokes."""
    assert _is_generic_anchor("![John F. Kennedy International Airport")
    assert _is_generic_anchor("![alt text")
    assert _is_generic_anchor("Foo [stray bracket")
    assert _is_generic_anchor("trailing bracket]")


# --- extract_missing_spokes ---------------------------------------------------

def test_missing_spokes_keeps_only_same_domain_semantic():
    organic = [
        {"url": "https://spothero.com/airport/jfk"},
        {"url": "https://example.com/page"},
    ]
    content_data = [
        {  # competitor 1
            "links": [
                {"text": "JFK Long Term Parking", "url": "https://spothero.com/airport/jfk-lt"},
                {"text": "Newark Parking", "url": "https://spothero.com/airport/ewr"},
                {"text": "Contact Us", "url": "https://spothero.com/contact"},  # generic
                {"text": "Privacy Policy", "url": "https://spothero.com/privacy"},  # generic
                {"text": "External Partner Site", "url": "https://other.com/partner"},  # external
                {"text": "Cell Phone Lot Guide", "url": "/airport/jfk-cell-phone"},  # relative -> internal
            ]
        },
        {  # competitor 2
            "links": [
                {"text": "JFK Long Term Parking", "url": "https://example.com/jfk-long-term"},
            ]
        },
    ]
    spokes = extract_missing_spokes(content_data, organic, top_n_competitors=3, top_k=10)
    anchors = [s["anchor"] for s in spokes]
    counts = {s["anchor"]: s["competitor_count"] for s in spokes}

    # Top spoke: appears in both competitors -> count 2
    assert spokes[0]["anchor"] == "JFK Long Term Parking"
    assert counts["JFK Long Term Parking"] == 2
    # Internal-relative URL counted
    assert "Cell Phone Lot Guide" in anchors
    # Generic nav and external links dropped
    assert "Contact Us" not in anchors
    assert "Privacy Policy" not in anchors
    assert "External Partner Site" not in anchors


def test_missing_spokes_respects_top_n_competitors():
    organic = [{"url": f"https://site{i}.com/"} for i in range(5)]
    content_data = [
        {"links": [{"text": "Visible Anchor", "url": "https://site0.com/x"}]},
        {"links": [{"text": "Visible Anchor", "url": "https://site1.com/x"}]},
        {"links": [{"text": "Visible Anchor", "url": "https://site2.com/x"}]},
        {"links": [{"text": "Hidden Anchor", "url": "https://site3.com/x"}]},
        {"links": [{"text": "Hidden Anchor", "url": "https://site4.com/x"}]},
    ]
    spokes = extract_missing_spokes(content_data, organic, top_n_competitors=3, top_k=10)
    anchors = [s["anchor"] for s in spokes]
    assert "Visible Anchor" in anchors
    assert "Hidden Anchor" not in anchors


def test_missing_spokes_empty_inputs():
    assert extract_missing_spokes([], [], 3, 10) == []
    assert extract_missing_spokes(None, None, 3, 10) == []
    assert extract_missing_spokes([None, None], [{"url": ""}, {"url": ""}], 3, 10) == []


# --- MassiveClient link extraction --------------------------------------------

def test_massive_parses_markdown_links():
    md = """# Title

See our [Long Term Parking](https://spothero.com/long-term) page
or read about [Cell Phone Lots](https://spothero.com/cell-phone).

Skip image: ![alt text](https://spothero.com/image.jpg)
Skip hash: [back to top](#top)
"""
    out = MassiveClient._parse_markdown(md)
    link_texts = [l["text"] for l in out["links"]]
    assert "Long Term Parking" in link_texts
    assert "Cell Phone Lots" in link_texts
    # Image links and hash anchors must be filtered
    assert "alt text" not in link_texts
    assert "back to top" not in link_texts


def test_massive_links_empty_when_no_links():
    out = MassiveClient._parse_markdown("# Just a heading\n\nNo links here.")
    assert out["links"] == []


# --- DataForSEOClient link extraction -----------------------------------------

def test_dataforseo_extracts_links_from_topic_tree():
    page_content = {
        "main_topic": [
            {
                "primary_content": [
                    {
                        "text": "See our parking options",
                        "urls": [
                            {"url": "/parking", "anchor_text": "parking options"},
                            {"url": "/rates", "anchor_text": "rates"},
                        ],
                    }
                ]
            }
        ],
        "secondary_topic": [
            {
                "primary_content": [
                    {
                        "urls": [
                            {"url": "/faq", "anchor_text": "FAQ"},
                        ]
                    }
                ]
            }
        ],
    }
    links = DataForSEOClient._extract_links(page_content)
    texts = [l["text"] for l in links]
    assert "parking options" in texts
    assert "rates" in texts
    assert "FAQ" in texts


def test_dataforseo_extract_links_empty():
    assert DataForSEOClient._extract_links({}) == []
    assert DataForSEOClient._extract_links({"main_topic": None}) == []


if __name__ == "__main__":
    test_parse_differentiators_basic()
    test_parse_differentiators_handles_whitespace_and_empty()
    test_normalize_domain_strips_scheme_www_path()
    test_normalize_domain_relative_url_is_empty_host()
    test_generic_anchor_strips_obvious_nav()
    test_generic_anchor_keeps_semantic_anchors()
    test_generic_anchor_filters_pure_punctuation()
    test_generic_anchor_filters_trailing_punctuation_variants()
    test_generic_anchor_filters_nested_image_link_leakage()
    test_missing_spokes_keeps_only_same_domain_semantic()
    test_missing_spokes_respects_top_n_competitors()
    test_missing_spokes_empty_inputs()
    test_massive_parses_markdown_links()
    test_massive_links_empty_when_no_links()
    test_dataforseo_extracts_links_from_topic_tree()
    test_dataforseo_extract_links_empty()
    print("All tests passed.")
