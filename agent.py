# agent.py
import re
import json
from config import client
from memory import load_memory, save_memory, build_transcript, Memory
from tools.finance import log_expense, get_monthly_summary, check_budget, set_reminder, make_plan
from tools.search import search
from intent import classify
from llm import call_llm_with_tools, call_llm_simple
from datetime import date

MAX_ITER = 5

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "update_profile",
            "description": "Update user profile information — name, monthly_income, or primary_goal. Call this when user tells you their income, name, or financial goal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "monthly_income": {"type": "string", "description": "Monthly income e.g. 19000, 80k, 2 lakh"},
                    "name":           {"type": "string", "description": "User name"},
                    "primary_goal":   {"type": "string", "description": "Primary financial goal"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_expense",
            "description": "Record an expense in the ledger. Call this when user says they spent money on something.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount":   {"type": "number", "description": "Expense amount (positive number)"},
                    "category": {"type": "string", "description": "Category e.g. food, petrol, rent"},
                    "note":     {"type": "string", "description": "Optional note"},
                },
                "required": ["amount", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_monthly_summary",
            "description": "Get income, expense, balance summary for a month. Call this when user asks how much they spent or their monthly summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year":  {"type": "integer", "description": "Year e.g. 2026"},
                    "month": {"type": "integer", "description": "Month 1-12"},
                },
                "required": ["year", "month"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_budget",
            "description": "Check if user can afford to spend or save a specific amount this month. Call this when user asks if they can buy something, afford something, or save a target amount.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Amount as a plain number e.g. 100000 not '1 lakh'. Always convert to integer before passing."},
                },
                "required": ["amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Save a reminder or commitment for the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title":    {"type": "string", "description": "Reminder title"},
                    "due_date": {"type": "string", "description": "Due date YYYY-MM-DD"},
                },
                "required": ["title", "due_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "make_plan",
            "description": "Create a savings plan based on income and current month expenses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "income": {"type": "number", "description": "Monthly income amount"},
                },
                "required": ["income"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search for financial news or information online.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
        },
    },
]


def build_system_prompt(memory):
    today = date.today().isoformat()
    prompt = f"""You are Artha — a personal voice finance agent.
Today: {today}

User profile: {memory.user_profile}
Summary: {memory.summary}
Goals: {memory.goals}
Commitments: {memory.commitments}
Patterns: {memory.observed_patterns}

Rules:
- Use tools when needed — never invent numbers
- When user mentions their income or name, call update_profile immediately
- Never assume or invent user's name — if unknown, do not use any name
- Math happens in tools, judgment happens here
- Respond in Hinglish — casual mix of Hindi and English
- Keep responses short — 2-3 lines max
- Never use formal words like "vaayan vyaktigat vaanijya sahayak"
- Always convert amounts to plain numbers before tool calls — "1 lakh" = 100000, "50k" = 50000
- amount parameters must always be numbers, never strings
- Never write <function=...> tags — always use proper tool call format
- Reference commitments and goals when relevant
- Numbers above are context only — fetch fresh via tools for calculations
"""
    return prompt


def execute_tool(name, args, memory, user_id):
    print(f"\n[TOOL] {name}({args})")
    try:
        if name == "update_profile":
            memory.user_profile.update(args)
            save_memory(user_id, memory)
            return {"status": "updated", "profile": memory.user_profile}

        if name == "log_expense":
            return log_expense(user_id, **args)

        if name == "get_monthly_summary":
            return get_monthly_summary(user_id, **args)

        if name == "check_budget":
            try:
                amount = float(args["amount"])
            except (TypeError, ValueError):
                amount = 0.0
            return check_budget(user_id, amount, memory)

        if name == "set_reminder":
            updated = set_reminder(memory, args["title"], args["due_date"])
            save_memory(user_id, updated)
            return {"status": "saved", "title": args["title"]}

        if name == "make_plan":
            from ledger import get_monthly_expenses
            today = date.today()
            expenses = get_monthly_expenses(user_id, today.year, today.month)
            return make_plan(args["income"], expenses)

        if name == "search":
            return {"result": search(args["query"])}

        return {"error": f"unknown tool: {name}"}

    except Exception as e:
        print(f"[TOOL] failed: {e}")
        return {"error": str(e)}


def agent_turn(messages, memory, user_id):
    history = [{"role": "system", "content": build_system_prompt(memory)}] + messages

    for _ in range(MAX_ITER):
        msg = call_llm_with_tools(history, TOOL_DEFS)
        if not msg:
            return "Something went wrong — please try again."

        if not getattr(msg, "tool_calls", None):
            return msg.content or ""

        history.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": msg.tool_calls,
        })

        for call in msg.tool_calls:
            try:
                args = json.loads(call.function.arguments)
            except json.JSONDecodeError:
                args = {}

            result = execute_tool(call.function.name, args, memory, user_id)
            history.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result),
            })

    return "Reached tool limit — please try again."


def sync_memory(memory, messages):
    transcript = build_transcript(messages)
    if not transcript.strip():
        return memory

    prompt = [
        {
            "role": "system",
            "content": """Extract memory from this finance conversation.
Return ONLY valid JSON, no markdown backticks.
Format:
{
  "summary": "2-3 lines on key decisions",
  "goals": [{"description": "...", "status": "active"}],
  "commitments": [{"title": "...", "due_date": "YYYY-MM-DD"}],
  "observed_patterns": [{"category": "...", "observation": "..."}]
}
Do not include balances or transaction amounts in summary."""
        },
        {"role": "user", "content": transcript}
    ]

    try:
        result = call_llm_simple(prompt)
        result = re.sub(r"```[\w]*\n?|```", "", result).strip()
        data = json.loads(result)
        memory.summary           = data.get("summary",           memory.summary)
        memory.goals             = data.get("goals",             memory.goals)
        memory.commitments       = data.get("commitments",       memory.commitments)
        memory.observed_patterns = data.get("observed_patterns", memory.observed_patterns)
        print(f"\n[MEMORY] Synced")
    except Exception as e:
        print(f"[MEMORY] sync failed: {e}")

    return memory


def run_session(user_id):
    print(f"\n{'='*40}\nARTHA — Session\n{'='*40}\n")
    memory = load_memory(user_id)
    messages = []

    while True:
        user = input("\nYou: ").strip()
        if user.lower() in ("exit", "quit"):
            break
        if not user:
            continue

        messages.append({"role": "user", "content": user})

        intent = classify(user)
        print(f"[INTENT] {intent}")

        if intent == "finance":
            reply = agent_turn(messages, memory, user_id)
        else:
            reply = call_llm_simple([
                {"role": "system", "content": build_system_prompt(memory)},
                {"role": "user", "content": user}
            ])

        print(f"\nArtha: {reply}")
        messages.append({"role": "assistant", "content": reply})

    memory = sync_memory(memory, messages)
    save_memory(user_id, memory)
    print("\n[MEMORY] Saved.")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import sys
    user_id = sys.argv[1] if len(sys.argv) > 1 else "default"
    run_session(user_id)