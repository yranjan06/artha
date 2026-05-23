# Artha

A voice first personal finance agent with persistent memory across sessions.

Speak in Hindi or English — Artha understands your intent, calls the right financial tools, and remembers your goals and commitments the next time you talk.

Built from scratch. Constrain for this task : no LangChain, no LlamaIndex, no agent frameworks used.

---

## Demo

will update ..

---

## Architecture

will update ..

---

## Key Design Decisions

**No frameworks.** The agent loop, memory layer, intent classifier, and tool dispatch are all written from scratch. Abstractions like LangChain hide what actually happens on each tool call cycle — building raw makes debugging tractable and the architecture transparent.

**Math in code, judgment in LLM.** Transaction filtering, category summing, budget calculations — all happen in Python. The LLM is called only for decisions that require reasoning: should I buy this, does this conflict with my goal, what should I remember from this conversation.

**Memory stores what doesn't change. Tools fetch what does.** Goals, commitments, and behavioral patterns persist in `memory/{user_id}.json`. Account balances and transaction lists are never stored — they are fetched fresh every session. Quoting a stale balance in a finance agent is a trust-breaking failure.

**Progressive user profiling.** No hardcoded user data. First session, Artha asks your name and income. Subsequent sessions load from memory. Scaling to multiple users requires changing one line — the memory file path.

---

## Voice Pipeline

```
Groq Whisper  → STT (speech to text)
Groq Llama 3.3 → LLM reasoning + tool calling
Sarvam Bulbul v3 → TTS (text to speech, Indian voice)
```

Single Groq API key for STT and LLM. Sarvam for natural Indian accent output.

---

## Setup

```bash
git clone https://github.com/yourusername/artha.git
cd artha

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

use env (create ur own)
# Add GROQ_API_KEY and SARVAM_API_KEY
```

---

## Running

```bash
python app.py
# Open http://localhost:7860
```

Click **Call** to start a session. Speak. Artha responds with voice.
Click **End Call** to save memory and end the session.

---

## Project Structure

```
artha/
├── app.py              # Gradio UI — voice pipeline entry point
├── agent.py            # Agent loop, tool dispatch, system prompts
├── intent.py           # 2-tier intent classifier (finance vs general)
├── memory.py           # Persistent JSON memory — load, save, sync
├── ledger.py           # Per-user transaction log
├── onboarding.py       # First-session user profile collection
├── stt.py              # Groq Whisper STT
├── tts.py              # Sarvam Bulbul v3 TTS
├── llm.py              # Groq SDK wrapper with retry logic
├── config.py           # Shared Groq client
├── tools/
│   ├── finance.py      # log_expense, get_monthly_summary, check_budget,
│   │                   # set_reminder, make_plan, parse_income
│   └── search.py       # DuckDuckGo financial search
├── utils/
│   └── audio.py        # Audio processing — resample, mono convert
├── memory/             # Auto-created — per-user JSON files (gitignored)
├── .env.example
└── requirements.txt
```

---

## What One Session Demonstrates

**Session 1:**
- User tells Artha their name and income — stored in profile
- User logs expenses — written to ledger
- User asks about budget — calculated from ledger in code, not LLM
- Session ends — goals, commitments, patterns extracted and saved

**Session 2 (different day):**
- Artha loads memory — knows the user's name, income, goals
- User asks a purchase decision — Artha checks budget against current ledger
- Artha references commitments from Session 1 without being told

---

## Inspiration

Built on top of two earlier projects:
- **Finno** — finance agent with persistent memory (Groq, raw agent loop)
- **Voice Assistant** — 3-tier intent classifier, Groq Whisper pipeline

Artha merges both into a single end-to-end product with voice I/O, a real user model, and a transaction ledger.

---

## Future

- FastAPI + WebSocket for true continuous conversation
- Chunked summarization for long sessions
- Multi-user auth layer
- Bank API integration (Setu, Plaid)