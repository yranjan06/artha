import re
from llm import call_llm_simple

FINANCE_PATTERN = re.compile(
    r"(balance|transaction|bill|sav|spend|incom|"
    r"goal|remind|invest|salary|"
    r"kharch|pais|bacha|emi|budget|mutual|fund)",
    re.IGNORECASE
)

GREETING_PATTERN = re.compile(
    r"^(hi|hello|hey|namaste|pranam|good\s+morning|good\s+evening|yo)$",
    re.IGNORECASE
)


def classify(text: str) -> str:
    """
    Classify user intent.

    Tier 0: empty / greeting  → general
    Tier 1: regex keywords    → finance
    Tier 2: LLM fallback      → finance or general

    Returns:
        "finance" or "general"
    """
    if not text or not text.strip():
        return "general"

    cleaned = text.strip()

    # tier 0 — greeting shield
    if GREETING_PATTERN.match(cleaned):
        return "general"

    # tier 1 — regex
    if FINANCE_PATTERN.search(cleaned):
        return "finance"

    # tier 2 — LLM fallback
    prompt = [
        {
            "role": "system",
            "content": (
                "Classify the user message as finance or general.\n"
                "finance: money, goals, income, expenses, savings, bills\n"
                "general: everything else\n"
                "Reply with exactly one word: finance or general."
            )
        },
        {
            "role": "user",
            "content": cleaned
        }
    ]

    try:
        result = call_llm_simple(prompt).strip().lower()
        if "finance" in result:
            return "finance"
    except Exception as e:
        print(f"[Intent] LLM fallback failed: {e}")

    return "general"


# ── quick test ──────────────────────────────────────────
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    tests = [
        ("mera paisa kahan gaya",        "finance"),
        ("spending kitna hua",            "finance"),
        ("balance check karo",            "finance"),
        ("hello",                         "general"),
        ("namaste",                       "general"),
        ("what is the capital of india",  "general"),
        ("mujhe ek MacBook kharidna hai", "finance"),
    ]

    print("Running intent tests...\n")
    for text, expected in tests:
        result = classify(text)
        status = "PASS" if result == expected else "FAIL"
        print(f"{status} | '{text}' → {result} (expected: {expected})")