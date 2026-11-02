import json
import re
import subprocess
import time
import traceback
import urllib.error
import urllib.request
import winsound

from config import CFG

IA = CFG.get("ia", {})
URL = IA.get("url", "http://localhost:11434/api/chat")
MODELO = IA.get("modelo", "llama3.2:3b")
GPU = IA.get("gpu", "auto")                       # true, false o "auto"
VRAM_MINIMA_MB = IA.get("vram_minima_mb", 3000)   # en "auto": memoria libre para usar la GPU
MANTENER = IA.get("mantener_cargado", "2m")       # cuánto tiempo queda el modelo en memoria
MAX_TOKENS = IA.get("max_tokens", 160)
RESPONDER_TODO = IA.get("responder_todo", False)

SISTEMA = (
    "Eres Jarvis, un asistente de voz en español que vive en el computador del usuario. "
    "Responde siempre en español, en una a tres frases cortas, con lenguaje natural y claro. "
    "No uses listas, markdown, emojis ni símbolos, porque tu respuesta se lee en voz alta. "
    "Si no sabes algo, dilo con honestidad en vez de inventar."
)

MAX_MENSAJES = 6        # mensajes recordados (3 preguntas y 3 respuestas)
OLVIDAR_TRAS = 300      # segundos sin hablar: la conversación se reinicia

_historial = []
_ultimo_uso = 0.0
_decision_gpu = None    # (usó_gpu, momento)


class RespuestaIA(str):
    """Respuesta de la IA: no cuenta en las estadísticas de uso."""


def _segundos(texto):
    m = re.fullmatch(r"\s*(\d+)\s*([smh]?)\s*", str(texto))
    if not m:
        return 120
    return int(m.group(1)) * {"": 1, "s": 1, "m": 60, "h": 3600}[m.group(2)]


def _vram_libre_mb():
    try:
        salida = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        ).stdout
        return int(salida.strip().splitlines()[0])
    except Exception:
        return None


def _usar_gpu():
    """En 'auto' usa la GPU solo si sobra memoria (por ejemplo, con un juego abierto no)."""
    global _decision_gpu
    if GPU is True or GPU is False:
        return GPU
    ahora = time.time()
    if _decision_gpu and ahora - _decision_gpu[1] < _segundos(MANTENER):
        return _decision_gpu[0]          # el modelo sigue cargado: no lo cambiamos de lugar
    libre = _vram_libre_mb()
    usar = libre is None or libre >= VRAM_MINIMA_MB
    _decision_gpu = (usar, ahora)
    return usar


def _consultar(mensajes, usar_gpu):
    opciones = {"num_predict": MAX_TOKENS, "temperature": 0.6, "num_ctx": 2048}
    if not usar_gpu:
        opciones["num_gpu"] = 0          # fuerza el procesador
    cuerpo = json.dumps({
        "model": MODELO,
        "messages": [{"role": "system", "content": SISTEMA}, *mensajes],
        "stream": False,
        "keep_alive": MANTENER,
        "options": opciones,
    }).encode("utf-8")
    req = urllib.request.Request(URL, data=cuerpo, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)["message"]["content"]


def _limpiar(texto):
    texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.S)    # por si el modelo "piensa"
    texto = re.sub(r"[*_`#>~|]", "", texto)
    texto = re.sub(r"^\s*(?:[-•]|\d+[.)])\s+", "", texto, flags=re.M)
    texto = re.sub(r"\s*\n+\s*", " ", texto).strip()
    if len(texto) > 700:
        texto = texto[:700]
    if texto and texto[-1] not in ".!?":
        corte = max(texto.rfind("."), texto.rfind("!"), texto.rfind("?"))
        if corte > len(texto) // 2:
            texto = texto[:corte + 1]        # no leer una frase cortada a la mitad
    return texto


def responder(pregunta):
    global _historial, _ultimo_uso, _decision_gpu
    if time.time() - _ultimo_uso > OLVIDAR_TRAS:
        _historial = []

    winsound.Beep(700, 120)                  # "estoy pensando"
    usar_gpu = _usar_gpu()
    mensajes = [*_historial, {"role": "user", "content": pregunta}][-MAX_MENSAJES:]
    try:
        texto = _limpiar(_consultar(mensajes, usar_gpu))
    except urllib.error.URLError:
        return RespuestaIA("No pude conectarme a Ollama. Revisa que esté abierto.")
    except Exception:
        traceback.print_exc()
        return RespuestaIA("La inteligencia artificial local no respondió.")

    if not texto:
        return RespuestaIA("No supe qué responder.")
    _historial = [*mensajes, {"role": "assistant", "content": texto}][-MAX_MENSAJES:]
    _ultimo_uso = time.time()
    if _decision_gpu:
        _decision_gpu = (_decision_gpu[0], _ultimo_uso)
    return RespuestaIA(texto)


def preguntar(m):
    pregunta = re.sub(r"^(?:pregunta|preguntale)\s+", "", m.string).strip()
    return responder(pregunta)


def reiniciar(m=None):
    global _historial
    _historial = []
    return "Conversación reiniciada."