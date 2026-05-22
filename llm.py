# LLM Connector Script

import os
import time
from groq import Groq
from dotenv import load_dotenv
from config import client

load_dotenv()

MODEL = "llama-3.3-70b-versatile"




def call_llm_with_tools(messages, tool_defs):
    """
    LLM call with tool calling enabled.
    Used by: agent loop
    Returns: message object (has .content and .tool_calls)
    Returns None on failure.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tool_defs,
            tool_choice="auto",
        )
        return response.choices[0].message

    except (ConnectionError, TimeoutError) as e:
        print(f"[LLM] transient error: {e}, retrying in 1s...")
        time.sleep(1)
        try:
            retry_messages = messages + [{
                "role": "system",
                "content": "Previous request failed. Retry safely and continue."
            }]
            response = client.chat.completions.create(
                model=MODEL,
                messages=retry_messages,
                tools=tool_defs,
                tool_choice="auto",
            )
            return response.choices[0].message
        except Exception as e:
            print(f"[LLM] retry also failed: {e}")
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
    assert result != "", "call_llm_simple returned empty, check API key"
    print("llm.py working correctly.")