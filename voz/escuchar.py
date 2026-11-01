import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SR = 16000
_modelo = WhisperModel("small", device="cpu", compute_type="int8")

VOCABULARIO = "Jarvis. Abre, cierra, cerrar, busca, presiona, aprende, olvida, volumen, pestaña."


def normalizar_audio(audio, objetivo=0.7, ganancia_max=20):
    """Sube el volumen hasta que el pico llegue al objetivo (sin amplificar el silencio)."""
    pico = float(np.max(np.abs(audio))) if len(audio) else 0.0
    if pico < 0.005:
        return audio
    return np.clip(audio * min(objetivo / pico, ganancia_max), -1.0, 1.0)


def escuchar(segundos=5):
    print("Escuchando...")
    audio = sd.rec(int(segundos * SR), samplerate=SR, channels=1, dtype="float32")
    sd.wait()
    audio = normalizar_audio(audio.flatten())
    segmentos, _ = _modelo.transcribe(
        audio,
        language="es",
        beam_size=5,
        vad_filter=True,
        initial_prompt=VOCABULARIO,
    )
    return " ".join(s.text.strip() for s in segmentos).strip()