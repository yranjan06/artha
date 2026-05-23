# Artha

Your voice-first finance bro that actually remembers stuff.

Chat in Hindi or English. Artha gets what you mean, hits up the right finance tools, and keeps your goals and promises in mind for next time.

Built from the ground up. The challenge? No LangChain, no LlamaIndex, no safety nets. Just raw code.

---

## Demo

(demo vid coming soon, promise)

---

## Architecture

(arch diagram also coming soon, lol)

---

## Key Design Decisions

**No frameworks, just vibes.** The agent loop, memory, intent classifier, and tool dispatch? All coded from scratch. Frameworks like LangChain are cool, but they hide the magic. Building it raw means we know exactly what's going on, making it easier to fix and understand.

**Let Python do the math, let the LLM do the thinking.** Calculating your budget, summing up transactions, all that number crunching is pure Python. The LLM only steps in for the big brain questions: "Should I really buy this?", "Does this mess with my goals?", "What's the key takeaway from our chat?".

**Memory for the constants, tools for the variables.** Your goals, promises, and habits? They're saved in `memory/{user_id}.json`. Your bank balance and transaction history? Never stored. We fetch that fresh every time. Nobody wants a finance agent giving them stale numbers. That's a trust-killer.

**Grows with you.** No filling out boring forms. First time you chat, Artha just asks for your name and income. After that, it remembers you. Adding more users is as simple as changing a single line of code.

---

## The Voice Tech

```
Groq Whisper  -> for speech-to-text (STT)
Groq Llama 3.3 -> for the brains and tool use
Sarvam Bulbul v3 -> for text-to-speech (TTS) with a natural Indian voice
```

One Groq API key handles both STT and the LLM. Sarvam gives the output that smooth Indian accent.

---

## Get it Running

```bash
git clone https://github.com/yourusername/artha.git
cd artha

# Set up a virtual environment
python -m venv venv
source venv/bin/activate

# Install the goods
pip install -r requirements.txt

# Make your own .env file
# You'll need to add your GROQ_API_KEY and SARVAM_API_KEY
```

---

## How to Use

```bash
python app.py
# Then open up http://localhost:7860 in your browser
```

Hit **Call** to start talking. Artha will talk back.
When you're done, click **End Call** to save your session.

---

## What's Inside

```
artha/
├── app.py              # The Gradio UI, where the voice magic starts
├── agent.py            # The main agent loop, tool handling, and system prompts
├── intent.py           # A 2-layer system to figure out if you're talking finance or just chatting
├── memory.py           # Handles loading and saving your profile so it's persistent
├── ledger.py           # A log of all your transactions, just for you
├── onboarding.py       # The part that gets your info the first time
├── stt.py              # Groq Whisper for turning your speech into text
├── tts.py              # Sarvam Bulbul v3 for turning text into speech
├── llm.py              # A wrapper for the Groq SDK with some retry smarts
├── config.py           # Shared Groq client setup
├── tools/
│   ├── finance.py      # Tools for logging expenses, checking your budget, setting reminders, etc.
│   └── search.py       # DuckDuckGo for looking up financial info
├── utils/
│   └── audio.py        # Tools for handling audio, like resampling and converting to mono
├── memory/             # This folder gets created automatically for user data (and is gitignored)
├── .env.example
└── requirements.txt
```

---

## A Tale of Two Sessions

**Session 1:**
- You tell Artha your name and how much you make. It saves this to your profile.
- You log some expenses. They go into your personal ledger.
- You ask about your budget. Artha calculates it using Python, not the LLM.
- You end the session. Artha figures out your goals and patterns and saves them.

**Session 2 (another day):**
- Artha loads up your profile. It already knows your name, income, and goals.
- You ask if you should buy something. Artha checks your budget against your current spending.
- It even remembers the promises you made in Session 1 without you having to repeat yourself.

---

## The Inspo

This project is a mashup of two of my earlier builds:
- **Finno**: A finance agent with memory, built with Groq and a raw agent loop.
- **Voice Assistant**: A voice-powered assistant with a 3-layer intent system and a Groq Whisper pipeline.

Artha takes the best of both and turns them into a real product with voice I/O, a user model, and a transaction ledger.

---

## What's Next

- Move to FastAPI + WebSockets for a real-time, continuous conversation.
- Add chunked summarization for super long chats.
- Build a proper multi-user authentication system.
- Integrate with bank APIs like Setu or Plaid.


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