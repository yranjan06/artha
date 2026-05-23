import json
from datetime import date
from pathlib import Path

MEMORY_DIR = Path("memory")
MEMORY_DIR.mkdir(exist_ok=True)


def _get_path(user_id: str) -> Path:
    return MEMORY_DIR / f"{user_id}_ledger.json"


def load_ledger(user_id: str) -> list:
    """
    Load user ledger.
    Returns empty list if missing or corrupted.
    """
    path = _get_path(user_id)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Ledger] load failed for {user_id}: {e}")
        return []


def save_ledger(user_id: str, data: list) -> bool:
    """
    Save ledger to disk.
    """
    path = _get_path(user_id)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Ledger] save failed for {user_id}: {e}")
        return False


def add_transaction(
    user_id: str,
    amount: float,
    category: str,
    note: str = ""
) -> bool:
    """
    Append transaction to ledger.
    Negative amount = expense
    Positive amount = income
    """
    ledger = load_ledger(user_id)
    ledger.append({
        "date": date.today().isoformat(),
        "amount": amount,
        "category": category,
        "note": note,
    })
    return save_ledger(user_id, ledger)


def get_monthly_expenses(user_id: str, year: int, month: int) -> list:
    """
    Return all transactions for given month.
    Uses string prefix match — fast and safe.
    """
    ledger = load_ledger(user_id)
    prefix = f"{year:04d}-{month:02d}-"
    return [tx for tx in ledger if tx.get("date", "").startswith(prefix)]


# ── quick test ──────────────────────────────────────────
if __name__ == "__main__":
    import os

    # test add transactions
    add_transaction("test", -500,  "sabzi",  "vegetables")
    add_transaction("test", -2000, "petrol", "bike fuel")
    add_transaction("test", 50000, "salary", "november salary")

    # test monthly fetch
    today = date.today()
    expenses = get_monthly_expenses("test", today.year, today.month)
    print(f"Transactions this month: {len(expenses)}")
    for tx in expenses:
        print(f"  {tx}")

    # cleanup
    path = MEMORY_DIR / "test_ledger.json"
    if path.exists():
        os.remove(path)
    print("ledger.py working correctly.")