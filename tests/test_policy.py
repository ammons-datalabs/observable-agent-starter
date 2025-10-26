"""Tests for the routing policy module."""

import pytest
from agents.example.policy import neutral_policy


class TestNeutralPolicy:
    """Tests for neutral_policy function."""

    # Billing-related tests
    def test_routes_invoice_to_billing(self):
        """Test that invoice-related requests route to billing."""
        assert neutral_policy("My invoice shows extra charges") == "billing"
        assert neutral_policy("I need an invoice for last month") == "billing"

    def test_routes_charge_to_billing(self):
        """Test that charge-related requests route to billing."""
        assert neutral_policy("There's an unexpected charge on my account") == "billing"
        assert neutral_policy("Why was I charged twice?") == "billing"

    def test_routes_refund_to_billing(self):
        """Test that refund requests route to billing."""
        assert neutral_policy("I need a refund") == "billing"
        assert neutral_policy("Can I get a refund for this?") == "billing"

    def test_routes_billing_keyword_to_billing(self):
        """Test that billing keyword routes to billing."""
        assert neutral_policy("billing question") == "billing"
        assert neutral_policy("Issue with my billing") == "billing"

    # Tech-related tests
    def test_routes_error_to_tech(self):
        """Test that error messages route to tech."""
        assert neutral_policy("I'm getting an error when I log in") == "tech"
        assert neutral_policy("Error 500 on the dashboard") == "tech"

    def test_routes_bug_to_tech(self):
        """Test that bug reports route to tech."""
        assert neutral_policy("I found a bug in the app") == "tech"
        assert neutral_policy("There's a bug with the search") == "tech"

    def test_routes_doesnt_work_to_tech(self):
        """Test that 'doesn't work' routes to tech."""
        assert neutral_policy("The feature doesn't work") == "tech"
        assert neutral_policy("Login doesn't work") == "tech"

    def test_routes_crash_to_tech(self):
        """Test that crash reports route to tech."""
        assert neutral_policy("The app keeps crashing") == "tech"
        assert neutral_policy("System crash on startup") == "tech"

    def test_routes_api_to_tech(self):
        """Test that API issues route to tech."""
        assert neutral_policy("The API is returning errors") == "tech"
        assert neutral_policy("API documentation question") == "tech"

    # Sales-related tests
    def test_routes_pricing_to_sales(self):
        """Test that pricing inquiries route to sales."""
        assert neutral_policy("What's your pricing?") == "sales"
        assert neutral_policy("Pricing for enterprise plan") == "sales"

    def test_routes_quote_to_sales(self):
        """Test that quote requests route to sales."""
        assert neutral_policy("I need a quote") == "sales"
        assert neutral_policy("Can you send me a quote?") == "sales"

    def test_routes_demo_to_sales(self):
        """Test that demo requests route to sales."""
        assert neutral_policy("I'd like to schedule a demo") == "sales"
        assert neutral_policy("Can I get a demo of the product?") == "sales"

    def test_routes_trial_to_sales(self):
        """Test that trial inquiries route to sales."""
        assert neutral_policy("How do I start a trial?") == "sales"
        assert neutral_policy("Extend my trial period") == "sales"

    # Default behavior
    def test_defaults_to_tech(self):
        """Test that unknown requests default to tech."""
        assert neutral_policy("random question") == "tech"
        assert neutral_policy("I have a question") == "tech"
        assert neutral_policy("help me") == "tech"

    # Edge cases
    def test_handles_empty_string(self):
        """Test that empty string defaults to tech."""
        assert neutral_policy("") == "tech"

    def test_handles_whitespace(self):
        """Test that whitespace-only string defaults to tech."""
        assert neutral_policy("   ") == "tech"
        assert neutral_policy("\n\t") == "tech"

    def test_case_insensitive(self):
        """Test that keyword matching is case insensitive."""
        assert neutral_policy("INVOICE ISSUE") == "billing"
        assert neutral_policy("Error MESSAGE") == "tech"
        assert neutral_policy("PRICING INFO") == "sales"
        assert neutral_policy("InVoIcE") == "billing"

    def test_handles_special_characters(self):
        """Test that special characters are handled."""
        assert neutral_policy("My invoice has $$$") == "billing"
        assert neutral_policy("Error: 404!!!") == "tech"
        assert neutral_policy("Pricing???") == "sales"

    def test_multiple_keywords_first_match_wins(self):
        """Test that when multiple keywords match, first category wins."""
        # "billing" keywords appear first in the function
        assert neutral_policy("invoice and pricing") == "billing"
        assert neutral_policy("refund or demo") == "billing"

        # "tech" keywords checked second
        assert neutral_policy("error and quote") == "tech"
        assert neutral_policy("bug or trial") == "tech"

    def test_partial_word_matching(self):
        """Test that keywords match as substrings."""
        assert neutral_policy("reinvoice") == "billing"  # Contains "invoice"
        assert neutral_policy("the buggy code") == "tech"  # Contains "bug"
        assert neutral_policy("repricing strategy") == "sales"  # Contains "pricing"

    def test_long_text_with_keyword(self):
        """Test that keywords are found in long text."""
        long_text = """
        Hi there, I've been using your service for a while and I'm generally happy,
        but I noticed something on my invoice that doesn't look right. Can you help?
        """
        assert neutral_policy(long_text) == "billing"

    def test_multiple_sentences(self):
        """Test handling of multi-sentence inputs."""
        text = "I love your product. However, I found a bug. Can you fix it?"
        assert neutral_policy(text) == "tech"
