import asyncio
import hashlib
import json
import threading
import time
from pathlib import Path

import edge_tts
import sounddevice as sd
import soundfile as sf
from pedalboard import (Compressor, HighpassFilter, LowpassFilter,
                        Pedalboard, Reverb)

BASE = Path(__file__).resolve().parent.parent
_CFG = json.loads((BASE / "config.json").read_text(encoding="utf-8"))

VOZ = _CFG["voz"]
RATE = _CFG["rate"]
PITCH = _CFG["pitch"]

CACHE = BASE / "datos" / "cache_voz"
CACHE.mkdir(parents=True, exist_ok=True)
MAX_CACHE = 600          # máximo de frases guardadas; las más antiguas se borran

_REPRODUCCION = threading.Lock()

JARVIS = Pedalboard([
    HighpassFilter(cutoff_frequency_hz=80),
    Compressor(threshold_db=-18, ratio=2.5),
    Reverb(room_size=0.1, damping=0.6, wet_level=0.08, dry_level=0.95),
    LowpassFilter(cutoff_frequency_hz=9000),
])


async def _sintetizar(texto, ruta, voz, rate, pitch):
    await edge_tts.Communicate(texto, voz, rate=rate, pitch=pitch).save(ruta)


def _ruta_cache(texto, voz, rate, pitch):
    clave = hashlib.md5(f"{voz}|{rate}|{pitch}|{texto}".encode("utf-8")).hexdigest()
    return CACHE / f"{clave}.mp3"


def _limpiar():
    archivos = sorted(CACHE.glob("*.mp3"), key=lambda p: p.stat().st_mtime)
    for p in archivos[:-MAX_CACHE]:
        p.unlink(missing_ok=True)


def _generar(texto, voz, rate, pitch):
    """Devuelve el audio de la frase; solo usa internet si aún no está guardada."""
    ruta = _ruta_cache(texto, voz, rate, pitch)
    if not ruta.exists():
        tmp = ruta.with_name(f"{ruta.stem}.{threading.get_ident()}.tmp")
        asyncio.run(_sintetizar(texto, str(tmp), voz, rate, pitch))
        tmp.replace(ruta)
        _limpiar()
    return ruta


def precalentar(frases):
    """Genera en segundo plano las frases que aún no están guardadas."""
    for frase in frases:
        if _ruta_cache(frase, VOZ, RATE, PITCH).exists():
            continue
        try:
            _generar(frase, VOZ, RATE, PITCH)
        except Exception:
            return                  # sin internet: se reintenta en el próximo arranque
        time.sleep(0.3)


def hablar(texto, efectos=True, voz=VOZ, rate=RATE, pitch=PITCH):
    ruta = _generar(texto, voz, rate, pitch)
    audio, sr = sf.read(str(ruta), dtype="float32")

    if efectos:
        audio = JARVIS(audio, sr)

    with _REPRODUCCION:
        sd.play(audio, sr)
        sd.wait()