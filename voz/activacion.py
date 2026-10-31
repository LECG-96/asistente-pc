import re
import threading
import unicodedata

import keyboard
import numpy as np
import sounddevice as sd

from voz.escuchar import _modelo   # reutiliza el Whisper ya cargado

SR = 16000
BLOQUE = 4000            # 0.25 s de audio por bloque
UMBRAL = 0.015           # volumen mínimo para considerar que hablas
SILENCIO_BLOQUES = 2     # 0.5 s de pausa = fin de la frase
MAX_BLOQUES = 16         # máximo 4 s por frase
ATAJO = "ctrl+alt+j"
DEPURAR = True           # muestra lo que oye; ponlo en False cuando todo funcione

# frase que activa -> variantes con las que Whisper puede escribirla
CLAVES = {
    "jarvis": ["jarvis", "yarvis", "jarbis", "yarbis", "charvis"],
    "vamos a trabajar": ["vamos a trabajar", "vamo a trabajar", "vamos trabajar"],
}

_atajo = threading.Event()
keyboard.add_hotkey(ATAJO, _atajo.set)


def _normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z ]", " ", texto)


def _detectar(audio):
    segmentos, _ = _modelo.transcribe(
        audio,
        language="es",
        beam_size=1,
        vad_filter=True,
        initial_prompt="Jarvis. Vamos a trabajar.",
    )
    texto = _normalizar(" ".join(s.text for s in segmentos))
    if DEPURAR and texto.strip():
        print("[oído]", texto.strip())
    for clave, variantes in CLAVES.items():
        if any(v in texto for v in variantes):
            return clave
    return None


def esperar_activacion():
    """Bloquea hasta oír una frase clave o presionar el atajo.
    Devuelve 'atajo', 'jarvis' o 'vamos a trabajar'."""
    _atajo.clear()
    frase, silencios = [], 0
    with sd.InputStream(samplerate=SR, channels=1, dtype="float32", blocksize=BLOQUE) as flujo:
        while True:
            if _atajo.is_set():
                return "atajo"

            bloque, _ = flujo.read(BLOQUE)
            bloque = bloque.flatten()
            volumen = float(np.sqrt(np.mean(bloque ** 2)))

            if volumen > UMBRAL:
                frase.append(bloque)
                silencios = 0
            elif frase:
                frase.append(bloque)
                silencios += 1

            if frase and (silencios >= SILENCIO_BLOQUES or len(frase) >= MAX_BLOQUES):
                audio = np.concatenate(frase)
                frase, silencios = [], 0
                clave = _detectar(audio)
                if clave:
                    return clave