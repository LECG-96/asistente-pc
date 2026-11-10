import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
CFG = json.loads((BASE / "config.json").read_text(encoding="utf-8"))
DEPURAR_VOZ = CFG.get("depurar_voz", False)
