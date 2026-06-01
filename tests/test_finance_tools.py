"""
Finance tool tests — no file I/O, no API calls.
All ledger operations are mocked.
"""
import pytest
from unittest.mock import patch
from datetime import date

from tools.finance import parse_income, check_budget, make_plan, get_monthly_summary
from memory import Memory


# ── parse_income ────────────────────────────────────────────
class TestParseIncome:
    def test_plain_int(self):
        assert parse_income(50000) == 50000.0

    def test_plain_string(self):
        assert parse_income("50000") == 50000.0

    def test_k_notation(self):
        assert parse_income("80k") == 80000.0
        assert parse_income("50K") == 50000.0

    def test_lakh_notation(self):
        assert parse_income("2 lakh") == 200000.0
        assert parse_income("1.5 lakh") == 150000.0

    def test_hazaar_notation(self):
        assert parse_income("80 hazaar") == 80000.0

    def test_comma_separators(self):
        assert parse_income("80,000") == 80000.0
        assert parse_income("1,00,000") == 100000.0

    def test_invalid_returns_zero(self):
        assert parse_income("abc") == 0.0

    def test_none_returns_zero(self):
        assert parse_income(None) == 0.0


# ── check_budget ────────────────────────────────────────────
class TestCheckBudget:

    def _mem(self, income=None):
        m = Memory()
        if income:
            m.user_profile = {"monthly_income": str(income)}
        return m

    @patch("tools.finance.get_monthly_expenses")
    def test_can_afford(self, mock_exp):
        mock_exp.return_value = [
            {"amount": -5000, "category": "food", "date": "2025-05-01"},
        ]
        result = check_budget("u1", 10000, self._mem(50000))
        assert result["can_afford"] is True
        assert result["remaining"] == 45000.0

    @patch("tools.finance.get_monthly_expenses")
    def test_cannot_afford(self, mock_exp):
        mock_exp.return_value = [
            {"amount": -48000, "category": "rent", "date": "2025-05-01"},
        ]
        result = check_budget("u1", 5000, self._mem(50000))
        assert result["can_afford"] is False

    def test_income_not_set_returns_error(self):
        result = check_budget("u1", 5000, self._mem())
        assert "error" in result
        assert result["error"] == "income_not_set"

    def test_income_zero_returns_error(self):
        m = Memory()
        m.user_profile = {"monthly_income": "0"}
        result = check_budget("u1", 1000, m)
        assert "error" in result

    @patch("tools.finance.get_monthly_expenses")
    def test_exact_remaining_match(self, mock_exp):
        mock_exp.return_value = []
        result = check_budget("u1", 50000, self._mem(50000))
        assert result["can_afford"] is True
        assert result["remaining"] == 50000.0


# ── make_plan ───────────────────────────────────────────────
class TestMakePlan:

    def test_basic_calculation(self):
        expenses = [
            {"amount": -5000, "category": "food"},
            {"amount": -2000, "category": "petrol"},
        ]
        result = make_plan("80k", expenses)
        assert result["income"] == 80000.0
        assert result["expenses"] == 7000.0
        assert result["possible_savings"] == 73000.0
        assert result["savings_rate"] == round(73000/80000*100, 1)

    def test_zero_income_safe(self):
        result = make_plan(0, [])
        assert result["savings_rate"] == 0
        assert result["possible_savings"] == 0

    def test_overspend_clamps_to_zero(self):
        expenses = [{"amount": -90000, "category": "rent"}]
        result = make_plan("80k", expenses)
        assert result["possible_savings"] == 0


# ── get_monthly_summary ─────────────────────────────────────
class TestGetMonthlySummary:

    @patch("tools.finance.get_monthly_expenses")
    def test_summary_calculation(self, mock_exp):
        mock_exp.return_value = [
            {"amount": -5000,  "category": "food"},
            {"amount": -2000,  "category": "petrol"},
            {"amount":  50000, "category": "salary"},
        ]
        result = get_monthly_summary("u1", 2025, 5)
        assert result["total_income"]  == 50000
        assert result["total_expense"] == 7000
        assert result["balance"]       == 43000
        assert result["by_category"]["food"] == 5000

    @patch("tools.finance.get_monthly_expenses")
    def test_empty_month(self, mock_exp):
        mock_exp.return_value = []
        result = get_monthly_summary("u1", 2025, 5)
        assert result["total_income"]  == 0
        assert result["total_expense"] == 0
        assert result["balance"]       == 0