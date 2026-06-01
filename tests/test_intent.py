"""
Intent classifier tests.
These only exercise tier-0 (greeting) and tier-1 (regex) — no LLM calls needed.
"""
import pytest
from dotenv import load_dotenv
load_dotenv()

from intent import classify


def test_greeting_shield():
    """Tier 0: standard greetings must never route to finance."""
    for word in ["hello", "hi", "namaste", "pranam", "hey", "good morning"]:
        assert classify(word) == "general", f"Greeting '{word}' should be general"


def test_hindi_finance_keywords():
    """Tier 1: Hindi finance keywords must match without LLM."""
    cases = [
        "mera balance check karo",
        "kitna kharch hua is mahine",
        "paise kahan gaye",
        "savings kitni hain",
        "EMI set karo",
        "budget kitna bacha hai",
    ]
    for text in cases:
        assert classify(text) == "finance", f"'{text}' should be finance"


def test_english_finance_keywords():
    """Tier 1: English finance keywords must match without LLM."""
    cases = [
        "check my monthly expenses",
        "log 500 rupees for groceries",
        "can I afford this phone",
        "set a reminder for rent payment",
        "what is my income this month",
    ]
    for text in cases:
        assert classify(text) == "finance", f"'{text}' should be finance"


def test_general_non_finance():
    """Non-finance queries must not route to the agent."""
    cases = [
        "what is the capital of india",
        "how are you doing",
        "tell me a joke",
        "what time is it in new york",
    ]
    for text in cases:
        assert classify(text) == "general", f"'{text}' should be general"


def test_empty_and_whitespace():
    """Empty input must be safe."""
    assert classify("") == "general"
    assert classify("   ") == "general"


def test_always_returns_valid_label():
    """classify() must always return 'finance' or 'general' — never raises."""
    inputs = [
        "mujhe MacBook kharidna hai",
        "SIP 2000 per month start karna chahta hun",
        "kuch bhi",
        "123",
        "!@#$",
    ]
    for text in inputs:
        result = classify(text)
        assert result in ("finance", "general"), (
            f"Invalid label '{result}' for input: '{text}'"
        )