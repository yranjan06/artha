"""
Memory persistence tests.
Uses a temp user ID — cleaned up after each test.
No mocking needed: tests actual file I/O.
"""
import os
import pytest
from pathlib import Path

from memory import Memory, save_memory, load_memory, build_transcript

_TEST_USER = "_pytest_artha_memory_"


@pytest.fixture(autouse=True)
def cleanup():
    """Delete the test memory file before and after each test."""
    path = Path("memory") / f"{_TEST_USER}.json"
    if path.exists():
        os.remove(path)
    yield
    if path.exists():
        os.remove(path)


def test_save_and_load_roundtrip():
    m = Memory()
    m.user_profile = {"name": "Rahul", "monthly_income": "80000"}
    m.summary      = "Test session summary"
    save_memory(_TEST_USER, m)

    loaded = load_memory(_TEST_USER)
    assert loaded.user_profile["name"]           == "Rahul"
    assert loaded.user_profile["monthly_income"] == "80000"
    assert loaded.summary == "Test session summary"


def test_load_nonexistent_returns_empty_memory():
    loaded = load_memory("__does_not_exist_xyz__")
    assert isinstance(loaded, Memory)
    assert loaded.user_profile == {}
    assert loaded.goals        == []
    assert loaded.commitments  == []


def test_update_and_reload():
    m = Memory()
    m.user_profile = {"name": "Priya"}
    save_memory(_TEST_USER, m)

    loaded = load_memory(_TEST_USER)
    loaded.user_profile["monthly_income"] = "60000"
    loaded.goals.append({"description": "Save 10k/month", "status": "active"})
    save_memory(_TEST_USER, loaded)

    final = load_memory(_TEST_USER)
    assert final.user_profile["monthly_income"] == "60000"
    assert len(final.goals) == 1
    assert final.goals[0]["description"] == "Save 10k/month"


def test_last_updated_is_set_on_save():
    m = Memory()
    save_memory(_TEST_USER, m)
    loaded = load_memory(_TEST_USER)
    assert loaded.last_updated != ""


def test_build_transcript_only_user_and_assistant():
    messages = [
        {"role": "system",    "content": "You are Artha"},
        {"role": "user",      "content": "mera balance kya hai"},
        {"role": "assistant", "content": "Aapka balance 45000 hai"},
        {"role": "tool",      "content": '{"result": 45000}'},
    ]
    tx = build_transcript(messages)
    assert "mera balance kya hai"     in tx
    assert "Aapka balance 45000 hai"  in tx
    assert "system"                  not in tx
    assert "tool"                    not in tx


def test_build_transcript_empty_messages():
    assert build_transcript([]) == ""


def test_build_transcript_skips_empty_content():
    messages = [
        {"role": "user",      "content": ""},
        {"role": "assistant", "content": "Namaste!"},
    ]
    tx = build_transcript(messages)
    assert "Namaste!" in tx
    # empty user content should not add a blank line
    assert tx.strip() == "assistant: Namaste!"