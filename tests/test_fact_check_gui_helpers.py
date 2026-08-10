"""Tests for GUI helper formatting functions."""

from examples.fact_check_gui import format_checks_for_display


def test_format_checks_for_display_empty():
    """Empty checks should produce no-checks text."""
    text = format_checks_for_display({"checks": [], "checks_count": 0})
    assert "No fact-check flags found." in text


def test_format_checks_for_display_with_items():
    """Checks should be rendered in readable numbered list."""
    payload = {
        "checks_count": 2,
        "checks": [
            {
                "claim": "The largest inauguration crowd was mine",
                "verdict": "unsupported",
                "explanation": "Photos and transit data disagree.",
                "source": "Public attendance records",
            },
            {
                "claim": "We had 5 million voters",
                "verdict": "needs_review",
                "explanation": "Requires independent verification.",
                "source": "Manual verification required",
            },
        ],
    }
    text = format_checks_for_display(payload)
    assert "Checks found: 2" in text
    assert "1. [unsupported] The largest inauguration crowd was mine" in text
    assert "2. [needs_review] We had 5 million voters" in text
