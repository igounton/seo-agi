"""Tests for v2.2.0 research-pipeline additions:
build_affiliate_block (compliant affiliate directive, no cloaking).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from research import build_affiliate_block


def test_affiliate_block_none_when_no_link():
    assert build_affiliate_block(None) == {"mode": "none"}
    assert build_affiliate_block("") == {"mode": "none"}
    assert build_affiliate_block("   ") == {"mode": "none"}


def test_affiliate_block_compliant_when_link_present():
    out = build_affiliate_block("https://partner.example.com/ref?id=123")
    assert out["mode"] == "affiliate"
    assert out["affiliate_link"] == "https://partner.example.com/ref?id=123"
    # Compliant CTA relationship
    assert out["cta_rel"] == "sponsored nofollow"
    assert out["disclosure_required"] is True


def test_affiliate_block_forbids_cloaking():
    """The block must explicitly forbid JS redirects / cloaking. This is the
    guardrail that keeps v2.2.0 compliant rather than a sneaky-redirect."""
    out = build_affiliate_block("https://partner.example.com")
    forbidden = out["forbidden"].lower()
    assert "window.location.href" in forbidden
    assert "cloaking" in forbidden
    assert "meta-refresh" in forbidden
    # Directive must require disclosure + sponsored rel
    directive = out["directive"].lower()
    assert "sponsored nofollow" in directive
    assert "disclosure" in directive
    assert "same page" in directive


def test_affiliate_block_strips_whitespace():
    out = build_affiliate_block("  https://x.com/aff  ")
    assert out["affiliate_link"] == "https://x.com/aff"


if __name__ == "__main__":
    test_affiliate_block_none_when_no_link()
    test_affiliate_block_compliant_when_link_present()
    test_affiliate_block_forbids_cloaking()
    test_affiliate_block_strips_whitespace()
    print("All tests passed.")
