import sounddevice as sd
from faster_whisper import WhisperModel

SR = 16000
_modelo = WhisperModel("small", device="cpu", compute_type="int8")


def escuchar(segundos=5):
    print("Escuchando...")
    audio = sd.rec(int(segundos * SR), samplerate=SR, channels=1, dtype="float32")
    sd.wait()
    segmentos, _ = _modelo.transcribe(
        audio.flatten(), language="es", beam_size=5, vad_filter=True
    )
    return " ".join(s.text.strip() for s in segmentos).strip()