import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date
from ledger import add_transaction, get_monthly_expenses


def parse_income(value) -> float:
    """
    Convert income strings to float.
    Handles: "80000", "80k", "80,000", "80 hazaar", "2 lakh", "1 crore"
    """
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return 0.0

    cleaned = value.lower().replace(",", "").strip()
    multiplier = 1

    if "crore" in cleaned:
        multiplier = 10_000_000
        cleaned = cleaned.replace("crore", "")
    elif "lakh" in cleaned or "lac" in cleaned:
        multiplier = 100_000
        cleaned = cleaned.replace("lakh", "").replace("lac", "")
    elif "hazaar" in cleaned or "hazar" in cleaned:
        multiplier = 1_000
        cleaned = cleaned.replace("hazaar", "").replace("hazar", "")
    elif "k" in cleaned:
        multiplier = 1_000
        cleaned = cleaned.replace("k", "")

    try:
        return float(cleaned.strip()) * multiplier
    except ValueError:
        return 0.0


def log_expense(user_id, amount, category, note=""):
    """
    Record expense in ledger.
    Always stores as negative amount.
    """
    add_transaction(user_id, -abs(amount), category, note)
    return {
        "status": "ok",
        "message": f"{abs(amount)} logged under {category}",
    }


def get_monthly_summary(user_id, year, month):
    """
    Monthly finance summary — math in code, not LLM.
    """
    txs = get_monthly_expenses(user_id, year, month)
    total_income  = 0
    total_expense = 0
    by_category   = {}

    for tx in txs:
        amount   = tx["amount"]
        category = tx["category"]
        if amount > 0:
            total_income += amount
        else:
            total_expense += abs(amount)
        by_category[category] = by_category.get(category, 0) + abs(amount)

    return {
        "total_income":  total_income,
        "total_expense": total_expense,
        "balance":       total_income - total_expense,
        "by_category":   by_category,
    }


def check_budget(user_id, amount, memory):
    """
    Check if user can afford a purchase this month.
    Returns explicit error if income is not set — never silently returns 'can't afford'.
    """
    monthly_income_raw = memory.user_profile.get("monthly_income")

    if not monthly_income_raw:
        return {
            "error":   "income_not_set",
            "message": "Pehle apni monthly income batao — tab budget check kar sakte hain.",
        }

    income = parse_income(monthly_income_raw)
    if income <= 0:
        return {
            "error":   "income_invalid",
            "message": "Monthly income valid number mein batao (e.g. 50000 or 50k).",
        }

    today    = date.today()
    expenses = get_monthly_expenses(user_id, today.year, today.month)

    total_expense = sum(
        abs(tx["amount"]) for tx in expenses if tx["amount"] < 0
    )
    remaining = max(income - total_expense, 0)

    return {
        "can_afford": remaining >= amount,
        "remaining":  remaining,
        "requested":  amount,
        "income":     income,
        "spent_so_far": total_expense,
    }


def set_reminder(memory, title, due_date):
    """
    Append reminder to memory commitments.
    Returns updated memory.
    """
    memory.commitments.append({
        "title":    title,
        "due_date": due_date,
        "status":   "pending",
    })
    return memory


def make_plan(income, expenses_list):
    """
    Simple savings estimate from income and expense list.
    """
    income        = parse_income(income)
    total_expense = sum(
        abs(tx["amount"]) for tx in expenses_list if tx["amount"] < 0
    )
    possible_savings = max(income - total_expense, 0)
    savings_rate     = round((possible_savings / income) * 100, 1) if income > 0 else 0

    return {
        "income":            income,
        "expenses":          total_expense,
        "possible_savings":  possible_savings,
        "savings_rate":      savings_rate,
    }


# ── quick test ──────────────────────────────────────────
if __name__ == "__main__":
    assert parse_income("80k")       == 80000.0
    assert parse_income("80,000")    == 80000.0
    assert parse_income("80 hazaar") == 80000.0
    assert parse_income("2 lakh")    == 200000.0
    assert parse_income(80000)       == 80000.0
    print("parse_income: all pass")

    plan = make_plan("80k", [
        {"amount": -5000, "category": "sabzi"},
        {"amount": -2000, "category": "petrol"},
    ])
    assert plan["possible_savings"] == 73000.0
    print("make_plan: pass")
    print("tools/finance.py working correctly.")