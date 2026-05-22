import os
import tempfile
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

TARGET_SR = 16000


def process_audio(input_path: str) -> str | None:
    """
    Process audio for STT.
    - Load WAV from Gradio
    - Convert stereo to mono
    - Resample to 16kHz
    - Save to temp WAV
    - Return output path

    Returns:
        str  -> processed file path
        None -> processing failed

    NOTE: Caller is responsible for cleanup.
    After transcription in stt.py:
        if path: os.remove(path)
    """
    try:
        audio, sr = sf.read(input_path)

        # stereo → mono
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        # resample to 16kHz if needed
        if sr != TARGET_SR:
            audio = resample_poly(audio, TARGET_SR, sr).astype("float32")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            output_path = tmp.name

        sf.write(output_path, audio, TARGET_SR)
        return output_path

    except Exception as e:
        print(f"[Audio] processing failed: {e}")
        return None


# ── quick test ──────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python audio.py <path_to_wav>")
        sys.exit(1)

    result = process_audio(sys.argv[1])
    if result:
        print(f"Output: {result}")
        print(f"Size: {os.path.getsize(result)} bytes")
        os.remove(result)
        print("Temp file cleaned up.")
    else:
        print("Processing failed.")