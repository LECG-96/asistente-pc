from collections import deque

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from config import CFG

SR = 16000
BLOQUE = 1600                                  # 0.1 s de audio por bloque
UMBRAL = CFG.get("umbral_voz", 0.015)

_modelo = WhisperModel("small", device="cpu", compute_type="int8")

VOCABULARIO = "Jarvis. Abre, cierra, cerrar, busca, presiona, aprende, olvida, volumen, pestaña."


def normalizar_audio(audio, objetivo=0.7, ganancia_max=20):
    """Sube el volumen hasta que el pico llegue al objetivo (sin amplificar el silencio)."""
    pico = float(np.max(np.abs(audio))) if len(audio) else 0.0
    if pico < 0.005:
        return audio
    return np.clip(audio * min(objetivo / pico, ganancia_max), -1.0, 1.0)


def grabar(espera=8, maximo=20, silencio=1.2):
    """Graba hasta que dejes de hablar.
    espera:  segundos que aguarda a que empieces a hablar.
    maximo:  duración máxima de lo que dices.
    silencio: pausa (en segundos) que da por terminada la frase."""
    previo = deque(maxlen=3)                   # 0.3 s antes de hablar, para no cortar el inicio
    grabado, hablando, quieto, bloques = [], False, 0, 0
    with sd.InputStream(samplerate=SR, channels=1, dtype="float32", blocksize=BLOQUE) as flujo:
        while True:
            bloque, _ = flujo.read(BLOQUE)
            bloque = bloque.flatten()
            bloques += 1
            volumen = float(np.sqrt(np.mean(bloque ** 2)))

            if volumen > UMBRAL:
                if not hablando:
                    hablando = True
                    grabado.extend(previo)
                grabado.append(bloque)
                quieto = 0
            elif hablando:
                grabado.append(bloque)
                quieto += 1
                if quieto * BLOQUE / SR >= silencio:
                    break
            else:
                previo.append(bloque)
                if bloques * BLOQUE / SR >= espera:
                    break                      # nadie habló

            if hablando and len(grabado) * BLOQUE / SR >= maximo:
                break
    return np.concatenate(grabado) if grabado else None


def escuchar(espera=8, maximo=20, silencio=1.2):
    print("Escuchando...")
    audio = grabar(espera, maximo, silencio)
    if audio is None:
        return ""
    segmentos, _ = _modelo.transcribe(
        normalizar_audio(audio),
        language="es",
        beam_size=5,
        vad_filter=True,
        initial_prompt=VOCABULARIO,
    )
    return " ".join(s.text.strip() for s in segmentos).strip()