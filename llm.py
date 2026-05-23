import os
import time
from groq import Groq

MODEL = "llama-3.3-70b-versatile"

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("GROQ_API_KEY not found — add it to .env")

client = Groq(api_key=api_key)


def call_llm_with_tools(messages, tool_defs):
    """
    LLM call with tool calling enabled.
    Retries on tool_use_failed with a correction hint.
    Returns: message object or None on failure.
    """
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tool_defs,
                tool_choice="auto",
            )
            return response.choices[0].message

        except Exception as e:
            err = str(e)
            is_tool_error = "tool_use_failed" in err or "Failed to call a function" in err
            if attempt == 0 and is_tool_error:
                print(f"[LLM] tool_use_failed — retrying with hint...")
                messages = messages + [{
                    "role": "user",
                    "content": (
                        "Your previous response had a malformed tool call. "
                        "Use the proper tool call format — do NOT write "
                        "<function=...> tags in plain text. Retry now."
                    )
                }]
                time.sleep(0.5)
                continue
            elif attempt == 0:
                print(f"[LLM] transient error: {e}, retrying...")
                time.sleep(1)
                messages = messages + [{"role": "user", "content": "Previous request failed. Retry safely."}]
                continue
            else:
                print(f"[LLM] failed after retry: {e}")
                return None
    return None


def call_llm_simple(messages):
    """
    Plain LLM call — no tools, returns text only.
    Used by: memory sync, general chat
    Returns: str (empty string on failure)
    """
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        print(f"[LLM] simple call failed: {e}")
        return ""


# ── quick test ──────────────────────────────────────────
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print("Testing call_llm_simple...")
    result = call_llm_simple([
        {"role": "user", "content": "Say hello in one word"}
    ])
    print(f"Response: {result}")
    assert result != "", "call_llm_simple returned empty — check API key"
    print("llm.py working correctly.")