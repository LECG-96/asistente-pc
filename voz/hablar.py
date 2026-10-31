import asyncio
import json
import os
import tempfile
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

# Efecto suave: toque de "sala" sobre una voz que ya es natural
JARVIS = Pedalboard([
    HighpassFilter(cutoff_frequency_hz=80),
    Compressor(threshold_db=-18, ratio=2.5),
    Reverb(room_size=0.1, damping=0.6, wet_level=0.08, dry_level=0.95),
    LowpassFilter(cutoff_frequency_hz=9000),
])


async def _generar(texto, ruta, voz, rate, pitch):
    await edge_tts.Communicate(texto, voz, rate=rate, pitch=pitch).save(ruta)


def hablar(texto, efectos=True, voz=VOZ, rate=RATE, pitch=PITCH):
    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "voz.mp3")
        asyncio.run(_generar(texto, ruta, voz, rate, pitch))
        audio, sr = sf.read(ruta, dtype="float32")

    if efectos:
        audio = JARVIS(audio, sr)

    sd.play(audio, sr)
    sd.wait()