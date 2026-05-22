import os
from config import client

MODEL = "whisper-large-v3"
MAX_FILE_SIZE_MB = 25


def transcribe(audio_path: str) -> str | None:
    """
    Transcribe processed WAV audio using Groq Whisper.

    Args:
        audio_path: processed temp WAV path from audio.py

    Returns:
        str  -> transcribed text
        None -> transcription failed

    NOTE: Temp file is always cleaned up in finally block.
    """
    # file existence check
    if not os.path.exists(audio_path):
        print(f"[STT] file not found: {audio_path}")
        return None

    # file size check — Groq limit 25MB
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        print(f"[STT] file too large ({file_size_mb:.2f}MB), limit is 25MB")
        try:
            os.remove(audio_path)
        except Exception:
            pass
        return None

    try:
        with open(audio_path, "rb") as audio:
            response = client.audio.transcriptions.create(
                file=audio,
                model=MODEL,
            )

        # safe response check
        if response and hasattr(response, "text") and response.text:
            return response.text.strip()

        print("[STT] empty response from Groq")
        return None

    except Exception as e:
        print(f"[STT] transcription failed: {e}")
        return None

    finally:
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception as e:
            print(f"[STT] cleanup failed: {e}")


# ── quick test ──────────────────────────────────────────
if __name__ == "__main__":
    import sys
    from utils.audio import process_audio

    if len(sys.argv) < 2:
        print("Usage: python stt.py <path_to_wav>")
        sys.exit(1)

    processed = process_audio(sys.argv[1])
    if processed:
        text = transcribe(processed)
        print(f"Transcription: {text}")
    else:
        print("Audio processing failed.")