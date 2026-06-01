import asyncio
import json
import base64
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from agent import agent_turn, sync_memory, build_system_prompt
from memory import load_memory, save_memory
from intent import classify
from llm import call_llm_simple
from stt import transcribe
from tts import speak

app = FastAPI()
_pool = ThreadPoolExecutor(max_workers=4)


async def _run(fn, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_pool, fn, *args)


@app.websocket("/ws/{user_id}")
async def ws_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()

    memory = load_memory(user_id)
    history = []  # full conversation history — fixes mid-session memory loss

    # ── welcome message ───────────────────────────────────────
    name = memory.user_profile.get("name", "")
    if memory.user_profile:
        welcome_text = f"Welcome back{', ' + name if name else ''}. Kya chal raha hai?"
    else:
        welcome_text = (
            "Namaste! Main Artha hun — aapka personal finance agent. "
            "Apna naam aur monthly income batao to start karte hain."
        )

    audio_path = await _run(speak, welcome_text)
    if audio_path and os.path.exists(audio_path):
        with open(audio_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        os.remove(audio_path)
        await websocket.send_json({
            "type": "audio",
            "data": b64,
            "text": welcome_text,
        })

    # ── main loop ─────────────────────────────────────────────
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            # ── audio turn ────────────────────────────────────
            if msg["type"] == "audio":
                audio_bytes = base64.b64decode(msg["data"])

                # infer extension from mime so Groq identifies format correctly
                # Groq supports: webm, ogg, mp4, wav, mp3
                mime = msg.get("mime", "audio/webm")
                ext = mime.split("/")[-1].split(";")[0]  # "webm" | "ogg" | "mp4"

                with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
                    tmp.write(audio_bytes)
                    tmp_path = tmp.name

                # STT — transcribe() cleans up the file itself
                await websocket.send_json({"type": "status", "state": "thinking"})
                text = await _run(transcribe, tmp_path)

                if not text or not text.strip():
                    await websocket.send_json({"type": "status", "state": "listening"})
                    continue

                await websocket.send_json({"type": "transcript", "text": text})

                # intent + agent
                intent = await _run(classify, text)
                history.append({"role": "user", "content": text})

                if intent == "finance":
                    reply = await _run(agent_turn, history, memory, user_id)
                else:
                    system_msgs = [
                        {"role": "system", "content": build_system_prompt(memory)},
                        {"role": "user", "content": text},
                    ]
                    reply = await _run(call_llm_simple, system_msgs)

                if not reply:
                    reply = "Kuch problem aa gayi — dobara bolna."

                history.append({"role": "assistant", "content": reply})

                # TTS
                audio_path = await _run(speak, reply)
                if audio_path and os.path.exists(audio_path):
                    with open(audio_path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    os.remove(audio_path)
                    await websocket.send_json({
                        "type": "audio",
                        "data": b64,
                        "text": reply,
                    })
                else:
                    # TTS failed — send text so UI can at least display it
                    await websocket.send_json({"type": "text_only", "text": reply})
                    await websocket.send_json({"type": "status", "state": "listening"})

            # ── end session ───────────────────────────────────
            elif msg["type"] == "end_session":
                await websocket.send_json({"type": "status", "state": "saving"})
                if history:
                    updated = await _run(sync_memory, memory, history)
                    await _run(save_memory, user_id, updated)
                await websocket.send_json({"type": "session_ended"})
                break

    except WebSocketDisconnect:
        # save memory on unexpected disconnect
        if history:
            try:
                updated = sync_memory(memory, history)
                save_memory(user_id, updated)
            except Exception as e:
                print(f"[WS] disconnect save failed: {e}")

    except Exception as e:
        print(f"[WS] error: {e}")
        try:
            await websocket.send_json({"type": "error", "text": "Something went wrong."})
        except Exception:
            pass


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return HTMLResponse(Path("static/index.html").read_text())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)