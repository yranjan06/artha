import json
from pathlib import Path
from dataclasses import dataclass, asdict, field, fields
from datetime import datetime, timezone

MEMORY_DIR = Path("memory")
MEMORY_DIR.mkdir(exist_ok=True)


@dataclass
class Memory:
    summary:           str  = ""
    goals:             list = field(default_factory=list)
    commitments:       list = field(default_factory=list)
    observed_patterns: list = field(default_factory=list)
    user_profile:      dict = field(default_factory=dict)
    last_updated:      str  = ""


def load_memory(user_id: str) -> Memory:
    """
    Load user memory from disk.
    Filters extra/missing fields — safe across schema changes.
    Returns empty Memory if file missing or corrupted.
    """
    path = MEMORY_DIR / f"{user_id}.json"
    try:
        if not path.exists():
            return Memory()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        valid_fields = {f.name for f in fields(Memory)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return Memory(**filtered)
    except Exception as e:
        print(f"[Memory] load failed for {user_id}: {e}")
        return Memory()


def save_memory(user_id: str, memory: Memory) -> bool:
    """
    Save memory to disk.
    Returns True on success.
    """
    path = MEMORY_DIR / f"{user_id}.json"
    try:
        memory.last_updated = datetime.now(timezone.utc).isoformat()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(memory), f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Memory] save failed for {user_id}: {e}")
        return False


def build_transcript(messages: list[dict]) -> str:
    """
    Filter user + assistant messages only.
    Returns plain text transcript for LLM memory sync.
    """
    lines = []
    for msg in messages:
        role = msg.get("role")
        if role not in ("user", "assistant"):
            continue
        content = msg.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


# ── quick test ──────────────────────────────────────────
if __name__ == "__main__":
    # test load/save cycle
    mem = load_memory("test_user")
    print(f"Loaded: {mem}")

    mem.user_profile = {"name": "Ranjan", "monthly_income": 80000}
    mem.summary = "Test session"

    saved = save_memory("test_user", mem)
    print(f"Saved: {saved}")

    mem2 = load_memory("test_user")
    print(f"Reloaded: {mem2}")
    assert mem2.user_profile["name"] == "Ranjan"
    print("memory.py working correctly.")