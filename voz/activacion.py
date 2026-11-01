import re
import threading
import unicodedata

import keyboard
import numpy as np
import sounddevice as sd

from acciones.rutinas import RUTINAS
from config import CFG
from voz.escuchar import _modelo, normalizar_audio

SR = 16000
BLOQUE = 4000            # 0.25 s de audio por bloque
UMBRAL = CFG.get("umbral_voz", 0.015)
SILENCIO_BLOQUES = 2     # 0.5 s de pausa = fin de la frase
MAX_BLOQUES = 24         # hasta 6 s por frase (cabe "Jarvis, abre ...")
ATAJO = "ctrl+alt+j"
DEPURAR = True           # muestra lo que oye; ponlo en False cuando todo funcione

# Frases de las rutinas que se activan sin decir "Jarvis" (marcadas "sin_jarvis" en config.json)
_frases_clave = [r["frases"][0].capitalize() + "." for r in RUTINAS.values() if r.get("sin_jarvis")]
VOCABULARIO = "Jarvis. " + " ".join(_frases_clave) + " Abre, cierra, busca."

# frase que activa -> variantes con las que Whisper puede escribirla
CLAVES = {"jarvis": ["jarvis", "yarvis", "jarbis", "yarbis", "charvis"]}
for _nombre, _r in RUTINAS.items():
    if _r.get("sin_jarvis"):
        CLAVES[f"rutina:{_nombre}"] = _r["frases"]

_atajo = threading.Event()
keyboard.add_hotkey(ATAJO, _atajo.set)


def _normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", " ", texto)


def _detectar(audio):
    """Devuelve (frase clave, resto de lo que dijiste después), o (None, "")."""
    audio = normalizar_audio(audio)
    segmentos, _ = _modelo.transcribe(
        audio,
        language="es",
        beam_size=3,
        vad_filter=True,
        initial_prompt=VOCABULARIO,
    )
    texto = _normalizar(" ".join(s.text for s in segmentos))
    if DEPURAR and texto.strip():
        print("[oído]", texto.strip())

    for clave, variantes in CLAVES.items():
        for variante in variantes:
            pos = texto.find(variante)
            if pos != -1:
                resto = re.sub(r"\s+", " ", texto[pos + len(variante):]).strip()
                return clave, resto
    return None, ""


def esperar_activacion(pausa=lambda: False):
    """Bloquea hasta oír una frase clave o presionar el atajo.
    Devuelve (origen, orden): origen es 'atajo', 'jarvis' o 'rutina:<nombre>';
    orden es lo que dijiste después de 'Jarvis' (o None si no dijiste nada más).
    Devuelve None si se pausó."""
    _atajo.clear()
    frase, silencios = [], 0
    with sd.InputStream(samplerate=SR, channels=1, dtype="float32", blocksize=BLOQUE) as flujo:
        while True:
            if pausa():
                return None
            if _atajo.is_set():
                return "atajo", None

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
                clave, resto = _detectar(audio)
                if clave:
                    return clave, (resto if len(resto) >= 3 else None)