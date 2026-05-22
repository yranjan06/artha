import os
import base64
import tempfile
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.sarvam.ai/text-to-speech"

api_key = os.getenv("SARVAM_API_KEY")
if not api_key:
    raise RuntimeError("SARVAM_API_KEY not found — add it to .env")


def speak(text: str) -> str | None:
    """
    Generate speech using Sarvam Bulbul v3.

    Args:
        text: LLM response text

    Returns:
        str  -> temp WAV file path
        None -> generation failed

    NOTE: Caller (app.py) is responsible for cleanup after playback.
    """
    if not text or not text.strip():
        print("[TTS] empty text, skipping")
        return None

    try:
        response = requests.post(
            API_URL,
            headers={
                "api-subscription-key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "target_language_code": "hi-IN",
                "model": "bulbul:v3",
                "speaker": "priya",
                "speech_sample_rate": 16000,
            },
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        audios = data.get("audios")

        if not audios or not audios[0]:
            print("[TTS] empty audio in response")
            return None

        audio_bytes = base64.b64decode(audios[0])

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            return tmp.name

    except Exception as e:
        print(f"[TTS] generation failed: {e}")
        return None


# ── quick test ──────────────────────────────────────────
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    path = speak("Namaste! Main Artha hun, aapka personal finance agent.")
    if path:
        print(f"Audio saved: {path}")
        print(f"Size: {os.path.getsize(path)} bytes")
    else:
        print("TTS failed.")