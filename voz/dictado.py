import re
import unicodedata
import winsound

import keyboard
import numpy as np
import sounddevice as sd

TIEMPO_SIN_VOZ = 15      # segundos en silencio antes de cerrar el dictado solo
SILENCIO_BLOQUES = 3     # 0.75 s de pausa separa una frase de otra
MAX_BLOQUES = 60         # hasta 15 s por frase

FIN = re.compile(r"\b(?:fin del dictado|terminar? (?:el )?dictado|dejar? de dictar|detener (?:el )?dictado)\b")


def _norm(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", texto)).strip()


def dictar(m=None):
    """Escribe en la ventana activa lo que digas, hasta oír 'fin del dictado'."""
    # Se importa aquí para no cargar Whisper al probar el cerebro por escrito
    from voz.activacion import BLOQUE, SR, UMBRAL
    from voz.escuchar import _modelo, normalizar_audio

    winsound.Beep(900, 150)
    frase, silencios, inactivo = [], 0, 0.0
    with sd.InputStream(samplerate=SR, channels=1, dtype="float32", blocksize=BLOQUE) as flujo:
        while True:
            bloque, _ = flujo.read(BLOQUE)
            bloque = bloque.flatten()
            volumen = float(np.sqrt(np.mean(bloque ** 2)))

            if volumen > UMBRAL:
                frase.append(bloque)
                silencios = 0
            elif frase:
                frase.append(bloque)
                silencios += 1
            else:
                inactivo += BLOQUE / SR
                if inactivo >= TIEMPO_SIN_VOZ:
                    break

            if frase and (silencios >= SILENCIO_BLOQUES or len(frase) >= MAX_BLOQUES):
                audio = np.concatenate(frase)
                frase, silencios, inactivo = [], 0, 0.0
                segmentos, _ = _modelo.transcribe(
                    normalizar_audio(audio), language="es", beam_size=5, vad_filter=True
                )
                texto = " ".join(s.text.strip() for s in segmentos).strip()
                if not texto:
                    continue
                print("[dictado]", texto)

                norm = _norm(texto)
                if FIN.search(norm):
                    break
                if norm in ("nueva linea", "salto de linea"):
                    keyboard.send("enter")
                elif norm == "punto y aparte":
                    keyboard.write(".")
                    keyboard.send("enter")
                else:
                    keyboard.write(texto + " ")

    winsound.Beep(600, 150)
    winsound.Beep(600, 150)
    return "Dictado terminado."