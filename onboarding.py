# onboarding.py
def run_onboarding(memory):
    """
    Collect initial user profile.
    Runs only once — skips if profile already exists.
    Collects:
    - name
    - monthly_income (stored as string — LLM handles "80k" etc)
    - primary_goal
    Returns:
        updated memory
    """
    if memory.user_profile:
        return memory

    print("\nWelcome to Artha.\n")

    name = input("What should I call you? ").strip()
    if not name:
        name = "User"

    monthly_income = input(
        "What is your monthly income? (e.g. 80000 or 80k) "
    ).strip()

    primary_goal = input(
        "What is your primary financial goal right now? "
    ).strip()
    if not primary_goal:
        primary_goal = "Not specified"

    memory.user_profile.update({
        "name": name,
        "monthly_income": monthly_income,
        "primary_goal": primary_goal,
    })

    print(f"\nGot it, {name}. Let's get started.\n")
    return memory


# ── quick test ──────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from memory import Memory

    # test 1 — new user
    mem = Memory()
    mem = run_onboarding(mem)
    print(f"Profile: {mem.user_profile}")

    # test 2 — existing user, should skip
    mem2 = Memory()
    mem2.user_profile = {"name": "Ranjan", "monthly_income": "80000"}
    mem2 = run_onboarding(mem2)
    print(f"Skipped: {mem2.user_profile}")